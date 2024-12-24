import rag as r
from Databases import User
import os
from dotenv import load_dotenv

#To load the key
load_dotenv()

user_data = User()

def main():
    voyage_api = os.getenv("VOYAGE_API_KEY")
    print(voyage_api)

    Voyage = r.VoyageEmbedding(voyage_api)

    text_chunks = Voyage.user_data()

    if not text_chunks:
        print("No text chunks generated; check the file path or content.")
        return
    
    vector_chunks = Voyage.vectorize(text_chunks)
    print(f"Vectorizr chunks:\n{vector_chunks}\n")

    if not vector_chunks:
        print("No vectorized chunks; vectorization failed or no content to vectorize.")
        return
    

    # Set up ChromaDB for persistent storagev
    persist_directory = "./Vector_UserDB"
    if not os.path.exists(persist_directory):
        print("VectorDB directory doesn't exist; creating it now...")

    # Initialize VectorDB and append vectorized data
    Personal_DB = r.VectorDB(persist_directory=persist_directory)
    for idx, vector in enumerate(vector_chunks):
        doc_id = f"doc_{idx}"
        Personal_DB.append(embedding=vector, doc_id=doc_id)

    # Convert text query to embedding first
    query_text = "Age"
    query_embedding = Voyage.embedding_model.encode(query_text)
    search_results = Personal_DB.semantic_search(query_embedding=query_embedding)
    print("\nChromaDB Search Results for 'Age':\n", search_results)
    
    # DEMO OF NEW FUNCTIONALITY
    print("\n=== Demonstrating New Search Capabilities ===")
    
    # 1. Demonstrate hybrid search with a sample query
    hybrid_results = Voyage.hybrid_search(
        query="Depression symptoms and treatment",
        top_k=3,
        semantic_weight=0.7
    )
    print("\nHybrid Search Results:")
    for idx, result in enumerate(hybrid_results, 1):
        print(f"\nResult {idx}:")
        print(f"Text: {result['text'][:200]}...")
        print(f"Combined Score: {result['similarity_score']:.3f}")
        print(f"Semantic Score: {result['semantic_score']:.3f}")
        print(f"Lexical Score: {result['lexical_score']:.3f}")

    # 2. Demonstrate embedding_to_text with an embedding
    sample_embedding = query_embedding  # Using the depression query embedding as example
    similar_texts = Voyage.embedding_to_text(
        embedding=sample_embedding,
        top_k=2,
        similarity_threshold=0.5
    )
    print("\nEmbedding to Text Results:")
    for idx, result in enumerate(similar_texts, 1):
        print(f"\nResult {idx}:")
        print(f"Text: {result['text'][:200]}...")
        print(f"Similarity Score: {result['similarity_score']:.3f}")

if __name__ == "__main__":
    main()