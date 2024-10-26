# Custom Libraries:
import Embedding
import Claude
import os



def call(Prompt):
    rag = Embedding.RAGSystem(api_key="your-api-key")
    
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
