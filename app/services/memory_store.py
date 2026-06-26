import hashlib
import json
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api import ClientAPI
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from app.config import Settings
from app.models.user import PostRecord, UserProfile

logger = logging.getLogger(__name__)


class HashEmbeddingFunction(EmbeddingFunction):
    """Lightweight local embeddings — no model download required."""

    def __init__(self) -> None:
        pass

    def name(self) -> str:
        return "hash-embedding"

    def __call__(self, input: Documents) -> Embeddings:
        vectors: Embeddings = []
        for text in input:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            vec = [float(b) / 255.0 for b in digest]
            while len(vec) < 384:
                vec.extend(vec[: min(384 - len(vec), len(vec))])
            vectors.append(vec[:384])
        return vectors


def _sqlite_path_from_url(database_url: str) -> str:
    if database_url.startswith("sqlite:///"):
        raw = database_url.replace("sqlite:///", "", 1)
        return str(Path(raw))
    return "./data/linkaid.db"


class MemoryService:
    """Long-term memory: SQLite for structured data, ChromaDB for semantic retrieval."""

    def __init__(
        self,
        settings: Settings,
        chroma_client: ClientAPI | None = None,
        embedding_function: EmbeddingFunction | None = None,
    ) -> None:
        self.settings = settings
        self.db_path = _sqlite_path_from_url(settings.database_url)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)

        self._embedding = embedding_function or HashEmbeddingFunction()
        self._chroma = chroma_client or chromadb.PersistentClient(
            path=settings.chroma_persist_dir
        )
        self._posts = self._chroma.get_or_create_collection(
            "linkaid_posts", embedding_function=self._embedding
        )
        self._context = self._chroma.get_or_create_collection(
            "linkaid_context", embedding_function=self._embedding
        )
        self._init_sqlite()

    def _init_sqlite(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS thread_summaries (
                    user_id TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, thread_id)
                )
                """
            )
            conn.commit()

    def get_profile(self, user_id: str) -> UserProfile | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT data FROM user_profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
        if not row:
            return None
        return UserProfile.model_validate(json.loads(row[0]))

    def save_profile(self, user_id: str, profile: UserProfile) -> UserProfile:
        profile.user_id = user_id
        now = datetime.now(UTC).isoformat()
        data = profile.model_dump_json()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO user_profiles (user_id, data, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    data = excluded.data, updated_at = excluded.updated_at
                """,
                (user_id, data, now),
            )
            conn.commit()

        self._index_entity_context(user_id, profile)
        logger.info("Saved profile for user=%s", user_id)
        return profile

    def add_post(self, user_id: str, post: PostRecord) -> PostRecord:
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO user_posts (user_id, data, created_at) VALUES (?, ?, ?)",
                (user_id, post.model_dump_json(), now),
            )
            conn.commit()

        doc_id = f"{user_id}-post-{now}"
        self._posts.upsert(
            ids=[doc_id],
            documents=[post.content],
            metadatas=[{"user_id": user_id, "post_type": post.post_type}],
        )
        logger.info("Added post for user=%s", user_id)
        return post

    def list_posts(self, user_id: str, limit: int = 50) -> list[PostRecord]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT data FROM user_posts WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [PostRecord.model_validate(json.loads(r[0])) for r in rows]

    def get_thread_summary(self, user_id: str, thread_id: str) -> str | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT summary FROM thread_summaries WHERE user_id = ? AND thread_id = ?",
                (user_id, thread_id),
            ).fetchone()
        return row[0] if row else None

    def save_thread_summary(self, user_id: str, thread_id: str, summary: str) -> None:
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO thread_summaries (user_id, thread_id, summary, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, thread_id) DO UPDATE SET
                    summary = excluded.summary, updated_at = excluded.updated_at
                """,
                (user_id, thread_id, summary, now),
            )
            conn.commit()

        doc_id = f"{user_id}-{thread_id}-summary"
        self._context.upsert(
            ids=[doc_id],
            documents=[summary],
            metadatas=[{"user_id": user_id, "type": "thread_summary", "thread_id": thread_id}],
        )

    def get_user_context(self, user_id: str, query: str | None = None) -> dict[str, Any]:
        profile = self.get_profile(user_id)
        context: dict[str, Any] = {}

        if profile:
            context.update(
                {
                    "name": profile.name,
                    "role": profile.role,
                    "niche": profile.niche,
                    "goals": profile.goals,
                    "competitors": profile.competitors,
                    "tech_stack": profile.tech_stack,
                    "target_audience": profile.target_audience,
                    "tone_preference": profile.tone_preference,
                    "language_mix": profile.language_mix,
                }
            )

        if query:
            relevant = self._search_context(user_id, query)
            if relevant:
                context["relevant_memory"] = relevant

        return context

    def _index_entity_context(self, user_id: str, profile: UserProfile) -> None:
        parts = []
        if profile.niche:
            parts.append(f"Niche: {profile.niche}")
        if profile.goals:
            parts.append(f"Goals: {', '.join(profile.goals)}")
        if profile.competitors:
            parts.append(f"Competitors: {', '.join(profile.competitors)}")
        if not parts:
            return

        text = " | ".join(parts)
        self._context.upsert(
            ids=[f"{user_id}-entities"],
            documents=[text],
            metadatas=[{"user_id": user_id, "type": "entities"}],
        )

    def _search_context(self, user_id: str, query: str, n: int = 3) -> list[str]:
        results = self._context.query(
            query_texts=[query],
            n_results=n,
            where={"user_id": user_id},
        )
        docs = results.get("documents", [[]])[0]
        return [d for d in docs if d]
