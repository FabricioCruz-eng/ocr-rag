"""
Contract analysis data models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class ClauseType(str, Enum):
    """Types of contract clauses"""
    SLA = "sla"
    FIBRA_OPTICA = "fibra_optica"
    MULTA = "multa"
    PRAZO_CONTRATO = "prazo_contrato"
    TERMINATION = "termination"
    PAYMENT = "payment"
    LIABILITY = "liability"
    CONFIDENTIALITY = "confidentiality"
    OTHER = "other"

class RiskLevel(str, Enum):
    """Risk levels for contract clauses"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class DocumentLocation(BaseModel):
    """Location information within document"""
    page_number: Optional[int] = None
    section: Optional[str] = None
    paragraph: Optional[int] = None
    start_char: Optional[int] = None
    end_char: Optional[int] = None

class ContractClause(BaseModel):
    """Contract clause model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ClauseType
    content: str
    location: DocumentLocation
    summary: str
    risk_level: RiskLevel = RiskLevel.LOW
    key_terms: Dict[str, Any] = Field(default_factory=dict)
    
    # Specific fields for operator contracts
    sla_time: Optional[str] = None
    fiber_km: Optional[str] = None
    penalty_value: Optional[str] = None
    contract_duration: Optional[str] = None
    
    class Config:
        use_enum_values = True

class RiskFlag(BaseModel):
    """Risk flag for contract analysis"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    description: str
    severity: RiskLevel
    location: Optional[DocumentLocation] = None
    recommendation: Optional[str] = None

class ContractAnalysis(BaseModel):
    """Complete contract analysis model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    analyzed_at: datetime = Field(default_factory=datetime.now)
    identified_clauses: List[ContractClause] = Field(default_factory=list)
    missing_clauses: List[str] = Field(default_factory=list)
    risk_flags: List[RiskFlag] = Field(default_factory=list)
    
    # Summary metrics
    total_clauses: int = 0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    
    def calculate_metrics(self):
        """Calculate analysis metrics"""
        self.total_clauses = len(self.identified_clauses)
        self.high_risk_count = len([c for c in self.identified_clauses if c.risk_level == RiskLevel.HIGH])
        self.medium_risk_count = len([c for c in self.identified_clauses if c.risk_level == RiskLevel.MEDIUM])
        self.low_risk_count = len([c for c in self.identified_clauses if c.risk_level == RiskLevel.LOW])
    
    def add_clause(self, clause: ContractClause):
        """Add a clause to the analysis"""
        self.identified_clauses.append(clause)
        self.calculate_metrics()
    
    def add_risk_flag(self, risk_flag: RiskFlag):
        """Add a risk flag to the analysis"""
        self.risk_flags.append(risk_flag)