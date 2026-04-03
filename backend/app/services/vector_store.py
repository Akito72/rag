import json
from pathlib import Path

import faiss
import numpy as np

from backend.app.models.domain import DocumentChunk


class FaissVectorStore:
    def __init__(self, index_dir: Path) -> None:
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def upsert(self, workspace_id: str, embeddings: np.ndarray, chunks: list[DocumentChunk]) -> None:
        if len(chunks) == 0:
            return

        index_path = self.index_dir / f"{workspace_id}.faiss"
        metadata_path = self.index_dir / f"{workspace_id}.json"
        dimension = int(embeddings.shape[1])

        if index_path.exists():
            index = faiss.read_index(str(index_path))
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        else:
            index = faiss.IndexFlatIP(dimension)
            metadata = []

        index.add(embeddings)
        metadata.extend(
            [
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "workspace_id": chunk.workspace_id,
                    "text": chunk.text,
                    "source_name": chunk.source_name,
                    "page_number": chunk.page_number,
                    "metadata": chunk.metadata,
                }
                for chunk in chunks
            ]
        )

        faiss.write_index(index, str(index_path))
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    def search(self, workspace_id: str, query_vector: np.ndarray, top_k: int) -> list[dict]:
        index_path = self.index_dir / f"{workspace_id}.faiss"
        metadata_path = self.index_dir / f"{workspace_id}.json"
        if not index_path.exists() or not metadata_path.exists():
            return []

        index = faiss.read_index(str(index_path))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

        query = np.expand_dims(query_vector.astype("float32"), axis=0)
        scores, indices = index.search(query, top_k)

        matches: list[dict] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(metadata):
                continue
            item = metadata[idx].copy()
            item["score"] = float(score)
            matches.append(item)
        return matches
