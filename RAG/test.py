import os
from typing import List, Dict, Any
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from anthropic import Anthropic
import numpy as np

# Append Stats Imports:
import logging
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime

class RAGPipeline:
    def __init__(self, pdf_directory: str, anthropic_api_key: str):
        """
        Initialize the RAG pipeline with necessary components.

        Args:
            pdf_directory: Directory containing PDF files
            anthropic_api_key: API key for Anthropic's Claude
        """
        self.pdf_directory = pdf_directory
        self.anthropic_client = Anthropic(api_key=anthropic_api_key)
        # Using a popular, publicly available embedding model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.db = None

    def load_documents(self) -> List[Dict[str, Any]]:
        """
        Load and process PDF documents from the specified directory.
        """
        documents = []
        # Traverse two levels of nesting in the folders
        for foldername in os.listdir(self.pdf_directory): 
            folder_path = os.path.join(self.pdf_directory, foldername)
            if os.path.isdir(folder_path):  # Check if it's a directory
                for filename in os.listdir(folder_path):
                    if filename.endswith('.pdf'):
                        file_path = os.path.join(folder_path, filename)
                        loader = PyPDFLoader(file_path)
                        documents.extend(loader.load())

        # Split documents into smaller chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        split_docs = text_splitter.split_documents(documents)
        return split_docs
    
    def create_vector_database(self, documents: List[Dict[str, Any]]):
        """
        Create and populate the vector database using ChromaDB.
        """
        self.db = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory="./chroma_db"
        )
        self.db.persist()
        
    def semantic_search(self, query: str, k: int = 3) -> List[str]:
        """
        Perform semantic search on the vector database.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant document chunks
        """
        if not self.db:
            raise ValueError("Vector database not initialized. Run create_vector_database first.")
            
        results = self.db.similarity_search(query, k=k)
        return [doc.page_content for doc in results]
    
    def final_wrapper_prompt(self, query: str, context: List[str], tonality: str) -> str:
        """
        Generate a wrapper prompt that includes context and desired tonality.
        
        Args:
            query: User query
            context: Retrieved context from semantic search
            tonality: Desired emotional tonality for the response
        """
        prompt = f"""Based on the following context, answer my query:

                Context:
                {'-' * 80}
                {' '.join(context)}
                {'-' * 80}

                Query: {query}

                The user said {tonality} tone. [Each sentence in your response will have the tonality clearly mentioned, to deliver appropriate emotional expression while replying back to the human.]
                """
        return prompt
    
    def generate_response(self, prompt: str) -> str:
        """
        Generate a response using Claude with the specified prompt.
        """
        message = self.anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        return message.content[0].text
    
    def process_query(self, query: str, tonality: str) -> str:
        """
        Process a query through the entire pipeline.
        
        Args:
            query: User query
            tonality: Desired emotional tonality for the response
            
        Returns:
            Generated response with specified tonality
        """
        # Perform semantic search
        relevant_contexts = self.semantic_search(query)
        
        # Generate wrapper prompt
        prompt = self.final_wrapper_prompt(query, relevant_contexts, tonality)
        
        # Generate response
        response = self.generate_response(prompt)
        
        return response
    
