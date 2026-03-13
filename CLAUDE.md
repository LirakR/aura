# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Aura — a universal, visual-context-aware AI orchestrator for game engines (Godot, Unity, Unreal).

## Architecture

Monorepo managed with pnpm workspaces + Turborepo (JS) and uv (Python).

- `apps/web/` — React 19 + Vite + TypeScript frontend (Shadcn UI, Tailwind v4)
- `packages/types/` — shared TypeScript types (placeholder)
- `services/backend/` — FastAPI backend with WebSocket support

## Development

### Backend

```bash
cd services/backend
uv sync                                         # install deps
uv run uvicorn aura_backend.main:app --reload   # start on :8000
```

### Frontend

```bash
pnpm install          # from repo root
pnpm dev:web          # start Vite dev server on :5173 (proxies /api + /ws to :8000)
```

### Full stack

Run backend and frontend in separate terminals. The Vite dev server proxies `/api` and `/ws` to `localhost:8000`.

## Key conventions

- **Python deps**: use `uv add <name>` — never pin versions manually
- **Shadcn UI**: preset `nova` (radix base), icon library `lucide-react`. Change preset with `pnpm dlx shadcn@latest init --preset <name> --force`
- **Styling**: Tailwind v4 CSS-first config, semantic colors only (`bg-primary`, `text-muted-foreground`), custom Aura tokens (`text-aura-cyan`, `text-aura-green`, etc.)
- **WebSocket contract**: typed envelope `{ type, timestamp, payload }` — see `services/backend/src/aura_backend/websocket/schemas.py`
