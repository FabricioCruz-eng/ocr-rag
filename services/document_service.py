"""
Document service for file upload, validation and storage
"""
import os
import shutil
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from datetime import datetime

from services.base_service import BaseService
from services.text_extraction_service import TextExtractionService
from services.vector_service import VectorService
from services.query_service import QueryService
from models.document import Document, DocumentStatus, FileType
from utils.file_utils import (
    validate_file_type, validate_file_size, get_file_hash,
    ensure_upload_directory, generate_safe_filename, get_file_info
)
from config import config

class DocumentService(BaseService):
    """Service for document management"""
    
    def __init__(self):
        super().__init__()
        self.upload_path = ensure_upload_directory()
        self.text_extraction_service = TextExtractionService()
        self.vector_service = VectorService()
        self.query_service = QueryService()
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validate uploaded file
        
        Args:
            filename: Original filename
            file_size: File size in bytes
            
        Returns:
            Tuple of (is_valid, error_message, file_info)
        """
        try:
            return get_file_info(filename, file_size)
        except Exception as e:
            return False, f"Erro na validação do arquivo: {str(e)}", {}
    
    def upload_document(self, file_content: bytes, filename: str, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Upload and store document
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            user_id: User identifier
            
        Returns:
            Dictionary with upload result
        """
        try:
            # Validate file
            file_size = len(file_content)
            is_valid, error_msg, file_info = self.validate_file(filename, file_size)
            
            if not is_valid:
                self.log_error(f"File validation failed: {error_msg}")
                return self.handle_error(Exception(error_msg), "file validation")
            
            # Generate file hash and safe filename
            file_hash = get_file_hash(file_content)
            safe_filename = generate_safe_filename(filename, file_hash)
            
            # Create document model
            document = Document(
                user_id=user_id,
                filename=filename,
                file_type=FileType(file_info["extension"]),
                file_size=file_size,
                status=DocumentStatus.UPLOADED
            )
            
            # Save file to disk
            file_path = self.upload_path / safe_filename
            
            # Check if file already exists (duplicate detection)
            if file_path.exists():
                self.log_warning(f"File already exists: {safe_filename}")
                # Load existing document info if available
                existing_doc = self._find_existing_document(file_hash)
                if existing_doc:
                    return self.success_response(
                        data=existing_doc.model_dump(),
                        message="Arquivo já existe no sistema"
                    )
            
            # Write file to disk
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            self.log_info(f"Document uploaded successfully: {document.id}")
            
            return self.success_response(
                data={
                    "document": document.model_dump(),
                    "file_path": str(file_path),
                    "file_hash": file_hash,
                    "safe_filename": safe_filename
                },
                message="Arquivo enviado com sucesso"
            )
            
        except Exception as e:
            return self.handle_error(e, "document upload")
    
    def get_document_path(self, document_id: str, filename: str) -> Optional[Path]:
        """
        Get the file path for a document
        
        Args:
            document_id: Document ID
            filename: Safe filename
            
        Returns:
            Path object or None if not found
        """
        try:
            # Look for files that contain the document_id or match the filename pattern
            for file_path in self.upload_path.glob("*"):
                if document_id[:8] in file_path.name or filename in file_path.name:
                    return file_path
            return None
        except Exception as e:
            self.log_error(f"Error finding document path: {str(e)}")
            return None
    
    def delete_document(self, document_id: str, filename: str) -> Dict[str, Any]:
        """
        Delete document file from storage
        
        Args:
            document_id: Document ID
            filename: Safe filename
            
        Returns:
            Dictionary with deletion result
        """
        try:
            file_path = self.get_document_path(document_id, filename)
            
            if not file_path or not file_path.exists():
                return self.handle_error(
                    Exception("Arquivo não encontrado"),
                    "document deletion"
                )
            
            # Delete file
            file_path.unlink()
            
            self.log_info(f"Document deleted successfully: {document_id}")
            return self.success_response(message="Arquivo deletado com sucesso")
            
        except Exception as e:
            return self.handle_error(e, "document deletion")
    
    def get_document_info(self, document_id: str) -> Dict[str, Any]:
        """
        Get document information
        
        Args:
            document_id: Document ID
            
        Returns:
            Dictionary with document info
        """
        try:
            # This would typically query a database
            # For now, we'll return basic info
            return self.success_response(
                data={"document_id": document_id, "status": "info_placeholder"},
                message="Informações do documento"
            )
        except Exception as e:
            return self.handle_error(e, "get document info")
    
    def _find_existing_document(self, file_hash: str) -> Optional[Document]:
        """
        Find existing document by file hash
        
        Args:
            file_hash: File hash to search for
            
        Returns:
            Document object if found, None otherwise
        """
        # This would typically query a database
        # For now, return None (no duplicates found)
        return None
    
    def list_documents(self, user_id: str = "default_user") -> Dict[str, Any]:
        """
        List all documents for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with list of documents
        """
        try:
            # Get all files in upload directory
            files = []
            for file_path in self.upload_path.glob("*"):
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "filename": file_path.name,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "path": str(file_path)
                    })
            
            return self.success_response(
                data={"files": files, "count": len(files)},
                message=f"Encontrados {len(files)} arquivos"
            )
            
        except Exception as e:
            return self.handle_error(e, "list documents")
    
    def process_document_text(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process document to extract text content
        
        Args:
            document_data: Document data from upload
            
        Returns:
            Dictionary with processing result including extracted text
        """
        try:
            # Get document info
            document = Document(**document_data["document"])
            file_path = Path(document_data["file_path"])
            
            # Update document status to processing
            document.status = DocumentStatus.PROCESSING
            
            # Extract text using text extraction service
            processing_result = self.text_extraction_service.process_document(document, file_path)
            
            if not processing_result["success"]:
                return processing_result
            
            # Get processed data
            processed_data = processing_result["data"]
            
            # Extract contract-specific information
            contract_info_result = self.text_extraction_service.extract_contract_specific_info(
                processed_data["text_content"]
            )
            
            # Combine all results
            final_result = {
                "document": processed_data,
                "contract_info": contract_info_result["data"] if contract_info_result["success"] else {},
                "processing_stats": processed_data["stats"]
            }
            
            self.log_info(f"Document text processing completed: {document.id}")
            
            return self.success_response(
                data=final_result,
                message="Texto extraído e processado com sucesso"
            )
            
        except Exception as e:
            return self.handle_error(e, "document text processing")
    
    def process_document_complete(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete document processing: text extraction + vectorization
        
        Args:
            document_data: Document data from upload
            
        Returns:
            Dictionary with complete processing result
        """
        try:
            # First, process text extraction
            text_result = self.process_document_text(document_data)
            
            if not text_result["success"]:
                return text_result
            
            # Get document and chunks for vectorization
            document_dict = text_result["data"]["document"]
            
            # Create Document object with original data from upload
            original_doc_data = document_data["document"].copy()
            
            # Remove any problematic vector_ids field
            if "vector_ids" in original_doc_data:
                del original_doc_data["vector_ids"]
            
            original_document = Document(**original_doc_data)
            
            # Update with processed data
            original_document.status = DocumentStatus.READY
            original_document.text_content = document_dict.get("text_content", "")
            
            chunks_data = document_dict["chunks"]
            
            # Convert chunks data back to DocumentSection objects
            from models.document import DocumentSection
            chunks = [DocumentSection(**chunk_data) for chunk_data in chunks_data]
            
            # Store vectors in ChromaDB
            vector_result = self.vector_service.store_document_chunks(original_document, chunks)
            
            if not vector_result["success"]:
                self.log_warning(f"Vector storage failed: {vector_result['error']}")
                vector_info = {"vectors_stored": False, "error": vector_result["error"]}
            else:
                vector_info = {
                    "vectors_stored": True,
                    "chunks_vectorized": vector_result["data"]["stored_count"]
                }
            
            # Combine all results
            complete_result = {
                "document": text_result["data"]["document"],
                "contract_info": text_result["data"]["contract_info"],
                "processing_stats": text_result["data"]["processing_stats"],
                "vector_info": vector_info
            }
            
            self.log_info(f"Complete document processing finished: {original_document.id}")
            
            return self.success_response(
                data=complete_result,
                message="Documento processado e vetorizado com sucesso"
            )
            
        except Exception as e:
            return self.handle_error(e, "complete document processing")
    
    def search_document(self, document_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Search within a specific document using semantic search
        
        Args:
            document_id: Document ID to search within
            query: Search query
            top_k: Number of results to return
            
        Returns:
            Dictionary with search results
        """
        try:
            return self.vector_service.semantic_search(
                query=query,
                document_id=document_id,
                top_k=top_k
            )
        except Exception as e:
            return self.handle_error(e, "document search")
    
    def query_document(self, document_id: str, question: str, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Process a natural language query about a document using RAG
        
        Args:
            document_id: Document ID to query
            question: User's natural language question
            user_id: User identifier
            
        Returns:
            Dictionary with RAG response
        """
        try:
            return self.query_service.process_query(
                question=question,
                document_id=document_id,
                user_id=user_id
            )
        except Exception as e:
            return self.handle_error(e, "document query")
    
    def get_query_suggestions(self, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get suggested queries for a document
        
        Args:
            document_id: Optional document ID
            
        Returns:
            Dictionary with query suggestions
        """
        try:
            return self.query_service.get_query_suggestions(document_id)
        except Exception as e:
            return self.handle_error(e, "query suggestions")
    
    def analyze_query_intent(self, question: str) -> Dict[str, Any]:
        """
        Analyze the intent of a user query
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with intent analysis
        """
        try:
            return self.query_service.analyze_query_intent(question)
        except Exception as e:
            return self.handle_error(e, "query intent analysis")