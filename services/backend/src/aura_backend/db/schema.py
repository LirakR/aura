"""SurrealDB schema for the Aura knowledge base.

Applies all table, field, and index definitions idempotently using a
schema-version check stored in ``kb_meta``.
"""

from __future__ import annotations

import logging

from aura_backend.config import settings

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 4

# Tables in dependency order (relations last).
ALL_TABLES = [
    # Edge / relation tables
    "inherits",
    "has_method",
    "has_property",
    "has_signal",
    "has_constant",
    "depends_on",
    "attached_to",
    "extends_class",
    # Data tables
    "kb_class",
    "kb_method",
    "kb_property",
    "kb_signal",
    "kb_constant",
    "kb_constructor",
    "kb_operator",
    "kb_theme_item",
    "kb_project",
    "kb_project_file",
    # Chat tables
    "chat_thread",
    "chat_message",
]

_DIM = settings.ollama_embed_dimensions

# Each element is executed as a separate query.
SCHEMA_STATEMENTS: list[str] = [
    # ── Analyzer ─────────────────────────────────────────────────────
    "DEFINE ANALYZER kb_analyzer TOKENIZERS blank,class FILTERS lowercase,snowball(english)",
    # ── Engine knowledge tables ──────────────────────────────────────
    # kb_class
    "DEFINE TABLE kb_class SCHEMAFULL",
    "DEFINE FIELD engine          ON kb_class TYPE string",
    "DEFINE FIELD engine_version  ON kb_class TYPE string",
    "DEFINE FIELD name            ON kb_class TYPE string",
    "DEFINE FIELD inherits_from   ON kb_class TYPE option<string>",
    "DEFINE FIELD category        ON kb_class TYPE option<string>",
    "DEFINE FIELD brief           ON kb_class TYPE option<string>",
    "DEFINE FIELD description     ON kb_class TYPE option<string>",
    "DEFINE FIELD search_text     ON kb_class TYPE option<string>",
    "DEFINE FIELD embedding       ON kb_class TYPE option<array<float>>",
    f"DEFINE INDEX kb_class_vec  ON kb_class FIELDS embedding HNSW DIMENSION {_DIM}",
    "DEFINE INDEX kb_class_fts   ON kb_class FIELDS search_text SEARCH ANALYZER kb_analyzer BM25",
    # kb_method
    "DEFINE TABLE kb_method SCHEMAFULL",
    "DEFINE FIELD engine          ON kb_method TYPE string",
    "DEFINE FIELD engine_version  ON kb_method TYPE string",
    "DEFINE FIELD class_name      ON kb_method TYPE string",
    "DEFINE FIELD name            ON kb_method TYPE string",
    "DEFINE FIELD return_type     ON kb_method TYPE option<string>",
    "DEFINE FIELD signature       ON kb_method TYPE option<string>",
    "DEFINE FIELD description     ON kb_method TYPE option<string>",
    "DEFINE FIELD qualifiers      ON kb_method TYPE option<string>",
    "DEFINE FIELD search_text     ON kb_method TYPE option<string>",
    "DEFINE FIELD embedding       ON kb_method TYPE option<array<float>>",
    f"DEFINE INDEX kb_method_vec ON kb_method FIELDS embedding HNSW DIMENSION {_DIM}",
    "DEFINE INDEX kb_method_fts  ON kb_method FIELDS search_text SEARCH ANALYZER kb_analyzer BM25",
    # kb_property
    "DEFINE TABLE kb_property SCHEMAFULL",
    "DEFINE FIELD engine          ON kb_property TYPE string",
    "DEFINE FIELD engine_version  ON kb_property TYPE string",
    "DEFINE FIELD class_name      ON kb_property TYPE string",
    "DEFINE FIELD name            ON kb_property TYPE string",
    "DEFINE FIELD prop_type       ON kb_property TYPE option<string>",
    "DEFINE FIELD description     ON kb_property TYPE option<string>",
    "DEFINE FIELD setter          ON kb_property TYPE option<string>",
    "DEFINE FIELD getter          ON kb_property TYPE option<string>",
    "DEFINE FIELD default_value   ON kb_property TYPE option<string>",
    "DEFINE FIELD search_text     ON kb_property TYPE option<string>",
    "DEFINE INDEX kb_prop_fts    ON kb_property FIELDS search_text SEARCH ANALYZER kb_analyzer BM25",
    # kb_signal
    "DEFINE TABLE kb_signal SCHEMAFULL",
    "DEFINE FIELD engine          ON kb_signal TYPE string",
    "DEFINE FIELD engine_version  ON kb_signal TYPE string",
    "DEFINE FIELD class_name      ON kb_signal TYPE string",
    "DEFINE FIELD name            ON kb_signal TYPE string",
    "DEFINE FIELD description     ON kb_signal TYPE option<string>",
    "DEFINE FIELD params          ON kb_signal TYPE option<string>",
    "DEFINE FIELD search_text     ON kb_signal TYPE option<string>",
    "DEFINE INDEX kb_sig_fts     ON kb_signal FIELDS search_text SEARCH ANALYZER kb_analyzer BM25",
    # kb_constant
    "DEFINE TABLE kb_constant SCHEMAFULL",
    "DEFINE FIELD engine          ON kb_constant TYPE string",
    "DEFINE FIELD engine_version  ON kb_constant TYPE string",
    "DEFINE FIELD class_name      ON kb_constant TYPE string",
    "DEFINE FIELD name            ON kb_constant TYPE string",
    "DEFINE FIELD value           ON kb_constant TYPE option<string>",
    "DEFINE FIELD description     ON kb_constant TYPE option<string>",
    "DEFINE FIELD enum_name       ON kb_constant TYPE option<string>",
    "DEFINE FIELD search_text     ON kb_constant TYPE option<string>",
    "DEFINE INDEX kb_const_fts   ON kb_constant FIELDS search_text SEARCH ANALYZER kb_analyzer BM25",
    # kb_constructor
    "DEFINE TABLE kb_constructor SCHEMAFULL",
    "DEFINE FIELD engine          ON kb_constructor TYPE string",
    "DEFINE FIELD class_name      ON kb_constructor TYPE string",
    "DEFINE FIELD name            ON kb_constructor TYPE string",
    "DEFINE FIELD return_type     ON kb_constructor TYPE option<string>",
    "DEFINE FIELD signature       ON kb_constructor TYPE option<string>",
    "DEFINE FIELD description     ON kb_constructor TYPE option<string>",
    # kb_operator
    "DEFINE TABLE kb_operator SCHEMAFULL",
    "DEFINE FIELD engine          ON kb_operator TYPE string",
    "DEFINE FIELD class_name      ON kb_operator TYPE string",
    "DEFINE FIELD name            ON kb_operator TYPE string",
    "DEFINE FIELD return_type     ON kb_operator TYPE option<string>",
    "DEFINE FIELD signature       ON kb_operator TYPE option<string>",
    "DEFINE FIELD description     ON kb_operator TYPE option<string>",
    # kb_theme_item
    "DEFINE TABLE kb_theme_item SCHEMAFULL",
    "DEFINE FIELD engine          ON kb_theme_item TYPE string",
    "DEFINE FIELD class_name      ON kb_theme_item TYPE string",
    "DEFINE FIELD name            ON kb_theme_item TYPE string",
    "DEFINE FIELD data_type       ON kb_theme_item TYPE option<string>",
    "DEFINE FIELD description     ON kb_theme_item TYPE option<string>",
    "DEFINE FIELD default_value   ON kb_theme_item TYPE option<string>",
    # ── Graph edge tables ────────────────────────────────────────────
    "DEFINE TABLE inherits     SCHEMAFULL TYPE RELATION",
    "DEFINE TABLE has_method   SCHEMAFULL TYPE RELATION",
    "DEFINE TABLE has_property SCHEMAFULL TYPE RELATION",
    "DEFINE TABLE has_signal   SCHEMAFULL TYPE RELATION",
    "DEFINE TABLE has_constant SCHEMAFULL TYPE RELATION",
    # ── Project knowledge tables ─────────────────────────────────────
    "DEFINE TABLE kb_project SCHEMAFULL",
    "DEFINE FIELD name            ON kb_project TYPE string",
    "DEFINE FIELD engine          ON kb_project TYPE string",
    "DEFINE FIELD engine_version  ON kb_project TYPE option<string>",
    "DEFINE FIELD path            ON kb_project TYPE option<string>",
    "DEFINE FIELD last_scan       ON kb_project TYPE option<string>",
    # kb_project_file
    "DEFINE TABLE kb_project_file SCHEMAFULL",
    "DEFINE FIELD project         ON kb_project_file TYPE string",
    "DEFINE FIELD path            ON kb_project_file TYPE string",
    "DEFINE FIELD file_hash       ON kb_project_file TYPE string",
    "DEFINE FIELD language        ON kb_project_file TYPE option<string>",
    "DEFINE FIELD summary         ON kb_project_file TYPE option<string>",
    "DEFINE FIELD search_text     ON kb_project_file TYPE option<string>",
    "DEFINE FIELD embedding       ON kb_project_file TYPE option<array<float>>",
    "DEFINE FIELD stored_path     ON kb_project_file TYPE option<string>",
    "DEFINE FIELD updated_at      ON kb_project_file TYPE option<string>",
    f"DEFINE INDEX kb_pf_vec     ON kb_project_file FIELDS embedding HNSW DIMENSION {_DIM}",
    "DEFINE INDEX kb_pf_fts      ON kb_project_file FIELDS search_text SEARCH ANALYZER kb_analyzer BM25",
    # Project graph edges
    "DEFINE TABLE depends_on     SCHEMAFULL TYPE RELATION",
    "DEFINE TABLE attached_to    SCHEMAFULL TYPE RELATION",
    "DEFINE TABLE extends_class  SCHEMAFULL TYPE RELATION",
    # ── Chat tables ────────────────────────────────────────────────────
    "DEFINE TABLE chat_thread SCHEMAFULL",
    "DEFINE FIELD project        ON chat_thread TYPE string",
    "DEFINE FIELD title          ON chat_thread TYPE string",
    "DEFINE FIELD provider       ON chat_thread TYPE option<string>",
    "DEFINE FIELD created_at     ON chat_thread TYPE string",
    "DEFINE FIELD updated_at     ON chat_thread TYPE string",
    "DEFINE INDEX chat_thread_project ON chat_thread FIELDS project",
    # chat_message
    "DEFINE TABLE chat_message SCHEMAFULL",
    "DEFINE FIELD thread         ON chat_message TYPE record<chat_thread>",
    "DEFINE FIELD role           ON chat_message TYPE string",
    "DEFINE FIELD content        ON chat_message TYPE string",
    "DEFINE FIELD metadata       ON chat_message TYPE option<object>",
    "DEFINE FIELD created_at     ON chat_message TYPE string",
    "DEFINE INDEX chat_msg_thread ON chat_message FIELDS thread, created_at",
]


