# Godot Knowledge Base

> A living knowledge base that combines Godot engine documentation, best practices, and per-project context — powering AI chat, project queries, and script generation from the Aura dashboard.

## Status

`idea` → next up for implementation

## Why

For Aura to be a useful AI orchestrator, it needs to know Godot inside-out — not just the API surface, but how to use it well. It also needs to understand each project's specific structure, conventions, and custom classes. Without this, AI suggestions will be generic and often wrong.

The knowledge base is the foundation for three first-day capabilities:
1. **Ask about Godot API** — "What signals does CharacterBody3D have?"
2. **Ask about your project** — "What scripts use the player node?"
3. **Generate new scripts** — "Write a double jump script" using knowledge of the engine AND your project's existing patterns, structure, and conventions

## Architecture

### Two-layer knowledge

| Layer | Scope | Shared? |
|-------|-------|---------|
| **Engine knowledge** | Godot API reference + best practices | Shared across all projects |
| **Project knowledge** | File tree, scripts, scenes, conventions | Isolated per project |

### Engine Knowledge (shared)
- **Full API reference**: every class, method, signal, enum, property in the current Godot version
- **Best practices & patterns**: GDScript idioms, node composition, scene organization, performance patterns, common pitfalls
- **Version-aware**: auto-ingests on backend start, matches the connected Godot version

### Project Knowledge (per-project, isolated)
- **File tree + script contents**: full GDScript source code indexed and queryable
- **Metadata**: class names, exported properties, signals, autoloads, project settings
- **Understanding of each file**: what it does, how it's used, its relationships to other files
- **Naming conventions & style**: picks up how you name nodes, variables, files
- **Game-type bootstrapping**: can start from a template (2D platformer, 3D FPS, etc.) then refine as the project diverges

## Storage: SurrealDB (Embedded)

### Deployment
- **Embedded mode** (in-process, file-backed) — zero ops, runs inside the Python backend
- All features (vectors, graphs, FTS, hybrid search) work identically in embedded mode
- Portable to server mode later with zero code changes when scaling is needed

### Data Models (all three from day 1)
- **Document model** — store engine docs, script contents, project metadata as JSON-native records
- **Graph model** — RELATE edges for script→script dependencies, scene→node relationships, class inheritance
- **Vector embeddings** — HNSW index for semantic search ("how do I..." natural language queries)

### Indexing & Search (all three from day 1)
- **Full-text search** — keyword lookup with configurable tokenizers for exact API queries ("CharacterBody3D")
- **Vector similarity search** — HNSW nearest-neighbor for semantic queries ("how do I make a player jump")
- **Hybrid search** — reciprocal rank fusion combining FTS + vector in a single query

### File Storage (Buckets) — v1
- Store raw project files (GDScript sources) alongside their indexed metadata and graph relationships
- Serves as a queryable mirror of the Godot project — Godot always owns the originals
- Backend/dashboard can access file contents without asking Godot
- **Storage size**: GDScript files are tiny (typical project: 5-10MB of text) — vector embeddings will dominate DB size, not raw files
- **Sync**: file watcher in AuraBridge detects changes (file-level hash), sends updates, backend overwrites bucket copy + re-indexes
- **Staleness**: if Godot is closed, bucket represents last known state — re-syncs on next AuraBridge connect
- Later: viewport screenshots, AI-generated scripts, asset thumbnails, binary assets (evaluate size at that point)

### TODO: SurrealDB features to evaluate later
- [ ] Live queries — subscribe to KB changes for dashboard auto-updates
- [ ] Table events — auto-re-embed docs when updated
- [ ] MCP server — connect Claude/Cursor directly to the KB
- [ ] SurrealML — in-DB model inference for auto-embedding on insert
- [ ] LangChain integration — pre-built vector store adapter for RAG
- [ ] Versioned temporal tables — track how project knowledge evolves over time
- [ ] Custom functions (JS/WASM) — complex processing inside queries
- [ ] Security (RBAC, permissions) — needed when moving to multi-user/server mode

## Docs Ingestion

### Source: Godot `--doctool` XML export
- Run `godot --doctool` to export structured XML of the full class reference from the installed version
- Parse into structured records (class → methods, signals, properties, enums, descriptions)
- Store in SurrealDB with graph relationships (class inheritance, signal connections)

### Trigger: auto on backend start
- Backend detects Godot version from connected engine (or config)
- Checks if docs for that version are already ingested
- If not (or version changed), runs ingestion pipeline automatically

