import os
import chromadb
import voyageai
from dotenv import load_dotenv
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, collection_name: str):
        # Load environment variables
        load_dotenv()
        self.voyage_api_key = os.getenv("VOYAGE_API_KEY")
        print(f"{self.voyage_api_key}")

        if not self.voyage_api_key:
            logger.error("VOYAGE_API_KEY not found in environment variables")
            raise ValueError("VOYAGE_API_KEY not found in environment variables")

        # Initialize VoyageAI client
        voyageai.api_key = self.voyage_api_key

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path="./chroma_db")

        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": f"Collection for {collection_name} embeddings"}
        )

        logger.info(f"Initialized VectorStore with collection: {collection_name}")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Fetch embeddings from VoyageAI for the given texts."""
        try:
            # Adjust parameters based on VoyageAI API documentation
            response = voyageai.Embedding.create(
                input=texts,  # Assuming 'input' is the correct parameter
                model="voyage-2"  # Change model as needed
            )
            
            # Extract embeddings from the response
            embeddings = [item['embedding'] for item in response['data']]
            return embeddings
        except Exception as e:
            logger.error(f"Error fetching embeddings: {str(e)}")
            raise
            
    def add_documents(self, documents: List[str], metadata: List[Dict[str, Any]] = None, ids: List[str] = None) -> None:
        """Add documents to the vector store with optional metadata and IDs."""
        try:
            embeddings = self.get_embeddings(documents)  # Fetch embeddings first
            if metadata is None:
                metadata = [{}] * len(documents)
            if ids is None:
                ids = [str(i) for i in range(len(documents))]
            
            self.collection.add(
                documents=documents,
                metadatas=metadata,
                ids=ids,
                embeddings=embeddings  # Add embeddings directly
            )
            logger.info(f"Successfully added {len(documents)} documents to the collection")
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise

    def query(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """Query the vector store for similar documents."""
        try:
            query_embedding = self.get_embeddings([query_text])[0]  # Get embedding for the query
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            logger.info(f"Successfully queried collection with: {query_text}")
            return results
        except Exception as e:
            logger.error(f"Error querying collection: {str(e)}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the current collection."""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection.name,
                "document_count": count,
                "peek": self.collection.peek()
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Initialize vector store
    vector_store = VectorStore(collection_name="my_documents")
    
    # Example documents
    documents = [
        "BOOK1"
    ]
    
    # Example metadata
    metadata = [
        {"category": "example", "source": "test"},
    ]
    
    # Add documents
    vector_store.add_documents(documents=documents, metadata=metadata)
    
    # Perform a query
    results = vector_store.query(query_text="Name all the characters of the story.", n_results=2)
    
    # Get collection statistics
    stats = vector_store.get_collection_stats()
    print(f"Collection stats: {stats}")
