"""
Unit tests for vector service functionality
"""
import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

from services.vector_service import VectorService
from models.document import Document, DocumentSection, FileType, DocumentStatus

class TestVectorService(unittest.TestCase):
    """Test vector service functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the config to avoid requiring actual API keys for tests
        with patch('services.vector_service.config') as mock_config:
            mock_config.VECTOR_DB_PATH = "./test_chroma_db"
            mock_config.OPENAI_API_KEY = "test_key"
            mock_config.OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
            
            # Mock OpenAI client
            with patch('services.vector_service.OpenAI') as mock_openai:
                mock_client = Mock()
                mock_openai.return_value = mock_client
                
                # Mock embeddings response
                mock_response = Mock()
                mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3]) for _ in range(3)]
                mock_client.embeddings.create.return_value = mock_response
                
                # Mock ChromaDB
                with patch('services.vector_service.chromadb') as mock_chromadb:
                    mock_chroma_client = Mock()
                    mock_collection = Mock()
                    mock_chroma_client.get_or_create_collection.return_value = mock_collection
                    mock_chromadb.PersistentClient.return_value = mock_chroma_client
                    
                    self.vector_service = VectorService()
                    self.mock_collection = mock_collection
                    self.mock_openai_client = mock_client
        
        # Test data
        self.test_document = Document(
            filename="test_contract.pdf",
            file_type=FileType.PDF,
            file_size=1024,
            status=DocumentStatus.READY
        )
        
        self.test_chunks = [
            DocumentSection(
                content="This is the first chunk of the contract",
                section_id="chunk_1",
                page_number=1
            ),
            DocumentSection(
                content="This is the second chunk with SLA information",
                section_id="chunk_2", 
                page_number=1
            ),
            DocumentSection(
                content="This chunk contains penalty and fine details",
                section_id="chunk_3",
                page_number=2
            )
        ]
    
    def test_create_embeddings(self):
        """Test embedding creation"""
        texts = ["test text 1", "test text 2"]
        
        embeddings = self.vector_service.create_embeddings(texts)
        
        self.assertEqual(len(embeddings), 2)
        self.assertEqual(len(embeddings[0]), 3)  # Mock embedding dimension
        self.mock_openai_client.embeddings.create.assert_called_once()
    
    def test_create_embeddings_empty_list(self):
        """Test embedding creation with empty list"""
        embeddings = self.vector_service.create_embeddings([])
        
        self.assertEqual(embeddings, [])
        self.mock_openai_client.embeddings.create.assert_not_called()
    
    def test_store_document_chunks(self):
        """Test storing document chunks in vector database"""
        result = self.vector_service.store_document_chunks(self.test_document, self.test_chunks)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["stored_count"], 3)
        self.assertEqual(len(result["data"]["vector_ids"]), 3)
        
        # Verify ChromaDB add was called
        self.mock_collection.add.assert_called_once()
        
        # Check the call arguments
        call_args = self.mock_collection.add.call_args
        self.assertEqual(len(call_args.kwargs["documents"]), 3)
        self.assertEqual(len(call_args.kwargs["embeddings"]), 3)
        self.assertEqual(len(call_args.kwargs["metadatas"]), 3)
        self.assertEqual(len(call_args.kwargs["ids"]), 3)
    
    def test_store_document_chunks_empty(self):
        """Test storing empty chunks list"""
        result = self.vector_service.store_document_chunks(self.test_document, [])
        
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["stored_count"], 0)
        self.mock_collection.add.assert_not_called()
    
    def test_semantic_search(self):
        """Test semantic search functionality"""
        # Mock search results
        mock_results = {
            "documents": [["First result", "Second result"]],
            "metadatas": [[{"document_id": "doc1", "chunk_id": "chunk_1"}, 
                          {"document_id": "doc1", "chunk_id": "chunk_2"}]],
            "distances": [[0.2, 0.4]]
        }
        self.mock_collection.query.return_value = mock_results
        
        result = self.vector_service.semantic_search("test query", top_k=2)
        
        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]["results"]), 2)
        self.assertEqual(result["data"]["results"][0]["content"], "First result")
        self.assertEqual(result["data"]["results"][0]["relevance_score"], 0.8)  # 1 - 0.2
        
        # Verify query was called
        self.mock_collection.query.assert_called_once()
    
    def test_semantic_search_with_document_filter(self):
        """Test semantic search with document ID filter"""
        mock_results = {
            "documents": [["Filtered result"]],
            "metadatas": [[{"document_id": "specific_doc", "chunk_id": "chunk_1"}]],
            "distances": [[0.1]]
        }
        self.mock_collection.query.return_value = mock_results
        
        result = self.vector_service.semantic_search("test query", document_id="specific_doc")
        
        self.assertTrue(result["success"])
        
        # Check that where clause was used
        call_args = self.mock_collection.query.call_args
        self.assertEqual(call_args.kwargs["where"], {"document_id": "specific_doc"})
    
    def test_semantic_search_no_results(self):
        """Test semantic search with no results"""
        mock_results = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }
        self.mock_collection.query.return_value = mock_results
        
        result = self.vector_service.semantic_search("test query")
        
        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]["results"]), 0)
    
    def test_get_document_chunks(self):
        """Test retrieving document chunks"""
        mock_results = {
            "documents": ["Chunk 1 content", "Chunk 2 content"],
            "metadatas": [
                {"document_id": "doc1", "chunk_id": "chunk_1", "page_number": 1},
                {"document_id": "doc1", "chunk_id": "chunk_2", "page_number": 2}
            ]
        }
        self.mock_collection.get.return_value = mock_results
        
        result = self.vector_service.get_document_chunks("doc1")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["total_chunks"], 2)
        self.assertEqual(result["data"]["chunks"][0]["content"], "Chunk 1 content")
        
        # Verify get was called with correct filter
        self.mock_collection.get.assert_called_once()
        call_args = self.mock_collection.get.call_args
        self.assertEqual(call_args.kwargs["where"], {"document_id": "doc1"})
    
    def test_delete_document_vectors(self):
        """Test deleting document vectors"""
        mock_results = {
            "ids": ["doc1_chunk_1", "doc1_chunk_2", "doc1_chunk_3"]
        }
        self.mock_collection.get.return_value = mock_results
        
        result = self.vector_service.delete_document_vectors("doc1")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["deleted_count"], 3)
        
        # Verify delete was called
        self.mock_collection.delete.assert_called_once_with(ids=mock_results["ids"])
    
    def test_delete_document_vectors_not_found(self):
        """Test deleting vectors for non-existent document"""
        mock_results = {"ids": []}
        self.mock_collection.get.return_value = mock_results
        
        result = self.vector_service.delete_document_vectors("nonexistent_doc")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["deleted_count"], 0)
        self.mock_collection.delete.assert_not_called()
    
    def test_get_collection_stats(self):
        """Test getting collection statistics"""
        self.mock_collection.count.return_value = 10
        
        mock_peek_results = {
            "metadatas": [
                {"document_type": "pdf", "document_id": "doc1"},
                {"document_type": "docx", "document_id": "doc2"},
                {"document_type": "pdf", "document_id": "doc1"}
            ]
        }
        self.mock_collection.peek.return_value = mock_peek_results
        
        result = self.vector_service.get_collection_stats()
        
        self.assertTrue(result["success"])
        stats = result["data"]
        self.assertEqual(stats["total_chunks"], 10)
        self.assertEqual(stats["unique_documents"], 2)
        self.assertEqual(stats["document_types"]["pdf"], 2)
        self.assertEqual(stats["document_types"]["docx"], 1)
    
    def test_health_check(self):
        """Test health check functionality"""
        # Mock successful connections
        self.vector_service.client.list_collections.return_value = []
        self.mock_collection.count.return_value = 5
        
        result = self.vector_service.health_check()
        
        self.assertTrue(result["success"])
        health_data = result["data"]
        self.assertTrue(health_data["healthy"])
        self.assertTrue(health_data["details"]["chromadb_connected"])
        self.assertTrue(health_data["details"]["openai_connected"])
        self.assertTrue(health_data["details"]["collection_accessible"])
        self.assertEqual(health_data["details"]["total_documents"], 5)

class TestVectorServiceIntegration(unittest.TestCase):
    """Integration tests for vector service (requires actual services)"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        # Skip integration tests if no API key is available
        if not os.getenv("OPENAI_API_KEY"):
            self.skipTest("OpenAI API key not available for integration tests")
        
        # Use temporary directory for test database
        self.temp_dir = tempfile.mkdtemp()
        
        # Patch config for integration tests
        with patch('services.vector_service.config') as mock_config:
            mock_config.VECTOR_DB_PATH = self.temp_dir
            mock_config.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
            mock_config.OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
            
            try:
                self.vector_service = VectorService()
            except Exception as e:
                self.skipTest(f"Failed to initialize vector service: {e}")
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        # Clean up temporary directory
        import shutil
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        # Create test document and chunks
        document = Document(
            filename="integration_test.pdf",
            file_type=FileType.PDF,
            file_size=2048,
            status=DocumentStatus.READY
        )
        
        chunks = [
            DocumentSection(
                content="This contract defines SLA requirements of 4 hours response time",
                section_id="chunk_1"
            ),
            DocumentSection(
                content="The fiber optic network spans 25 kilometers in total length",
                section_id="chunk_2"
            )
        ]
        
        # Store chunks
        store_result = self.vector_service.store_document_chunks(document, chunks)
        self.assertTrue(store_result["success"])
        
        # Search for SLA information
        search_result = self.vector_service.semantic_search("SLA response time requirements")
        self.assertTrue(search_result["success"])
        self.assertGreater(len(search_result["data"]["results"]), 0)
        
        # Verify the most relevant result contains SLA information
        top_result = search_result["data"]["results"][0]
        self.assertIn("SLA", top_result["content"])
        
        # Clean up
        delete_result = self.vector_service.delete_document_vectors(document.id)
        self.assertTrue(delete_result["success"])

if __name__ == '__main__':
    unittest.main()