async def apply_schema(db) -> None:
    """Apply the full KB schema if the stored version is outdated."""

    # Ensure kb_meta exists (schemaless, survives migrations).
    try:
        await db.query("DEFINE TABLE kb_meta")
    except Exception:
        pass  # already exists

    # Check stored version.
    try:
        result = await db.query("SELECT version FROM kb_meta:schema_version")
        if (
            isinstance(result, list)
            and len(result) > 0
            and result[0].get("version") == SCHEMA_VERSION
        ):
            logger.info("KB schema v%d already applied", SCHEMA_VERSION)
            return
    except Exception:
        pass

    logger.info("Applying KB schema v%d …", SCHEMA_VERSION)

    # Remove existing tables (reverse order — edges first).
    for table in ALL_TABLES:
        try:
            await db.query(f"REMOVE TABLE {table}")
        except Exception:
            pass

    # Remove analyzer so it can be recreated.
    try:
        await db.query("REMOVE ANALYZER kb_analyzer")
    except Exception:
        pass

    # Apply all statements.
    for stmt in SCHEMA_STATEMENTS:
        await db.query(stmt)

    # Record version.
    await db.query(
        "UPSERT kb_meta:schema_version SET version = $v",
        {"v": SCHEMA_VERSION},
    )
    logger.info("KB schema v%d applied", SCHEMA_VERSION)