### TODO: evaluate additional sources later
- [ ] Scrape docs.godotengine.org (includes tutorials + guides beyond API)
- [ ] Parse godot-docs GitHub repo RST files (structured, version-tagged)
- [ ] Community resources (GDQuest, etc.)

## Project Scanning

### Trigger: connect + file watcher
- **On AuraBridge connect**: full project scan — sends file tree, script contents, metadata
- **While running**: AuraBridge watches for file changes and sends diffs incrementally

### Incremental re-indexing
- **File-level hashing**: hash each file, only re-index when hash changes
- **TODO**: refine to function/class-level granularity later for less re-indexing

### What AuraBridge sends (v1)
- File tree (paths + types)
- Full GDScript source contents
- Script metadata (class names, exports, signals)

### TODO: expand scanning scope later
- [ ] Scene files (.tscn) — node tree structure, attached scripts, resource references
- [ ] Resource files — materials, textures, audio references
- [ ] project.godot — full project settings, input mappings, autoloads
- [ ] Everything parseable in the project

## Script Generation

The knowledge base enables context-aware script generation:
- AI understands the full Godot API (what's available, correct signatures)
- AI sees the project's existing scripts (naming patterns, signal conventions, code style)
- AI knows the scene structure (what nodes exist, what scripts are attached where)
- Generated scripts follow the project's established patterns, not generic boilerplate

## Chat Interface

### Location: Aura web dashboard (first)
- Chat panel in the React app alongside the telemetry view
- Answers both engine and project questions
- Can generate new scripts using full knowledge base context

### Engine-agnostic design
- Chat interface and backend APIs should be engine-agnostic
- Same features should work across Godot, Unity, Unreal when those engines are supported
- Abstract the "engine knowledge" and "project knowledge" concepts so they're not Godot-specific

## AI Layer

**Pluggable architecture** — abstract the AI provider so it can be swapped:
- Initial implementation likely **Codex CLI Agent** running in the background
- Architecture should support Claude API, local models (Ollama), or other providers later

> ⚠️ **DISCUSS BEFORE IMPLEMENTING** — align on the AI agent approach before writing code for this layer.

## Embedding Model

### Decision: `qwen3-embedding:0.6b` via Ollama
- **Size**: 639MB — fast on CPU-only servers, no GPU required
- **Context**: 32K tokens — embed entire scripts or full class docs in one shot
- **Dimensions**: flexible 32–4096 (start with 384 or 768, increase later)
- **Code-aware**: explicitly trained for code retrieval, not just text
- **MTEB family**: 0.6b is the lightweight version of the #1 ranked model
- **Cost**: free, runs locally
- **API**: Ollama REST API at `localhost:11434/api/embed` — same interface local and deployed

### Architecture
```
Aura Backend → Ollama API (localhost:11434) → qwen3-embedding:0.6b → vector → SurrealDB
```

### Swappable
- Backend calls an embedding service abstraction, not Ollama directly
- Can swap to OpenAI, Voyage, or any other provider by changing the client
- SurrealDB doesn't care where vectors come from

## Open Questions / Concerns

- **Chunking strategy**: how to chunk docs for effective retrieval — by class? by method? by topic? (32K context helps — most files can go whole)
- **Privacy**: project code stays in the backend — acceptable for all users, or need local-only mode?
- **Size**: full Godot 4.x class reference is large — how to keep retrieval fast and relevant?
- **Multi-version**: if a team pins Godot 4.4 but 4.6 is out, the KB should match their pinned version
- **Embedding dimensions**: start with 384 (fast) or 768 (balanced)? Benchmark both.

## Progress

- [ ] Install SurrealDB Python SDK and set up embedded instance
- [ ] Install Ollama and pull `qwen3-embedding:0.6b`
- [ ] Build embedding service abstraction (pluggable provider)
- [ ] Design knowledge base schema (engine docs + project context + graph relationships)
- [ ] Implement Godot `--doctool` XML parsing
- [ ] Store engine docs in SurrealDB (documents + graph edges + FTS index + vectors)
- [ ] Set up file storage buckets for project files
- [ ] Implement project scanning in AuraBridge (file tree + scripts + metadata)
- [ ] Implement file-level hashing for incremental re-indexing
- [ ] Implement file watcher in AuraBridge for live updates
- [ ] Store project data in SurrealDB (documents + graph + vectors + buckets)
- [ ] Build retrieval/query API (hybrid search: FTS + vector + graph)
- [ ] Build chat interface in dashboard
- [ ] Implement script generation using KB context
- [ ] Auto-ingest engine docs on backend start
- [ ] Game-type templates / bootstrapping
