import chromadb
from chromadb.utils import embedding_functions
import os
from dotenv import load_dotenv

load_dotenv()

class PortfolioVectorDB:
    def __init__(self, collection_name="resume_vault"):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        # Using default embedding function (sentence-transformers) or can use OpenAI/OpenRouter
        # For simplicity and offline capability (partially), using default hue. 
        # But for high quality, we'll suggest OpenAI embeddings in the future.
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def upsert_resume(self, user_id, resume_id, text_chunks, metadata_list):
        """Adds or updates resume chunks, scoped by user_id."""
        ids = [f"u{user_id}_{resume_id}_{i}" for i in range(len(text_chunks))]
        # Add user_id to metadata to ensure correct filtering
        for meta in metadata_list:
            meta["user_id"] = user_id
            
        self.collection.upsert(
            documents=text_chunks,
            metadatas=metadata_list,
            ids=ids
        )

    def query_resume(self, user_id, query_text, n_results=3):
        """Retrieves relevant chunks, strictly filtered by user_id."""
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where={"user_id": user_id}
        )
        return results["documents"][0] if results["documents"] else []

if __name__ == "__main__":
    db = PortfolioVectorDB()
    print("ChromaDB initialized.")
