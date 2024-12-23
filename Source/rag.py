import os
from dotenv import load_dotenv
# from typing import List, Dict, Any
# from sentence_transformers import SentenceTransformer
# import chromadb
from chromadb.config import Settings
from anthropic import Anthropic

import re
import torch
import tiktoken
import numpy as np
from pathlib import Path
from sklearn.preprocessing import normalize
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer, util
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from chromadb import PersistentClient
from rank_bm25 import BM25Okapi

import google.generativeai as genai

# Load environment variables from the .env file
load_dotenv()

class DataHandler:
    """A class to handle document processing, embedding, and search operations."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", chunk_size: int = 1000, chunk_overlap: int = 100) -> None:
        """
        Initialize the DataHandler with specified parameters.

        Args:
            model_name: Name of the sentence transformer model to use
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between consecutive chunks
        """
        try:
            self.embedding_model = SentenceTransformer(model_name)
        except Exception as e:
            raise RuntimeError(f"Failed to load embedding model: {e}")

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        # Initialize empty containers
        self.text_chunks: List[str] = []
        self.chunk_embeddings: List[List[float]] = []
        self.bm25: Optional[BM25Okapi] = None
        self.tokenized_corpus: Optional[List[List[str]]] = None
        self.collection = None
    
    def _get_document_paths(self, directory: str | Path) -> List[Path]:
        """
        Recursively get all PDF and TXT files in a directory.

        Args:
            directory: Directory to search for documents

        Returns:
            List of Path objects for found documents
        """
        directory = Path(directory)
        if not directory.exists():
            raise FileNotFoundError(f"Directory {directory} does not exist")

        return [
            path for path in directory.rglob("*") 
            if path.suffix.lower() in {'.pdf', '.txt'}
        ]

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """
        Tokenize text into words.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        return re.findall(r'\w+', text.lower())

    def _compute_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Compute embeddings for a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            embeddings = [self.embedding_model.encode(chunk) for chunk in texts]
            self.chunk_embeddings = embeddings
            return embeddings
        except Exception as e:
            raise RuntimeError(f"Failed to compute embeddings: {e}")

    def load_documents(self, directory: str | Path) -> List[str]:
        """
        Load and process documents from a directory.

        Args:
            directory: Directory containing documents

        Returns:
            List of processed text chunks
        """
        chunks = []
        for doc_path in self._get_document_paths(directory):
            try:
                if doc_path.suffix.lower() == '.pdf':
                    loader = PyPDFLoader(str(doc_path))
                    pages = loader.load()
                    for page in pages:
                        page_chunks = self.text_splitter.split_text(page.page_content)
                        chunks.extend(page_chunks)
                else:  # .txt files
                    text = doc_path.read_text(encoding='utf-8')
                    text_chunks = self.text_splitter.split_text(text)
                    chunks.extend(text_chunks)
            except Exception as e:
                print(f"Error processing {doc_path}: {e}")
                continue

        self.text_chunks = chunks
        print(f"Loaded {len(self.text_chunks)} text chunks.")

        self.chunk_embeddings = self._compute_embeddings(chunks)
        print(f"Computed {len(self.chunk_embeddings)} embeddings.")

        self.tokenized_corpus = [self._tokenize(chunk) for chunk in chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        print("BM25 initialized successfully.")

        return chunks

    def initialize_vector_db(self, directory: str | Path, collection_name: str = "MedDB") -> None:
        """
        Initialize or connect to a vector database.

        Args:
            directory: Directory for persistent storage
            collection_name: Name of the collection
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        try:
            client = PersistentClient(path=str(directory))
            self.collection = client.get_or_create_collection(name=collection_name)
            print("Vector database initialized successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize vector database: {e}")

    def add_to_vector_db(self, embedding: List[float], doc_id: str, metadata: Optional[Dict] = None) -> None:
        """
        Add a document embedding to the vector database.

        Args:
            embedding: Document embedding
            doc_id: Unique document identifier
            metadata: Optional metadata for the document
        """
        if self.collection is None:
            raise ValueError("Vector database not initialized")

        try:
            self.collection.add(
                embeddings=[embedding if isinstance(embedding, list) else embedding.tolist()],
                ids=[doc_id],
                metadatas=[metadata] if metadata else None
            )
        except Exception as e:
            raise RuntimeError(f"Failed to add embedding to database: {e}")

    def hybrid_search(self, query: str, top_k: int = 3, semantic_weight: float = 0.5) -> List[Dict[str, Any]]:
        """
        Perform hybrid semantic and lexical search.

        Args:
            query: Search query
            top_k: Number of results to return
            semantic_weight: Weight for semantic search (0-1)

        Returns:
            List of search results with scores
        """
        if not self.text_chunks or not self.chunk_embeddings:
            raise ValueError("No documents loaded")

        # Semantic search
        query_embedding = self.embedding_model.encode(query)
        semantic_similarities = util.pytorch_cos_sim(
            torch.tensor(query_embedding), 
            torch.tensor(np.array(self.chunk_embeddings))
        )[0].numpy()

        # Lexical search
        bm25_scores = np.array(self.bm25.get_scores(self._tokenize(query)))

        # Normalize scores
        semantic_scores = (semantic_similarities - semantic_similarities.min()) / (semantic_similarities.max() - semantic_similarities.min() + 1e-6)
        bm25_scores = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min() + 1e-6)

        # Combine scores
        combined_scores = (semantic_weight * semantic_scores + (1 - semantic_weight) * bm25_scores)

        # Get top results
        top_indices = np.argsort(combined_scores)[-top_k:][::-1]

        results = [{
            "text": self.text_chunks[idx],
            "combined_score": float(combined_scores[idx]),
            "semantic_score": float(semantic_scores[idx]),
            "lexical_score": float(bm25_scores[idx])
        } for idx in top_indices]

        print("Search Results:", results)
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

    def summarizing_prompt(self, text_to_be_summarized: str) -> str:
        return f"""You are a summarizing bot. You are given a task to summarize a conversation between a user and an AI friend. 
        The AI friend is supposed to help the human user in any health aspect it possibly can. 
        If instead you were the friend of this user, what information would you have included in the summary to be remembered later? 
        Include those pieces of information in the summary! Do not cross the limit of 1500 words per summary!
        Here's the conversation <<<{text_to_be_summarized}>>>"""

    def count_tokens(self, input_text: str, encoding_name="cl100k_base"):
        """Counts the number of tokens in a given text using a specified encoding.

        Args:
            text: The input text string.
            encoding_name: The name of the encoding to use (e.g., "cl100k_base", "p50k_base", "r50k_base").
                Defaults to "cl100k_base", which is used by models like `gpt-3.5-turbo` and `gpt-4`.

        Returns:
            The number of tokens in the text, or None if an error occurs (e.g., invalid encoding name).
        """

        try:
            encoding = tiktoken.get_encoding(encoding_name)
            num_tokens = len(encoding.encode(input_text))
            return num_tokens
        except KeyError:
            print(f"Error: Invalid encoding name: {encoding_name}")
            return None
        except Exception as e: # Catching other potential exceptions
            print(f"An error occurred: {e}")
            return None

    def conversations_summarizer(self, user: list[str], llm: list[str], token_limit = 10000) -> str:
        # we have to join them like this: 
        temp = []
        for i, j in user, llm:
            temp.append(f"User : {i}\n")
            temp.append(f"DiagnAI : {j}\n")

        combined_conversation = "".join(temp)
        prompt = self.summarizing_prompt(combined_conversation)
        n_tokens = self.count_tokens(prompt)
        
        if (n_tokens < token_limit):
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(combined_conversation)
            print(response.text)
            return response

        elif (n_tokens > token_limit):
            return "Token Limit Reached! Conversation too big to summarize"


    def generate_response_gemini(self, prompt: str) -> str:
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        print(response.text)
        return response
    

### TESTING:
# Initialize the handler
handler = DataHandler()

# Load documents
chunks = handler.load_documents("/Users/varunahlawat/DiagnAI_December/DiagnAI/DataCorpus")

# Initialize vector database
handler.initialize_vector_db("TRY_DB", "OMFG")

# Perform searches
try:
    results = handler.hybrid_search("Health", top_k=1)
except Exception as e:
    print(f"Error during search: {e}")

