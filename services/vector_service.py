"""
Vector database service for document embeddings and semantic search
"""
import os
import uuid
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import chromadb
from chromadb.config import Settings
import openai
from openai import OpenAI

from services.base_service import BaseService
from models.document import Document, DocumentSection
from config import config

class VectorService(BaseService):
    """Service for vector database operations and semantic search"""
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.collection = None
        self.openai_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize ChromaDB and OpenAI clients"""
        try:
            # Initialize ChromaDB
            self.client = chromadb.PersistentClient(
                path=config.VECTOR_DB_PATH,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="contract_documents",
                metadata={"description": "Contract documents for semantic search"}
            )
            
            # Initialize OpenAI client
            if config.OPENAI_API_KEY:
                self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
            else:
                raise ValueError("OpenAI API key not configured")
            
            self.log_info("Vector service initialized successfully")
            
        except Exception as e:
            self.log_error(f"Failed to initialize vector service: {str(e)}")
            raise
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Create embeddings for a list of texts using OpenAI
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if not texts:
                return []
            
            # Create embeddings using OpenAI
            response = self.openai_client.embeddings.create(
                model=config.OPENAI_EMBEDDING_MODEL,
                input=texts
            )
            
            # Extract embeddings from response
            embeddings = [item.embedding for item in response.data]
            
            self.log_info(f"Created {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            self.log_error(f"Error creating embeddings: {str(e)}")
            raise
    
    def store_document_chunks(self, document: Document, chunks: List[DocumentSection]) -> Dict[str, Any]:
        """
        Store document chunks in vector database
        
        Args:
            document: Document model
            chunks: List of document sections/chunks
            
        Returns:
            Dictionary with storage result
        """
        try:
            if not chunks:
                return self.success_response(
                    data={"stored_count": 0},
                    message="No chunks to store"
                )
            
            # Prepare data for storage
            texts = [chunk.content for chunk in chunks]
            chunk_ids = [f"{document.id}_{chunk.section_id}" for chunk in chunks]
            
            # Create embeddings
            embeddings = self.create_embeddings(texts)
            
            # Prepare metadata
            metadatas = []
            for chunk in chunks:
                metadata = {
                    "document_id": document.id,
                    "document_filename": document.filename,
                    "document_type": document.file_type,
                    "chunk_id": chunk.section_id,
                    "page_number": chunk.page_number or 0,
                    "start_char": chunk.start_char or 0,
                    "end_char": chunk.end_char or 0
                }
                metadatas.append(metadata)
            
            # Store in ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=chunk_ids
            )
            
            # Update document with vector IDs
            vector_ids = chunk_ids
            
            self.log_info(f"Stored {len(chunks)} chunks for document {document.id}")
            
            return self.success_response(
                data={
                    "stored_count": len(chunks),
                    "document_id": document.id
                },
                message=f"Armazenados {len(chunks)} chunks no banco vetorial"
            )
            
        except Exception as e:
            return self.handle_error(e, "document chunk storage")
    
    def semantic_search(self, query: str, document_id: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        """
        Perform semantic search in the vector database
        
        Args:
            query: Search query
            document_id: Optional document ID to filter results
            top_k: Number of top results to return
            
        Returns:
            Dictionary with search results
        """
        try:
            # Create query embedding
            query_embedding = self.create_embeddings([query])[0]
            
            # Prepare where clause for filtering
            where_clause = None
            if document_id:
                where_clause = {"document_id": document_id}
            
            # Perform search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            search_results = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    result = {
                        "content": doc,
                        "metadata": metadata,
                        "relevance_score": 1 - distance,  # Convert distance to similarity
                        "rank": i + 1
                    }
                    search_results.append(result)
            
            self.log_info(f"Semantic search returned {len(search_results)} results")
            
            return self.success_response(
                data={
                    "query": query,
                    "results": search_results,
                    "total_results": len(search_results)
                },
                message=f"Encontrados {len(search_results)} resultados relevantes"
            )
            
        except Exception as e:
            return self.handle_error(e, "semantic search")
    
    def get_document_chunks(self, document_id: str) -> Dict[str, Any]:
        """
        Get all chunks for a specific document
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with document chunks
        """
        try:
            # Query all chunks for the document
            results = self.collection.get(
                where={"document_id": document_id},
                include=["documents", "metadatas"]
            )
            
            chunks = []
            if results["documents"]:
                for doc, metadata in zip(results["documents"], results["metadatas"]):
                    chunk = {
                        "content": doc,
                        "metadata": metadata,
                        "chunk_id": metadata.get("chunk_id"),
                        "page_number": metadata.get("page_number", 0)
                    }
                    chunks.append(chunk)
            
            # Sort by chunk_id for consistent ordering
            chunks.sort(key=lambda x: x["chunk_id"])
            
            return self.success_response(
                data={
                    "document_id": document_id,
                    "chunks": chunks,
                    "total_chunks": len(chunks)
                },
                message=f"Recuperados {len(chunks)} chunks do documento"
            )
            
        except Exception as e:
            return self.handle_error(e, "get document chunks")
    
    def delete_document_vectors(self, document_id: str) -> Dict[str, Any]:
        """
        Delete all vectors for a specific document
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with deletion result
        """
        try:
            # Get all chunk IDs for the document
            results = self.collection.get(
                where={"document_id": document_id},
                include=["metadatas"]
            )
            
            if results["ids"]:
                # Delete the chunks
                self.collection.delete(ids=results["ids"])
                deleted_count = len(results["ids"])
                
                self.log_info(f"Deleted {deleted_count} vectors for document {document_id}")
                
                return self.success_response(
                    data={"deleted_count": deleted_count},
                    message=f"Removidos {deleted_count} vetores do documento"
                )
            else:
                return self.success_response(
                    data={"deleted_count": 0},
                    message="Nenhum vetor encontrado para deletar"
                )
                
        except Exception as e:
            return self.handle_error(e, "delete document vectors")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector collection
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            # Get collection count
            count = self.collection.count()
            
            # Get sample of documents to analyze
            sample_results = self.collection.peek(limit=10)
            
            # Analyze document types
            doc_types = {}
            documents = set()
            
            if sample_results["metadatas"]:
                for metadata in sample_results["metadatas"]:
                    doc_type = metadata.get("document_type", "unknown")
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                    documents.add(metadata.get("document_id", "unknown"))
            
            stats = {
                "total_chunks": count,
                "unique_documents": len(documents),
                "document_types": doc_types,
                "collection_name": self.collection.name
            }
            
            return self.success_response(
                data=stats,
                message="Estatísticas da coleção recuperadas"
            )
            
        except Exception as e:
            return self.handle_error(e, "get collection stats")
    
    def reset_collection(self) -> Dict[str, Any]:
        """
        Reset the entire vector collection (use with caution)
        
        Returns:
            Dictionary with reset result
        """
        try:
            # Delete the collection
            self.client.delete_collection(name="contract_documents")
            
            # Recreate the collection
            self.collection = self.client.get_or_create_collection(
                name="contract_documents",
                metadata={"description": "Contract documents for semantic search"}
            )
            
            self.log_info("Vector collection reset successfully")
            
            return self.success_response(
                message="Coleção vetorial resetada com sucesso"
            )
            
        except Exception as e:
            return self.handle_error(e, "reset collection")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of vector service connections
        
        Returns:
            Dictionary with health status
        """
        try:
            health_status = {
                "chromadb_connected": False,
                "openai_connected": False,
                "collection_accessible": False,
                "total_documents": 0
            }
            
            # Check ChromaDB connection
            try:
                collections = self.client.list_collections()
                health_status["chromadb_connected"] = True
            except Exception:
                pass
            
            # Check OpenAI connection
            try:
                if self.openai_client:
                    # Try a small embedding request
                    self.create_embeddings(["test"])
                    health_status["openai_connected"] = True
            except Exception:
                pass
            
            # Check collection access
            try:
                count = self.collection.count()
                health_status["collection_accessible"] = True
                health_status["total_documents"] = count
            except Exception:
                pass
            
            # Determine overall health
            is_healthy = all([
                health_status["chromadb_connected"],
                health_status["openai_connected"],
                health_status["collection_accessible"]
            ])
            
            return self.success_response(
                data={
                    "healthy": is_healthy,
                    "details": health_status
                },
                message="Verificação de saúde concluída"
            )
            
        except Exception as e:
            return self.handle_error(e, "health check")