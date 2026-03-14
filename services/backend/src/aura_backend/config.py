from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Aura"
    version: str = "0.1.0"
    debug: bool = False

    # SurrealDB (embedded)
    surreal_path: str = "file://data/aura.db"
    surreal_namespace: str = "aura"
    surreal_database: str = "aura"

    # Ollama embeddings
    ollama_base_url: str = "http://localhost:11434"
    ollama_embed_model: str = "qwen3-embedding:0.6b"
    ollama_embed_dimensions: int = 1024

    # Knowledge base
    kb_auto_ingest: bool = True
    kb_godot_version: str = "4.4"
    kb_docs_cache_dir: str = "data/godot-docs"

    # Agent
    agent_provider: str = "codex"
    agent_codex_binary: str = "codex"
    agent_codex_model: str = "gpt-5.4"
    agent_context_budget: int = 8000

    model_config = {"env_prefix": "AURA_"}


settings = Settings()
