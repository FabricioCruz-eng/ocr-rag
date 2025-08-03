"""
Document data models for contract analysis
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"

class FileType(str, Enum):
    """Supported file types"""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"

class Document(BaseModel):
    """Document model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(default="default_user")
    filename: str
    file_type: FileType
    file_size: int
    uploaded_at: datetime = Field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    status: DocumentStatus = DocumentStatus.UPLOADED
    text_content: Optional[str] = None
    
    class Config:
        use_enum_values = True

class DocumentSection(BaseModel):
    """Document section with location information"""
    content: str
    page_number: Optional[int] = None
    section_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    relevance_score: Optional[float] = None

class QueryResponse(BaseModel):
    """Query response model"""
    question: str
    answer: str
    sources: List[DocumentSection] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence_score: Optional[float] = None

class QuerySession(BaseModel):
    """Query session model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(default="default_user")
    document_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    queries: List[QueryResponse] = Field(default_factory=list)
    
    def add_query(self, query_response: QueryResponse):
        """Add a query response to the session"""
        self.queries.append(query_response)