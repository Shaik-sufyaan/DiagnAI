import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import shutil
from typing import List

# Import your classes
from rag import VoyageEmbedding, VectorDB, RAG

class TestVoyageEmbedding:
    @pytest.fixture
    def voyage_embedding(self):
        with patch('rag.VoyageEmbeddings') as mock_embeddings:
            # Mock the embedding model's embed_query method
            mock_embeddings.return_value.embed_query.return_value = [0.1, 0.2, 0.3]
            instance = VoyageEmbedding(voyage_api_key="fake_key")
            yield instance

    @pytest.fixture
    def sample_pdf(self):
        # Create a temporary PDF file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(b"Sample PDF content")
            return tmp_file.name

    def test_document_load(self, voyage_embedding, sample_pdf):
        with patch('rag.PyPDFLoader') as mock_loader:
            # Mock the loader's load method
            mock_page = MagicMock()
            mock_page.page_content = "This is a test page content."
            mock_loader.return_value.load.return_value = [mock_page]

            chunks = voyage_embedding.document_load([sample_pdf])
            
            assert isinstance(chunks, list)
            assert len(chunks) > 0
            assert isinstance(chunks[0], str)
            mock_loader.assert_called_once_with(sample_pdf)

    def test_vectorize(self, voyage_embedding):
        test_texts = ["This is a test.", "Another test text."]
        embeddings = voyage_embedding.vectorize(test_texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == len(test_texts)
        assert all(isinstance(emb, list) for emb in embeddings)
        assert all(isinstance(val, float) for emb in embeddings for val in emb)

class TestVectorDB:
    @pytest.fixture
    def vector_db(self):
        # Create a temporary directory for ChromaDB
        temp_dir = tempfile.mkdtemp()
        db = VectorDB(persist_directory=temp_dir)
        yield db
        # Cleanup
        shutil.rmtree(temp_dir)

    def test_create_and_append_to_vector_db(self, vector_db):
        # Test both create_vector_db and append methods
        test_texts = ["Test document 1", "Test document 2"]
        test_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        
        vector_db.create_vector_db()
        vector_db.append(test_texts, test_embeddings)
        
        # Verify documents were added by performing a search
        results = vector_db.semantic_search([0.1, 0.2, 0.3], n_results=1)
        assert len(results['documents'][0]) > 0

    def test_semantic_search(self, vector_db):
        # Setup test data
        vector_db.create_vector_db()
        test_texts = ["Test document 1", "Test document 2"]
        test_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        vector_db.append(test_texts, test_embeddings)
        
        # Test search
        query_embedding = [0.1, 0.2, 0.3]
        results = vector_db.semantic_search(query_embedding, n_results=2)
        
        assert 'documents' in results
        assert 'distances' in results
        assert len(results['documents'][0]) == 2
        assert len(results['distances'][0]) == 2

class TestRAG:
    @pytest.fixture
    def rag_instance(self):
        with patch('rag.Anthropic') as mock_anthropic:
            # Mock the Anthropic client's messages.create method
            mock_message = MagicMock()
            mock_message.content = [MagicMock(text="Generated response")]
            mock_anthropic.return_value.messages.create.return_value = mock_message
            
            instance = RAG(anthropic_api_key="fake_key")
            yield instance

    def test_wrapper_prompt(self, rag_instance):
        text = "Sample text"
        emotion = "happy"
        prompt = rag_instance.wrapper_prompt(text, emotion)
        
        assert isinstance(prompt, str)
        assert text in prompt
        assert emotion in prompt
        assert "emotional tone" in prompt.lower()

    def test_final_wrapper_prompt(self, rag_instance):
        context = "Sample context"
        user_tonality = "concerned"
        query = "Sample query"
        
        prompt = rag_instance.final_wrapper_prompt(context, user_tonality, query)
        
        assert isinstance(prompt, str)
        assert context in prompt
        assert user_tonality in prompt
        assert query in prompt

    def test_generate_response(self, rag_instance):
        test_prompt = "Test prompt"
        response = rag_instance.generate_response(test_prompt)
        
        assert isinstance(response, str)
        assert len(response) > 0
        # Verify that the Anthropic client was called correctly
        rag_instance.client.messages.create.assert_called_once()
        call_args = rag_instance.client.messages.create.call_args[1]
        assert call_args['model'] == "claude-3-sonnet-20240229"
        assert call_args['max_tokens'] == 1000
        assert call_args['messages'][0]['content'] == test_prompt

if __name__ == "__main__":
    pytest.main([__file__])

