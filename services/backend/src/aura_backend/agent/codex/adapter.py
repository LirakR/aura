"""Codex CLI app-server adapter — subprocess management + JSON-RPC.

Protocol flow:
  1. Spawn `codex app-server` (communicates via JSON-RPC over stdio)
  2. Client sends `initialize` request
  3. Client sends `initialized` notification
  4. Client sends `thread/start` request  →  gets threadId back
  5. Client sends `turn/start` request    →  gets turnId back
  6. Server streams notifications:
       - item/agentMessage/delta   (text deltas)
       - turn/completed            (turn done)
  7. Server may send requests for approval:
       - item/commandExecution/requestApproval
       - item/fileChange/requestApproval
     Client responds with {decision: "accept"} or {decision: "decline"}
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator

from aura_backend.agent.base import ProviderEvent, SessionInfo, TurnInfo
from aura_backend.agent.codex.protocol import (
    JsonRpcResponse,
    is_notification,
    is_response,
    is_server_request,
    make_request,
    parse_message,
)
from aura_backend.config import settings

logger = logging.getLogger(__name__)


class CodexAdapter:
    """Manages a single Codex app-server subprocess for one thread."""

    def __init__(self, thread_id: str, cwd: str, model: str) -> None:
        self.thread_id = thread_id
        self.cwd = cwd
        self.model = model
        self._proc: asyncio.subprocess.Process | None = None
        self._events: asyncio.Queue[ProviderEvent] = asyncio.Queue()
        self._pending_responses: dict[int | str, asyncio.Future[JsonRpcResponse]] = {}
        self._pending_approvals: dict[str, asyncio.Future[str]] = {}
        self._reader_task: asyncio.Task | None = None
        self._next_id = 1
        self._codex_thread_id: str | None = None
        self._codex_turn_id: str | None = None
        # Item tracking — only the last agentMessage is persisted
        self._msg_text = ""  # current agentMessage accumulator
        self._last_msg_text = ""  # last completed agentMessage text
        self._msg_item_id: str | None = None  # current agentMessage item id

    async def start(self) -> SessionInfo:
        binary = settings.agent_codex_binary
        cmd = [
            binary,
            "app-server",
            "-c", f'model="{self.model}"',
        ]
        logger.info("Starting Codex: %s (cwd=%s)", " ".join(cmd), self.cwd)

        self._proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Start reading stdout
        self._reader_task = asyncio.create_task(self._read_loop())
        # Start draining stderr so it doesn't block
        asyncio.create_task(self._drain_stderr())

        # 1. Send initialize
        init_resp = await self._request("initialize", {
            "clientInfo": {
                "name": "aura",
                "version": settings.version,
            },
            "capabilities": {
                "experimentalApi": False,
            },
        })
        logger.info("Codex initialized: %s", init_resp.result)

        # 2. Send initialized notification
        await self._notify("initialized")

        # 3. Start a thread
        thread_resp = await self._request("thread/start", {
            "cwd": self.cwd,
            "model": self.model,
            "approvalPolicy": "on-request",
        })
        result = thread_resp.result or {}
        # thread/start returns {thread: {id: ..., ...}}
        thread_obj = result.get("thread", result)
        self._codex_thread_id = thread_obj.get("id") or result.get("threadId") or self.thread_id
        logger.info("Codex thread started: %s", self._codex_thread_id)

        return SessionInfo(
            thread_id=self.thread_id,
            provider="codex",
            model=self.model,
        )

    async def send_turn(self, message: str, context: str | None = None) -> TurnInfo:
        self._msg_text = ""
        self._last_msg_text = ""
        self._msg_item_id = None

        text = message
        if context:
            text = f"{context}\n\n---\n\n{message}"

        turn_resp = await self._request("turn/start", {
            "threadId": self._codex_thread_id,
            "input": [{"type": "text", "text": text}],
        })
        result = turn_resp.result or {}
        # turn/start returns {turn: {id: ..., ...}}
        turn_obj = result.get("turn", result)
        self._codex_turn_id = turn_obj.get("id") or result.get("turnId")

        # Emit turn started
        await self._events.put(ProviderEvent(
            kind="turn.started",
            thread_id=self.thread_id,
        ))

        return TurnInfo(
            thread_id=self.thread_id,
            request_id=self._codex_turn_id or "",
        )

    async def interrupt(self) -> None:
        if self._codex_thread_id and self._codex_turn_id:
            try:
                await self._request("turn/interrupt", {
                    "threadId": self._codex_thread_id,
                    "turnId": self._codex_turn_id,
                })
            except Exception:
                logger.debug("Interrupt request failed", exc_info=True)

    async def respond_to_approval(self, request_id: str, decision: str) -> None:
        fut = self._pending_approvals.pop(request_id, None)
        if fut and not fut.done():
            fut.set_result(decision)

    async def stop(self) -> None:
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        if self._proc and self._proc.returncode is None:
            self._proc.terminate()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._proc.kill()

        logger.info("Codex adapter stopped for thread %s", self.thread_id)

    async def stream_events(self) -> AsyncIterator[ProviderEvent]:
        while True:
            event = await self._events.get()
            yield event
            if event.kind in ("turn.completed", "error"):
                break

    # ── Internal helpers ────────────────────────────────────────────

    async def _request(self, method: str, params: dict) -> JsonRpcResponse:
        """Send a JSON-RPC request and wait for the response."""
        req_id = self._next_id
        self._next_id += 1

        fut: asyncio.Future[JsonRpcResponse] = asyncio.get_event_loop().create_future()
        self._pending_responses[req_id] = fut

        req = make_request(method, params, req_id=req_id)
        await self._write(req.to_json())

        try:
            return await asyncio.wait_for(fut, timeout=30.0)
        except asyncio.TimeoutError:
            self._pending_responses.pop(req_id, None)
            raise

    async def _notify(self, method: str, params: dict | None = None) -> None:
        """Send a JSON-RPC notification (no id, no response expected)."""
        msg = {"jsonrpc": "2.0", "method": method}
        if params:
            msg["params"] = params
        await self._write(json.dumps(msg))

    async def _write(self, data: str) -> None:
        if self._proc and self._proc.stdin:
            line = data + "\n"
            self._proc.stdin.write(line.encode())
            await self._proc.stdin.drain()

    async def _drain_stderr(self) -> None:
        """Read and log stderr so the pipe doesn't fill up."""
        try:
            assert self._proc and self._proc.stderr
            while True:
                line = await self._proc.stderr.readline()
                if not line:
                    break
                text = line.decode().strip()
                if text:
                    logger.debug("Codex stderr: %s", text[:500])
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def _read_loop(self) -> None:
        """Read lines from Codex stdout and dispatch."""
        try:
            assert self._proc and self._proc.stdout
            while True:
                line = await self._proc.stdout.readline()
                if not line:
                    # Process exited
                    await self._events.put(ProviderEvent(
                        kind="error",
                        thread_id=self.thread_id,
                        error="Codex process exited unexpectedly",
                    ))
                    break
                text = line.decode().strip()
                if not text:
                    continue

                try:
                    msg = parse_message(text)
                except json.JSONDecodeError:
                    logger.debug("Non-JSON from Codex: %s", text[:200])
                    continue

                await self._dispatch(msg)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.error("Codex reader loop error", exc_info=True)
            await self._events.put(ProviderEvent(
                kind="error",
                thread_id=self.thread_id,
                error="Reader loop crashed",
            ))

    async def _dispatch(self, msg: dict) -> None:
        """Route a parsed JSON-RPC message."""

        if is_response(msg):
            rid = msg.get("id")
            fut = self._pending_responses.pop(rid, None)
            if fut and not fut.done():
                if "error" in msg:
                    fut.set_result(JsonRpcResponse(id=rid, error=msg["error"]))
                else:
                    fut.set_result(JsonRpcResponse(id=rid, result=msg.get("result")))
            return

        if is_notification(msg):
            method = msg.get("method", "")
            params = msg.get("params", {})

            # ── Item lifecycle ──────────────────────────────────────
            if method == "item/started":
                item = params.get("item", {})
                itype = item.get("type", "")
                iid = item.get("id", "")

                if itype == "agentMessage":
                    # New agent message — reset text accumulator
                    self._msg_text = ""
                    self._msg_item_id = iid
                    await self._events.put(ProviderEvent(
                        kind="item.started",
                        thread_id=self.thread_id,
                        item_id=iid,
                        item_type="message",
                    ))
                elif itype == "commandExecution":
                    await self._events.put(ProviderEvent(
                        kind="item.started",
                        thread_id=self.thread_id,
                        item_id=iid,
                        item_type="command",
                    ))
                elif itype == "fileChange":
                    await self._events.put(ProviderEvent(
                        kind="item.started",
                        thread_id=self.thread_id,
                        item_id=iid,
                        item_type="file_change",
                    ))
                # reasoning items — skip (internal)

            elif method == "item/agentMessage/delta":
                delta = params.get("delta", "")
                iid = params.get("itemId", "")
                # Only stream if this is the current message item
                if iid == self._msg_item_id:
                    self._msg_text += delta
                    await self._events.put(ProviderEvent(
                        kind="message.delta",
                        thread_id=self.thread_id,
                        item_id=iid,
                        text_delta=delta,
                    ))

            elif method == "item/completed":
                item = params.get("item", {})
                itype = item.get("type", "")
                iid = item.get("id", "")

                if itype == "agentMessage":
                    # Extract final text from content array
                    content = item.get("content", [])
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "output_text":
                            text = part.get("text", "")
                            if text:
                                self._msg_text = text
                    self._last_msg_text = self._msg_text
                    await self._events.put(ProviderEvent(
                        kind="item.completed",
                        thread_id=self.thread_id,
                        item_id=iid,
                        item_type="message",
                        full_text=self._msg_text,
                    ))
                elif itype == "commandExecution":
                    await self._events.put(ProviderEvent(
                        kind="item.completed",
                        thread_id=self.thread_id,
                        item_id=iid,
                        item_type="command",
                        item_data=self._extract_command_data(item),
                    ))
                elif itype == "fileChange":
                    await self._events.put(ProviderEvent(
                        kind="item.completed",
                        thread_id=self.thread_id,
                        item_id=iid,
                        item_type="file_change",
                        item_data=self._extract_file_data(item),
                    ))

            # ── Command/file output deltas ──────────────────────────
            elif method == "item/commandExecution/outputDelta":
                iid = params.get("itemId", "")
                delta = params.get("delta", "")
                await self._events.put(ProviderEvent(
                    kind="item.output",
                    thread_id=self.thread_id,
                    item_id=iid,
                    item_type="command",
                    text_delta=delta,
                ))

            elif method == "item/fileChange/outputDelta":
                iid = params.get("itemId", "")
                delta = params.get("delta", "")
                await self._events.put(ProviderEvent(
                    kind="item.output",
                    thread_id=self.thread_id,
                    item_id=iid,
                    item_type="file_change",
                    text_delta=delta,
                ))

            # ── Turn lifecycle ──────────────────────────────────────
            elif method == "turn/started":
                turn = params.get("turn", {})
                self._codex_turn_id = turn.get("id") or self._codex_turn_id

            elif method == "turn/completed":
                await self._events.put(ProviderEvent(
                    kind="turn.completed",
                    thread_id=self.thread_id,
                    full_text=self._last_msg_text,
                ))

            return

        if is_server_request(msg):
            method = msg.get("method", "")
            rid = msg["id"]
            params = msg.get("params", {})

            if method in (
                "item/commandExecution/requestApproval",
                "item/fileChange/requestApproval",
            ):
                await self._handle_approval_request(rid, method, params)

            elif method == "execCommandApproval":
                # Legacy approval format
                await self._handle_legacy_approval(rid, params)

            elif method == "applyPatchApproval":
                # Legacy patch approval
                await self._handle_legacy_patch_approval(rid, params)

            else:
                # Unknown server request — respond with error
                logger.warning("Unknown server request: %s", method)
                resp = json.dumps({
                    "jsonrpc": "2.0",
                    "id": rid,
                    "error": {"code": -32601, "message": f"Unknown method: {method}"},
                })
                await self._write(resp)

            return

    @staticmethod
    def _extract_command_data(item: dict) -> dict:
        """Extract useful info from a completed commandExecution item."""
        return {
            "command": item.get("command", ""),
            "cwd": item.get("cwd", ""),
            "exitCode": item.get("exitCode"),
        }

    @staticmethod
    def _extract_file_data(item: dict) -> dict:
        """Extract useful info from a completed fileChange item."""
        changes = item.get("fileChanges", item.get("changes", {}))
        files = list(changes.keys()) if isinstance(changes, dict) else []
        return {"files": files}

    async def _handle_approval_request(
        self, rid: int | str, method: str, params: dict
    ) -> None:
        """Handle new-style approval requests."""
        is_file = method == "item/fileChange/requestApproval"
        item_id = params.get("itemId", str(rid))
        req_id = params.get("approvalId") or item_id

        description = params.get("reason", "")
        if not description:
            if is_file:
                description = "File change approval"
            else:
                cmd = params.get("command", "")
                description = f"Command: {cmd}" if cmd else "Command execution approval"

        tool_args: dict = {}
        if is_file:
            tool_args = {"grantRoot": params.get("grantRoot")}
        else:
            tool_args = {
                "command": params.get("command"),
                "cwd": params.get("cwd"),
            }

        fut: asyncio.Future[str] = asyncio.get_event_loop().create_future()
        self._pending_approvals[req_id] = fut

        await self._events.put(ProviderEvent(
            kind="approval.request",
            thread_id=self.thread_id,
            request_id=req_id,
            approval_data={
                "tool_name": "file_change" if is_file else "command_execution",
                "tool_args": tool_args,
                "description": description,
            },
        ))

        try:
            decision = await asyncio.wait_for(fut, timeout=300.0)
            if decision == "approve":
                codex_decision = "accept"
            else:
                codex_decision = "decline" if is_file else "decline"

            resp = json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"decision": codex_decision},
            })
            await self._write(resp)
        except asyncio.TimeoutError:
            resp = json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"decision": "cancel" if is_file else "decline"},
            })
            await self._write(resp)

    async def _handle_legacy_approval(self, rid: int | str, params: dict) -> None:
        """Handle legacy execCommandApproval requests."""
        req_id = params.get("callId", str(rid))
        command = params.get("command", [])
        cmd_str = " ".join(command) if isinstance(command, list) else str(command)

        fut: asyncio.Future[str] = asyncio.get_event_loop().create_future()
        self._pending_approvals[req_id] = fut

        await self._events.put(ProviderEvent(
            kind="approval.request",
            thread_id=self.thread_id,
            request_id=req_id,
            approval_data={
                "tool_name": "command_execution",
                "tool_args": {"command": cmd_str, "cwd": params.get("cwd")},
                "description": f"Execute: {cmd_str}",
            },
        ))

        try:
            decision = await asyncio.wait_for(fut, timeout=300.0)
            codex_decision = "approved" if decision == "approve" else "denied"
            resp = json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"decision": codex_decision},
            })
            await self._write(resp)
        except asyncio.TimeoutError:
            resp = json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"decision": "denied"},
            })
            await self._write(resp)

    async def _handle_legacy_patch_approval(self, rid: int | str, params: dict) -> None:
        """Handle legacy applyPatchApproval requests."""
        req_id = params.get("callId", str(rid))
        file_changes = params.get("fileChanges", {})
        files = list(file_changes.keys())

        fut: asyncio.Future[str] = asyncio.get_event_loop().create_future()
        self._pending_approvals[req_id] = fut

        await self._events.put(ProviderEvent(
            kind="approval.request",
            thread_id=self.thread_id,
            request_id=req_id,
            approval_data={
                "tool_name": "file_change",
                "tool_args": {"files": files},
                "description": f"Modify files: {', '.join(files[:5])}",
            },
        ))

        try:
            decision = await asyncio.wait_for(fut, timeout=300.0)
            codex_decision = "approved" if decision == "approve" else "denied"
            resp = json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"decision": codex_decision},
            })
            await self._write(resp)
        except asyncio.TimeoutError:
            resp = json.dumps({
                "jsonrpc": "2.0",
                "id": rid,
                "result": {"decision": "denied"},
            })
            await self._write(resp)
