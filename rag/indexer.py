import os
import pymupdf
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from sentence_transformers import SentenceTransformer
import uuid

class DocumentIndexer:
    def __init__(self, storage_path: str = "qdrant_storage", collection_name: str = "textbooks"):
        # Initialize lightweight embedding model
        print("Loading embedding model (MiniLM)...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Initialize local Qdrant (saves to disk, no Docker needed!)
        os.makedirs(storage_path, exist_ok=True)
        self.client = QdrantClient(path=storage_path)
        self.collection_name = collection_name
        
        # Create collection if it doesn't exist
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=self.model.get_sentence_embedding_dimension(), distance=Distance.COSINE),
            )

    def extract_and_chunk(self, pdf_path: str, chunk_size: int = 500) -> list[str]:
        print(f"Extracting text from {pdf_path}...")
        doc = pymupdf.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text("text") + " "
            
        # Basic chunking by rough character limit (respecting sentence boundaries roughly)
        chunks = []
        words = full_text.split()
        current_chunk = []
        current_len = 0
        
        for word in words:
            current_chunk.append(word)
            current_len += len(word) + 1
            if current_len >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_len = 0
                
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks

    def index_pdf(self, pdf_path: str):
        chunks = self.extract_and_chunk(pdf_path)
        print(f"Generated {len(chunks)} chunks. Embedding and indexing...")
        
        # Embed all chunks
        embeddings = self.model.encode(chunks)
        
        # Create Qdrant points
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload={"text": chunk, "source": os.path.basename(pdf_path)}
            ))
            
        # Upload to local DB
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"Successfully indexed {len(chunks)} chunks into '{self.collection_name}'.")

if __name__ == "__main__":
    # Test script usage
    pass
