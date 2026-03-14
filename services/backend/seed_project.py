"""Seed the KB with the godot-test project."""

import asyncio
import json
from pathlib import Path
import websockets

PROJECT_PATH = Path(__file__).resolve().parent.parent.parent / "engines" / "godot-test"
PROJECT_NAME = "godot-test"


def read_files():
    """Read all project files (skip .uid, .import, etc.)."""
    files = []
    extensions = {".gd", ".tscn", ".tres", ".godot", ".cfg", ".gdshader"}
    for p in sorted(PROJECT_PATH.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix not in extensions:
            continue
        if ".godot/" in str(p):  # skip Godot cache dir
            continue
        rel = str(p.relative_to(PROJECT_PATH))
        try:
            content = p.read_text()
        except Exception:
            continue
        lang = "gdscript" if p.suffix == ".gd" else p.suffix.lstrip(".")
        files.append({"path": rel, "content": content, "language": lang})
    return files


async def seed():
    files = read_files()
    print(f"Found {len(files)} files in {PROJECT_PATH}")
    for f in files:
        print(f"  {f['path']} ({f['language']}, {len(f['content'])} bytes)")

    async with websockets.connect("ws://localhost:8000/ws") as ws:
        ack = json.loads(await ws.recv())
        print(f"\nConnected: {ack['payload']['clientId']}")

        await ws.send(json.dumps({
            "type": "project.scan",
            "timestamp": "2026-03-14T00:00:00Z",
            "payload": {
                "project_name": PROJECT_NAME,
                "engine": "godot",
                "engine_version": "4.6",
                "project_path": str(PROJECT_PATH),
                "files": files,
            },
        }))

        resp = json.loads(await ws.recv())
        print(f"Scan result: {resp['payload']}")


asyncio.run(seed())
