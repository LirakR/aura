# Aura — Architecture & Big Picture

> Universal, visual-context-aware AI orchestrator for game engines (Godot, Unity, Unreal).

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Aura Dashboard                           │
│              (React 19 + Vite + Tailwind v4 + Shadcn)           │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  Telemetry   │  │  Chat Panel  │  │  Script Generator  │    │
│  │  (live FPS)  │  │  (AI queries)│  │  (KB-powered)      │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket + REST
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Aura Backend (FastAPI)                      │
│                                                                 │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐    │
│  │ WS Server │  │ KB Query API │  │ Embedding Service      │    │
│  │ /ws       │  │ /api/kb/*    │  │ (pluggable provider)   │    │
│  └──────────┘  └──────────────┘  └────────────┬───────────┘    │
│       │              │                         │                │
│       │         ┌────▼────────────────┐  ┌─────▼──────────┐    │
│       │         │    SurrealDB        │  │    Ollama       │    │
│       │         │    (embedded)       │  │    (local API)  │    │
│       │         │                     │  │                 │    │
│       │         │  • Documents        │  │  qwen3-embed    │    │
│       │         │  • Graph edges      │  │  :0.6b          │    │
│       │         │  • Vector index     │  │                 │    │
│       │         │  • FTS index        │  │  CPU-only,      │    │
│       │         │  • File buckets     │  │  32K context     │    │
│       │         └─────────────────────┘  └────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Game Engine (Godot 4.6)                       │
│                                                                 │
│  AuraBridge (autoload GDScript)                                 │
│  • Connects to /ws on start                                     │
│  • Sends real-time FPS telemetry every 2s                       │
│  • Full project scan on connect                                 │
│  • File watcher for incremental updates                         │
│  • File-level hashing for change detection                      │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | React 19 + Vite 6 + TypeScript | Shadcn UI (nova preset), Tailwind v4, Geist + Geist Mono fonts |
| Backend | FastAPI (Python 3.12+) | Managed by uv, no version pinning |
| Database | SurrealDB (embedded, file-backed) | Documents + graph + vectors + FTS + buckets |
| Embeddings | qwen3-embedding:0.6b via Ollama | CPU-only, 32K context, code-aware, REST API |
| AI Layer | Pluggable (TBD — likely Codex CLI Agent first) | ⚠️ Discuss before implementing |
| Engine | Godot 4.6 | GDScript autoload, WebSocket client |
| Monorepo | pnpm workspaces + Turborepo (JS), uv (Python) | |
| Build | Vite (frontend), uv (backend) | Vite proxy for /api + /ws to backend |

## Directory Structure

```
aura/
├── apps/web/                    # React dashboard (Vite SPA)
│   └── src/
│       ├── components/ui/       # Shadcn components (Card, Badge, Button)
│       ├── features/dashboard/  # Dashboard + EngineStatusCard
│       ├── hooks/               # useWebSocket
│       └── types/               # WS message types
│
├── packages/types/              # Shared TS types (placeholder)
│
├── services/backend/            # FastAPI backend
│   └── src/aura_backend/
│       ├── api/health.py        # GET /api/health
│       ├── websocket/           # WS server, ConnectionManager, schemas
│       ├── config.py            # pydantic-settings
│       └── main.py              # FastAPI app
│
├── engines/godot-test/          # Test Godot project
│   ├── project.godot
│   └── aura_bridge.gd          # WebSocket autoload
│
├── docs/
│   ├── ARCHITECTURE.md          # This file
│   └── todo/
│       ├── _TEMPLATE.md
│       ├── godot-knowledge-base.md  # Full KB spec (next feature)
│       └── viewport-capture.md
│
└── TODO.md                      # Main tracker
```

## What's Built (v0.1.0)

- [x] Monorepo skeleton (pnpm + Turborepo + uv)
- [x] FastAPI backend with WebSocket server
- [x] React dashboard with dark HUD-style UI
- [x] Live FPS telemetry from Godot → backend → dashboard
- [x] Godot AuraBridge autoload (connects, sends real telemetry)
- [x] Engine disconnect clears dashboard state
- [x] No mocks — only real engine data flows through

## WebSocket Protocol

All messages use typed envelopes: `{ type, timestamp, payload }`

### Server → Client
| type | payload | description |
|------|---------|-------------|
| `connection.ack` | `{ clientId, serverVersion }` | On connect |
| `engine.status` | `{ engine, status, version, fps }` | Forwarded from engine |
| `engine.disconnect` | `{}` | Engine client left |
| `heartbeat.pong` | `{}` | Response to ping |

### Client → Server
| type | description |
|------|-------------|
| `heartbeat.ping` | Keepalive (dashboard sends every 30s) |
| `engine.status` | Real telemetry (Godot sends every 2s) |

### REST
| Method | Path | Response |
|--------|------|----------|
| GET | `/api/health` | `{ status: "ok", version: "0.1.0" }` |

## What's Next: Knowledge Base

Full spec: [docs/todo/godot-knowledge-base.md](todo/godot-knowledge-base.md)

### Summary of Decisions

**Storage**: SurrealDB embedded (file-backed, in-process)
- Documents + Graph + Vectors + FTS + Hybrid Search + File Buckets
- All from day 1, portable to server mode later with zero code changes

**Embeddings**: qwen3-embedding:0.6b via Ollama
- 639MB, CPU-only, 32K context, code-aware
- Pluggable abstraction — swappable to any provider

**Docs ingestion**: Godot `--doctool` XML export
- Auto on backend start, version-aware
- Parsed into structured records with graph relationships

**Project scanning**: AuraBridge connect + file watcher
- Full scan on connect, incremental via file-level hashing
- Sends: file tree + script contents + metadata
- Raw files stored in SurrealDB buckets

**Chat interface**: Aura web dashboard
- Three capabilities from day 1: API queries, project queries, script generation
- Engine-agnostic design (abstract for future Unity/Unreal support)

**AI layer**: Pluggable architecture
- Likely Codex CLI Agent initially
- ⚠️ Must discuss and align before implementing

### Implementation Order (from Progress checklist)
1. Install SurrealDB Python SDK + set up embedded instance
2. Install Ollama + pull qwen3-embedding:0.6b
3. Build embedding service abstraction
4. Design KB schema (engine docs + project context + graph)
5. Implement --doctool XML parsing
6. Store engine docs (documents + graph + FTS + vectors)
7. Set up file storage buckets
8. Implement project scanning in AuraBridge
9. Implement file-level hashing for incremental re-indexing
10. Implement file watcher in AuraBridge
11. Store project data (documents + graph + vectors + buckets)
12. Build retrieval/query API (hybrid search)
13. Build chat interface in dashboard
14. Implement script generation using KB context
15. Auto-ingest engine docs on backend start

## Dev Commands

### Backend
```bash
cd services/backend
uv sync                                         # install deps
uv run uvicorn aura_backend.main:app --reload   # start on :8000
```

### Frontend
```bash
pnpm install          # from repo root
pnpm dev:web          # Vite dev server on :5173 (proxies to :8000)
```

### Godot
Open `engines/godot-test/` in Godot → Play (F5)

## Conventions

- **Python deps**: `uv add <name>` — never pin versions
- **Shadcn UI**: nova preset (radix base), lucide-react icons. Change with `pnpm dlx shadcn@latest init --preset <name> --force`
- **Styling**: Tailwind v4, semantic colors only, custom Aura tokens (`text-aura-cyan`, `text-aura-green`, etc.)
- **WebSocket**: typed envelope `{ type, timestamp, payload }`
- **Research**: start from `/llms.txt` or AI-friendly docs, not marketing pages
