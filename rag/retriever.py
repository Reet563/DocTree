import os
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class DocumentRetriever:
    def __init__(self, storage_path: str = "qdrant_storage", collection_name: str = "textbooks"):
        # We must use the exact same embedding model used for indexing
        print("Loading embedding model (MiniLM) for retrieval...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        self.client = QdrantClient(path=storage_path)
        self.collection_name = collection_name
        
    def retrieve_context(self, query: str, top_k: int = 5, threshold: float = 0.70) -> str:
        """
        Retrieves the top_k most relevant chunks for the query, filtered by a strict
        cosine similarity threshold so the LLM isn't fed irrelevant garbage.
        """
        print(f"Retrieving context for query: '{query}'")
        query_vector = self.model.encode(query).tolist()
        
        search_results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            with_payload=True,
            score_threshold=threshold # This enforces our strict cutoff!
        ).points
        
        if not search_results:
            print(f"No context found exceeding threshold {threshold}.")
            return ""
            
        print(f"Found {len(search_results)} highly relevant chunks.")
        
        context_parts = []
        for i, hit in enumerate(search_results):
            text = hit.payload.get("text", "")
            source = hit.payload.get("source", "Unknown")
            context_parts.append(f"[Source: {source} (Score: {hit.score:.2f})]\n{text}")
            
        return "\n\n".join(context_parts)