####################### Append Stats ##########################
@dataclass
class AppendStats:
    """Statistics for document append operation"""
    total_pdfs: int
    processed_pdfs: int
    total_chunks: int
    start_time: datetime
    end_time: datetime = None
    
    @property
    def duration(self):
        """Calculate duration of operation"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def to_dict(self):
        return {
            "total_pdfs": self.total_pdfs,
            "processed_pdfs": self.processed_pdfs,
            "total_chunks": self.total_chunks,
            "duration_seconds": self.duration,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }

def setup_logger():
    """Configure logging for the RAG pipeline"""
    logger = logging.getLogger('RAGPipeline')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('rag_pipeline.log')
    
    # Create formatters and add it to handlers
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    c_format = logging.Formatter(log_format)
    f_format = logging.Formatter(log_format)
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)
    
    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    
    return logger

def append_documents(self, new_pdf_paths: List[str], batch_size: int = 10) -> AppendStats:
    """
    Append new PDF documents to an existing vector database with progress tracking.
    
    Args:
        new_pdf_paths: List of file paths to new PDF documents to be added
        batch_size: Number of documents to process in each batch
        
    Returns:
        AppendStats: Statistics about the append operation
        
    Raises:
        ValueError: If the vector database hasn't been initialized
        FileNotFoundError: If any of the specified PDF files don't exist
    """
    logger = setup_logger()
    
    if not self.db:
        raise ValueError("Vector database not initialized. Run create_vector_database first.")
    
    stats = AppendStats(
        total_pdfs=len(new_pdf_paths),
        processed_pdfs=0,
        total_chunks=0,
        start_time=datetime.now()
    )
    
    try:
        # Verify all files exist before processing
        logger.info(f"Verifying {len(new_pdf_paths)} PDF files...")
        for pdf_path in new_pdf_paths:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Process documents in batches
        batches = [new_pdf_paths[i:i + batch_size] 
                  for i in range(0, len(new_pdf_paths), batch_size)]
        
        logger.info(f"Starting document processing in {len(batches)} batches")
        
        for batch_num, batch in enumerate(batches, 1):
            new_documents = []
            
            # Process PDFs in current batch with progress bar
            with tqdm(total=len(batch), 
                     desc=f"Batch {batch_num}/{len(batches)}", 
                     unit="pdf") as pbar:
                
                def process_pdf(pdf_path):
                    try:
                        loader = PyPDFLoader(pdf_path)
                        docs = loader.load()
                        pbar.update(1)
                        logger.debug(f"Processed {pdf_path}")
                        return docs
                    except Exception as e:
                        logger.error(f"Error processing {pdf_path}: {str(e)}")
                        return []
                
                # Process PDFs in parallel
                with ThreadPoolExecutor() as executor:
                    results = list(executor.map(process_pdf, batch))
                    for docs in results:
                        new_documents.extend(docs)
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            split_docs = text_splitter.split_documents(new_documents)
            
            # Update statistics
            stats.processed_pdfs += len(batch)
            stats.total_chunks += len(split_docs)
            
            # Add chunks to database with progress bar
            with tqdm(total=len(split_docs), 
                     desc=f"Adding chunks (Batch {batch_num})", 
                     unit="chunk") as pbar:
                
                # Add documents in smaller sub-batches to show progress
                chunk_batch_size = 50
                for i in range(0, len(split_docs), chunk_batch_size):
                    chunk_batch = split_docs[i:i + chunk_batch_size]
                    self.db.add_documents(chunk_batch)
                    pbar.update(len(chunk_batch))
            
            # Persist after each batch
            self.db.persist()
            logger.info(f"Completed batch {batch_num}/{len(batches)}")
            
        # Record completion
        stats.end_time = datetime.now()
        
        # Log final statistics
        logger.info(
            f"Append operation completed:\n"
            f"- Processed {stats.processed_pdfs}/{stats.total_pdfs} PDFs\n"
            f"- Added {stats.total_chunks} chunks\n"
            f"- Duration: {stats.duration:.2f} seconds"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error appending documents: {str(e)}")
        stats.end_time = datetime.now()
        raise
############################################################ 
def get_database_stats(self) -> Dict[str, Any]:
    """
    Get current statistics about the vector database.
    """
    if not self.db:
        raise ValueError("Vector database not initialized")
        
    return {
        "total_documents": len(self.db.get()),
        "embedding_dimensions": len(self.db.get()[0][1]) if len(self.db.get()) > 0 else 0,
    }

def test_append_documents_with_progress():
    """
    Test function to verify the append functionality with progress tracking.
    """
    import tempfile
    from reportlab.pdfgen import canvas
    
    try:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test PDF files
            test_pdfs = []
            for i in range(5):  # Create more test files to demonstrate progress
                pdf_path = os.path.join(temp_dir, f"test_{i}.pdf")
                c = canvas.Canvas(pdf_path)
                c.drawString(100, 750, f"This is test document {i}")
                c.save()
                test_pdfs.append(pdf_path)
            
            # Initialize pipeline
            pipeline = RAGPipeline(
                pdf_directory="./data/pdfs",
                anthropic_api_key="your_api_key_here"
            )
            
            # Create initial database
            documents = pipeline.load_documents()
            pipeline.create_vector_database(documents)
            
            # Get initial stats
            initial_stats = pipeline.get_database_stats()
            
            # Append new documents with progress tracking
            append_stats = pipeline.append_documents(test_pdfs, batch_size=2)
            
            # Get final stats
            final_stats = pipeline.get_database_stats()
            
            # Verify results
            assert final_stats["total_documents"] > initial_stats["total_documents"]
            assert append_stats.processed_pdfs == len(test_pdfs)
            
            print("Progress-tracked append test passed successfully!")
            return True
            
    except Exception as e:
        print(f"Error during append test: {str(e)}")
        return False
    


def test_pipeline():
    """
    Test function to verify the pipeline works correctly.
    """
    try:
        # Initialize pipeline
        pipeline = RAGPipeline(
            pdf_directory="./data/pdfs",
            anthropic_api_key="your_api_key_here"
        )
        print("Pipeline initialized successfully")
        
        # Test document loading
        if not os.path.exists("./data/pdfs"):
            os.makedirs("./data/pdfs")
            print("Created PDF directory")
        
        # Add a test for embedding model
        test_text = ["This is a test sentence."]
        embeddings = pipeline.embeddings.embed_documents(test_text)
        print(f"Successfully generated embeddings of shape: {len(embeddings[0])}")
        
        print("All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        return False

if __name__ == "__main__":
    test_pipeline()

