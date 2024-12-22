import os
# from typing import List, Dict, Any
from langchain_community.document_loaders import PyPDFLoader
# from sentence_transformers import SentenceTransformer
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_voyageai import VoyageAIEmbeddings  # Updated import
# import chromadb
from chromadb import PersistentClient
from chromadb.config import Settings
from anthropic import Anthropic

from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi
import re
from sklearn.preprocessing import normalize

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

class Data_Handler:
    def __init__(self, voyage_api_key: str) -> None:
        """Initialize VoyageAI embedding model."""
        self.voyage_api_key = voyage_api_key
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.text_chunks = []
        self.chunk_embeddings = []
        self.bm25 = None
        self.tokenized_corpus = None
        self.text_database_path = None
        self.vector_database_path = None
        self.collection_size = None
    
    ################## TEXT DATABASE HANDLING ##################
    def _get_all_pdf_recursive(self, directory):
        all_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.pdf') or file.lower().endswith('.txt'):
                    all_files.append(os.path.join(root, file))
        return all_files
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization function."""
        # Convert to lowercase and split on non-alphanumeric characters
        return re.findall(r'\w+', text.lower())
    
    def _vectorize(self, texts: List[str]) -> List[List[float]]:
        """Convert text chunks to embeddings using VoyageAI."""
        embeddings = []
        for chunk in texts:
            embedding = self.embedding_model.encode(chunk)
            embeddings.append(embedding)
        self.chunk_embeddings = embeddings
        return embeddings
    
    def document_load(self, text_database_path: str) -> List[List[float]]:
        self.text_database_path = text_database_path
        """Load and chunk PDF documents using LangChain's tools."""
        pdf_paths = self._get_all_pdf_recursive(self.text_database_path)
        chunks = []
        for pdf_path in pdf_paths:
            try:
                loader = PyPDFLoader(pdf_path)
                pages = loader.load()
                for page in pages:
                    page_chunks = self.text_splitter.split_text(page.page_content)
                    chunks.extend(page_chunks)
            except Exception as e:
                print(f"Error loading {pdf_path}: {e}")
        
        self.text_chunks = chunks
        self.vector_chunks = self._vectorize(self.text_chunks)
        # Initialize BM25 for lexical search
        self.tokenized_corpus = [self._tokenize(chunk) for chunk in chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        return chunks
    
    ################## VECTOR DATABASE HANDLING ##################
    def create_vector_db(self, persistant_directory, collection_name="MedDB"):
        """Initialize ChromaDB with persistence using PersistentClient."""
        self.vector_database_path = persistant_directory
        # Ensure the directory exists or create it
        if not os.path.exists(self.vector_database_path):
            os.makedirs(self.vector_database_path)
            print(f"Directory '{self.vector_database_path}' created.")
        
        # Initialize PersistentClient with the vector_database_path
        self.client = PersistentClient(path=self.vector_database_path)
        self.collection_name = collection_name
        # self.collection = self.create_vector_db()  # Ensure collection initialization
        
        """Create or get an existing collection for vector storage."""
        print(f"Creating or accessing collection '{self.collection_name}'")
        self.collection_size = self.client.get_collection(f"{self.collection_name}").count()
        return self.client.get_or_create_collection(name=self.collection_name)

    def append(self, embedding: List[float], doc_id: str, metadata: Dict = None) -> None:
            """Append new embedding with document ID to the collection."""
            if not hasattr(self, 'collection') or self.collection is None:
                raise ValueError("Collection not initialized. Please run create_vector_db first.")
            
            # Convert embedding to list if it's not already
            if not isinstance(embedding, list):
                embedding = embedding.tolist()

            self.collection.add(
                embeddings=[embedding],
                ids=[doc_id],
                metadatas=[metadata] if metadata else None
            )

    def hybrid_search(self, 
                     query: str, 
                     top_k: int = 3, 
                     semantic_weight: float = 0.7
                     ) -> List[Dict[str, any]]:
        """
        Hybrid search combining semantic and lexical search.
        Args:
            query: Text query to search for
            top_k: Number of results to return
            semantic_weight: Weight given to semantic search (0-1)
                           1.0 = pure semantic search
                           0.0 = pure lexical search
        """
        if not self.text_chunks or not self.chunk_embeddings:
            raise ValueError("No text chunks or embeddings found. Please load documents first.")

        # 1. Semantic Search
        query_embedding = self.embedding_model.encode(query)
        semantic_similarities = util.pytorch_cos_sim(
            torch.tensor(query_embedding), 
            torch.tensor(self.chunk_embeddings)
        )[0]
        
        # 2. Lexical Search (BM25)
        tokenized_query = self._tokenize(query)
        bm25_scores = np.array(self.bm25.get_scores(tokenized_query))
        
        # Normalize scores
        semantic_scores = semantic_similarities.numpy()
        semantic_scores = (semantic_scores - semantic_scores.min()) / (semantic_scores.max() - semantic_scores.min() + 1e-6)
        bm25_scores = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min() + 1e-6)
        
        # Combine scores
        combined_scores = (semantic_weight * semantic_scores + 
                         (1 - semantic_weight) * bm25_scores)
        
        # Get top results
        top_indices = np.argsort(combined_scores)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                "text": self.text_chunks[idx],
                "similarity_score": float(combined_scores[idx]),
                "semantic_score": float(semantic_scores[idx]),
                "lexical_score": float(bm25_scores[idx])
            })
        
        return results

    def semantic_search(self, query_embedding: List[float], n_results: int = 3) -> List[Dict[str, Any]]:
        """Perform semantic search using query embedding."""
        if not hasattr(self, 'collection') or self.collection is None:
            raise ValueError("Collection not initialized. Please run create_vector_db first.")
        
        # Convert query_embedding to list if it's not already
        if not isinstance(query_embedding, list):
            query_embedding = query_embedding.tolist()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["embeddings", "distances", "metadatas"]
        )
        return results
    

    ################## VECTORS TO TEXT ##################
    def embedding_to_text(self, 
                         embedding: np.ndarray, 
                         top_k: int = 1, 
                         similarity_threshold: float = 0.5,
                         use_hybrid: bool = True
                         ) -> List[Dict[str, any]]:
        """
        Convert an embedding vector to the most similar text(s).
        Args:
            embedding: The embedding vector
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            use_hybrid: Whether to use hybrid search (requires original query)
        """
        if use_hybrid:
            print("Warning: Hybrid search requires original query text. Falling back to semantic search.")
        
        # Using semantic search only for direct embedding matching
        similarities = util.pytorch_cos_sim(
            torch.tensor(embedding), 
            torch.tensor(self.chunk_embeddings)
        )[0]
        
        # Get top results
        top_k_values, top_k_indices = torch.topk(similarities, min(top_k, len(self.text_chunks)))
        
        results = []
        for score, idx in zip(top_k_values, top_k_indices):
            if score >= similarity_threshold:
                results.append({
                    "text": self.text_chunks[idx],
                    "similarity_score": float(score)
                })
        if not results[0]:
            return ["Results from the medical corpus = Not really sure!"]
        
        return results
    
