"""Lightweight RAG over parsed course data."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.shared.services.llm.embeddings import EmbeddingsService


class ParsedDataRetriever:
    """Builds a tiny in-memory index from parsed_data.json."""

    def __init__(
        self,
        data_path: Optional[Path] = None,
        embeddings: Optional[EmbeddingsService] = None,
        chunk_size: int = 180,
        max_content_chunks: int = 12,
    ) -> None:
        backend_root = Path(__file__).resolve().parents[3]
        self.data_path = Path(data_path) if data_path else backend_root / "course_service" / "data" / "parsed_data.json"
        self.embeddings = embeddings or EmbeddingsService()
        self.chunk_size = max(40, chunk_size)
        self.max_content_chunks = max_content_chunks
        self._index: List[Dict[str, Any]] | None = None

    def _chunk(self, text: str) -> List[str]:
        words = text.split()
        return [" ".join(words[i : i + self.chunk_size]) for i in range(0, len(words), self.chunk_size)]

    def _build_index(self) -> List[Dict[str, Any]]:
        if self._index is not None:
            return self._index
        if not self.data_path.exists():
            self._index = []
            return self._index

        with open(self.data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        entries: List[Dict[str, Any]] = []
        for file_key, file_data in data.items():
            summary_text = file_data.get("summary") or ""
            content_text = file_data.get("content") or ""

            summary_chunks = self._chunk(summary_text) if summary_text else []
            content_chunks = self._chunk(content_text)[: self.max_content_chunks] if content_text else []

            for chunk in summary_chunks + content_chunks:
                entries.append(
                    {
                        "text": chunk,
                        "file": file_key,
                        "embedding": self.embeddings.get_embedding(chunk),
                    }
                )

        self._index = entries
        return self._index

    def search(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        index = self._build_index()
        if not index:
            return []

        query_emb = self.embeddings.get_embedding(query)
        scored = sorted(
            index,
            key=lambda item: self.embeddings.cosine_similarity(query_emb, item["embedding"]),
            reverse=True,
        )
        return scored[:limit]

