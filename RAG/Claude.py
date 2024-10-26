import os
from typing import List
from anthropic import Anthropic
import chromadb
from chromadb.utils import embedding_functions
import textwrap

class RAGSystem:
    def __init__(self, api_key: str, collection_name: str = "documents"):
        """
        Initialize the RAG system with Claude and ChromaDB
        
        Args:
            api_key: Anthropic API key
            collection_name: Name for the ChromaDB collection
        """
        self.client = Anthropic(api_key=api_key)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.Client()
        
        # Use OpenAI embeddings for better compatibility
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-ada-002"
        )
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )

    def add_documents(self, texts: List[str], ids: List[str] = None):
        """
        Add documents to the vector store
        
        Args:
            texts: List of text documents to add
            ids: Optional list of IDs for the documents
        """
        if ids is None:
            ids = [str(i) for i in range(len(texts))]
            
        self.collection.add(
            documents=texts,
            ids=ids
        )

    def retrieve_relevant_docs(self, query: str, n_results: int = 3) -> List[str]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: The search query
            n_results: Number of documents to retrieve
            
        Returns:
            List of relevant document texts
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return results['documents'][0]

    def generate_response(self, query: str, context: List[str]) -> str:
        """
        Generate a response using Claude with retrieved context
        
        Args:
            query: User query
            context: Retrieved relevant documents
            
        Returns:
            Generated response
        """
        # Create system prompt with context
        system_prompt = f"""You are a helpful AI assistant. Use the following context to answer the user's question.
        If the context doesn't contain relevant information, say so.
        
        Context:
        {' '.join(context)}
        
        Answer the question based on the context above."""
        
        # Generate response using Claude
        message = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"Question: {query}\nPlease provide a detailed answer based on the given context."
                }
            ],
            system=system_prompt
        )
        
        return message.content[0].text

    def query(self, query: str, n_docs: int = 3) -> str:
        """
        End-to-end RAG pipeline
        
        Args:
            query: User query
            n_docs: Number of documents to retrieve
            
        Returns:
            Generated response
        """
        # Retrieve relevant documents
        relevant_docs = self.retrieve_relevant_docs(query, n_docs)
        
        # Generate response
        response = self.generate_response(query, relevant_docs)
        
        return response

# Example usage
def main():
    # Initialize RAG system
    rag = RAGSystem(api_key="your-api-key")
    
    # Add some sample documents
    documents = [
        "The capital of France is Paris. It is known for the Eiffel Tower.",
        "London is the capital of England. Big Ben is a famous landmark.",
        "Tokyo is Japan's capital city. It's known for its technology."
    ]
    rag.add_documents(documents)
    
    # Query the system
    query = "What is the capital of France?"
    response = rag.query(query)
    print(f"Query: {query}")
    print(f"Response: {response}")

if __name__ == "__main__":
    main()