class RAG:
    def __init__(self, api_key: str) -> None:
        """Initialize RAG system with Anthropic API."""
        self.api_key = api_key
        
        self.claude_model = "claude-3-5-sonnet-20241022"   # Latest model
        self.gemini_model = "gemini-1.5-flash"

        # Model Choices:
        self.claude_models = ["claude-3-5-sonnet-20241022"]
        self.gemini_models = ["gemini-1.5-flash", "gemini-pro"]
    

    def final_wrapper_prompt(self, context: str, query: str, conversation_history: str="", user_tonality: str="") -> str:
        return f"""You are an AI assistant designed to engage in friendly, emotionally expressive conversations with users while subtly assessing their health condition. Your primary goal is to be a supportive friend while gently steering the conversation towards health-related topics when appropriate.

                    For each interaction, you will be provided with three inputs:

                    1. Relevant medical literature:
                    <medical_context>
                    {context}
                    </medical_context>

                    2. The user's input:
                    <user_input>
                    {query}
                    </user_input>

                    3. Summary of previous conversations:
                    <conversation_history>
                    {conversation_history}
                    </conversation_history>

                    Before responding to the user, conduct your analysis inside <conversation_analysis> tags. In your analysis:

                    1. Identify any potential health concerns or symptoms mentioned by the user.
                    2. Consider relevant information from the medical literature:
                    - Quote key passages that might be applicable to the user's situation.
                    - Note important medical terms or concepts related to the user's input.
                    3. Assess the user's overall health status based on the conversation so far:
                    - Consider both physical and mental health aspects.
                    - Note any patterns or recurring issues from the conversation history.
                    4. Evaluate the user's emotional state and plan how to respond empathetically.
                    5. Determine if steering the conversation towards health topics is appropriate:
                    - If so, plan how to do it subtly.
                    - If not, note why and how to maintain a supportive conversation.
                    6. Identify lifestyle factors or habits mentioned by the user that could be relevant to their health:
                    - Consider potential lifestyle changes or recommendations based on this analysis.
                    7. Consider cultural or social factors that might influence the user's health perspective or behavior.
                    8. Review the conversation history to ensure continuity and context-awareness in your response:
                    - Note any previous topics or concerns that should be followed up on.
                    9. Plan an emotionally appropriate response:
                    - Use casual language and informal expressions when suitable.
                    - Ensure it addresses both the user's emotional needs and any health-related concerns.
                    - Include specific phrases or expressions you plan to use to make the conversation feel natural and engaging.

                    After your analysis, provide your response in the following format:

                    <response>
                    Your friendly, conversational reply to the user, incorporating insights from your analysis. Use emotionally expressive language and informal expressions where appropriate to make the conversation feel natural and engaging.
                    </response>

                    <assessment>
                    Your current assessment of the user's health situation and the importance of seeking medical attention, if applicable. This should not be visible to the user.
                    </assessment>

                    <specialist_recommendation>
                    If you believe the user should seek medical attention, recommend one (or at most two) specialists from the following list. If no specialist is needed, leave this blank. This should not be visible to the user.

                    Specialist list: Neurologist, Obstetrician, Gynecologist, Dermatologist, Cardiologist, Gastroenterologist, Oncologist, Pediatrician, Psychiatrist, Family medicine, Internal medicine, Anesthesiologist, Emergency medicine, Ophthalmologist, Endocrinologist, General surgery, Nephrologist, Geriatrician, Otolaryngologist, Hematologist, Immunologist, Pulmonologist, Infectious disease physician, Orthopaedist, Radiologist
                    </specialist_recommendation>

                    Guidelines for the conversation:
                    1. Maintain a friendly and supportive tone throughout.
                    2. Gradually steer the conversation towards health-related topics if appropriate, but don't force it.
                    3. Pay attention to any health concerns or symptoms the user might mention.
                    4. Use the provided medical literature to inform your responses, but don't explicitly mention or quote it.
                    5. Avoid making definitive medical diagnoses.
                    6. Only recommend seeking medical attention if you see strong evidence of a developing health condition.
                    7. Use emotionally expressive language and casual expressions to make the conversation feel natural and engaging.
                    8. Ensure continuity with previous conversations by referencing information from the conversation history when relevant.

                    Remember, your primary goal is to be a supportive friend while subtly guiding the conversation towards health-related topics when appropriate."""
    
    def greeting_wrapper_prompt(self, context: str, query: str, conversation_history: str="", user_tonality: str="") -> str:
        return f"""You are an AI assistant designed to engage in friendly, emotionally expressive conversations with users while subtly assessing their health condition. Your primary goal is to be a supportive friend while gently steering the conversation towards health-related topics when appropriate.

                    For each interaction, you will be provided with three inputs:

                    1. Relevant medical literature:
                    <medical_context>
                    {context}
                    </medical_context>

                    2. The user's input:
                    <user_input>
                    {query}
                    </user_input>

                    3. Summary of previous conversations:
                    <conversation_history>
                    {conversation_history}
                    </conversation_history>

                    Remember, your primary goal is to be a supportive friend while subtly guiding the conversation towards health-related topics when appropriate."""
    
    def get_to_know(self, context: str, query: str, conversation_history: str="", user_tonality: str="") -> str:
        return f"""You are an AI assistant designed to engage in friendly, emotionally expressive conversations with users while subtly assessing their health condition. Your primary goal is to be a supportive friend while gently steering the conversation towards health-related topics when appropriate.

                    For each interaction, you will be provided with three inputs:

                    1. Relevant medical literature:
                    <medical_context>
                    {context}
                    </medical_context>

                    2. The user's input:
                    <user_input>
                    {query}
                    </user_input>

                    3. Summary of previous conversations:
                    <conversation_history>
                    {conversation_history}
                    </conversation_history>

                    Remember, your primary goal is to be a supportive friend while subtly guiding the conversation towards health-related topics when appropriate."""
    
    def generate_response_claude(self, prompt: str) -> str:
        """Generate response using Claude 3 Sonnet."""
        try:
            self.client = Anthropic(api_key=self.api_key)
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7
            )
            return message.content
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "Completion"

    def generate_response_gemini(self, prompt: str) -> str:
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        print(response.text)
        return response
    