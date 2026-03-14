# Aura — Todo Tracker

<!--
  Usage:
  - Add ideas to the Ideas section as they come
  - Move items to In Progress when you start working on them
  - Check off and move to Done when complete
  - Reorder freely within sections to reflect priority (top = highest)
  - Tags: [backend] [frontend] [godot] [infra] [design]
  - Link to detail files: [→ details](docs/todo/feature-name.md)
  - Detail files live in docs/todo/ — use the template below
-->

## Ideas

- [ ] Godot knowledge base — API docs + best practices + per-project context, managed in backend [backend] — [→ details](docs/todo/godot-knowledge-base.md)
- [ ] AI chat panel in dashboard — engine queries, project queries, script generation [frontend] [backend]
- [ ] Engine-agnostic interfaces — abstract chat, KB, and scanning so they work across all engines [backend]
- [ ] In-editor chat panel for Godot — same features as dashboard chat, inside the Godot editor [godot]
- [ ] In-editor chat panel for Unity [unity]
- [ ] In-editor chat panel for Unreal [unreal]
- [ ] SurrealDB: evaluate live queries + table events for real-time KB updates [backend]
- [ ] SurrealDB: evaluate MCP server — connect Claude/Cursor directly to KB [infra]
- [ ] SurrealDB: evaluate SurrealML — in-DB embedding generation on insert [backend]
- [ ] SurrealDB: evaluate LangChain integration for RAG pipelines [backend]
- [ ] SurrealDB: evaluate temporal tables — track KB evolution over time [backend]
- [ ] SurrealDB: evaluate custom functions (JS/WASM) [backend]
- [ ] SurrealDB: add security (RBAC, permissions) when moving to server mode [backend] [infra]
- [ ] Evaluate additional doc sources — online docs scraping, godot-docs RST repo, community resources [backend]
- [ ] Expand project scanning — .tscn scenes, resources, project.godot, everything parseable [godot] [backend]
- [ ] Fine-grained re-indexing — function/class-level change detection instead of file-level [backend]
- [ ] Session recording and playback
- [ ] Scene tree inspection via WebSocket
- [ ] Multi-engine support (Unity, Unreal plugin stubs)
- [ ] Node property editor controlled from dashboard
- [ ] Authentication for multi-user sessions
- [ ] Plugin marketplace / registry
- [ ] Screenshot/viewport capture from Godot → send to Aura for AI analysis — [→ details](docs/todo/viewport-capture.md)
- [ ] Gameplay diagnostics recorder — toggleable 1-min recording with timeline annotations, AI-powered bug analysis [godot] [backend] [frontend] — [→ details](docs/todo/gameplay-diagnostics.md)
- [ ] Dark/light theme toggle in dashboard
- [ ] Evaluate PydanticAI for agent layer — easier switching between LLM providers/models [backend]

## Up Next

- [ ] "Auto accept mode" — toggle to auto-approve all agent tool calls / file changes without prompting [frontend] [backend]

## In Progress


## Done

- [x] Monorepo setup (pnpm + Turborepo + uv) [infra]
- [x] FastAPI backend with WebSocket server [backend]
- [x] React dashboard with live FPS telemetry [frontend]
- [x] Godot AuraBridge autoload script [godot]
- [x] Real engine → backend → dashboard pipeline (no mocks) [backend] [godot]
- [x] Engine disconnect clears dashboard state [backend] [frontend]
