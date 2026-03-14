"""JSON-RPC helpers for Codex CLI app-server communication."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class JsonRpcRequest:
    method: str
    params: dict = field(default_factory=dict)
    id: int | str | None = None

    def to_json(self) -> str:
        obj: dict[str, Any] = {"jsonrpc": "2.0", "method": self.method}
        if self.params:
            obj["params"] = self.params
        if self.id is not None:
            obj["id"] = self.id
        return json.dumps(obj)


@dataclass
class JsonRpcResponse:
    id: int | str | None
    result: Any = None
    error: dict | None = None

    @property
    def is_error(self) -> bool:
        return self.error is not None


def make_request(method: str, params: dict | None = None, req_id: int | str | None = None) -> JsonRpcRequest:
    return JsonRpcRequest(method=method, params=params or {}, id=req_id)


def parse_message(line: str) -> dict:
    """Parse a JSON-RPC message from a line of text."""
    return json.loads(line)


def is_response(msg: dict) -> bool:
    """Check if msg is a JSON-RPC response (has id + result/error, no method)."""
    return "id" in msg and ("result" in msg or "error" in msg) and "method" not in msg


def is_notification(msg: dict) -> bool:
    """Check if msg is a JSON-RPC notification (has method, no id)."""
    return "method" in msg and "id" not in msg


def is_server_request(msg: dict) -> bool:
    """Check if msg is a JSON-RPC request from the server (has both id and method)."""
    return "method" in msg and "id" in msg
