from backend.app.schemas.document import SourceChunk
from backend.app.services.embedding import EmbeddingService
from backend.app.services.vector_store import FaissVectorStore


class RetrieverService:
    def __init__(self, embedding_service: EmbeddingService, vector_store: FaissVectorStore) -> None:
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(self, workspace_id: str, question: str, top_k: int) -> list[SourceChunk]:
        query_vector = self.embedding_service.embed_query(question)
        results = self.vector_store.search(workspace_id, query_vector, top_k)
        return [
            SourceChunk(
                chunk_id=item["chunk_id"],
                document_id=item["document_id"],
                source_name=item["source_name"],
                text=item["text"],
                score=item["score"],
                page_number=item.get("page_number"),
            )
            for item in results
        ]
