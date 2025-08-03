"""
Unit tests for text extraction functionality
"""
import unittest
import tempfile
import os
from pathlib import Path
from io import BytesIO

from services.text_extraction_service import TextExtractionService
from models.document import Document, FileType, DocumentStatus

class TestTextExtractionService(unittest.TestCase):
    """Test text extraction service functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.text_service = TextExtractionService()
        self.test_text = """
        CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE FIBRA ÓPTICA
        
        Contrato nº DCT-NEO165-000210
        
        CLÁUSULA 1 - DO OBJETO
        O presente contrato tem por objeto a prestação de serviços de fibra óptica.
        
        CLÁUSULA 2 - DO SLA
        O SLA de atendimento será de 4 horas para incidentes críticos.
        O prazo de 24 horas para incidentes de média prioridade.
        
        CLÁUSULA 3 - DA EXTENSÃO
        A extensão da fibra óptica será de 15,5 km.
        
        CLÁUSULA 4 - DAS PENALIDADES
        Em caso de descumprimento, será aplicada multa de R$ 5.000,00.
        
        CLÁUSULA 5 - DA VIGÊNCIA
        O contrato terá vigência de 24 meses.
        """
    
    def test_clean_text(self):
        """Test text cleaning functionality"""
        dirty_text = "  Texto   com    espaços   \n\n\n  excessivos  \n  "
        cleaned = self.text_service._clean_text(dirty_text)
        
        self.assertNotIn("   ", cleaned)  # No triple spaces
        self.assertFalse(cleaned.startswith(" "))  # No leading space
        self.assertFalse(cleaned.endswith(" "))  # No trailing space
    
    def test_create_text_chunks(self):
        """Test text chunking functionality"""
        chunks = self.text_service._create_text_chunks(self.test_text)
        
        self.assertGreater(len(chunks), 0)
        
        # Check chunk properties
        for chunk in chunks:
            self.assertIsInstance(chunk.content, str)
            self.assertIsNotNone(chunk.section_id)
            self.assertTrue(chunk.section_id.startswith("chunk_"))
    
    def test_extract_contract_specific_info(self):
        """Test contract-specific information extraction"""
        result = self.text_service.extract_contract_specific_info(self.test_text)
        
        self.assertTrue(result["success"])
        contract_info = result["data"]
        
        # Test contract number extraction
        self.assertEqual(contract_info["contract_number"], "DCT-NEO165-000210")
        
        # Test SLA extraction
        self.assertIn("4 horas", contract_info["sla_times"])
        self.assertIn("24 horas", contract_info["sla_times"])
        
        # Test fiber km extraction
        self.assertIn("15,5 km", contract_info["fiber_km"])
        
        # Test penalty extraction
        self.assertIn("R$ 5.000,00", contract_info["penalty_values"])
        
        # Test duration extraction
        self.assertIn("24 meses", contract_info["contract_duration"])
    
    def test_extract_from_txt_file(self):
        """Test text extraction from TXT file"""
        # Create temporary TXT file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(self.test_text)
            temp_path = Path(f.name)
        
        try:
            # Test extraction
            result = self.text_service.extract_text_from_file(temp_path, 'txt')
            
            self.assertTrue(result["success"])
            data = result["data"]
            
            self.assertIn("CONTRATO DE PRESTAÇÃO", data["text_content"])
            self.assertGreater(len(data["chunks"]), 0)
            self.assertEqual(data["metadata"]["format"], "txt")
            self.assertGreater(data["stats"]["total_chars"], 0)
            
        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()
    
    def test_extract_from_nonexistent_file(self):
        """Test extraction from non-existent file"""
        fake_path = Path("nonexistent_file.txt")
        result = self.text_service.extract_text_from_file(fake_path, 'txt')
        
        self.assertFalse(result["success"])
        self.assertIn("não encontrado", result["error"])
    
    def test_extract_from_unsupported_format(self):
        """Test extraction from unsupported file format"""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            result = self.text_service.extract_text_from_file(temp_path, 'xyz')
            
            self.assertFalse(result["success"])
            self.assertIn("não suportado", result["error"])
            
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_process_document(self):
        """Test complete document processing"""
        # Create test document
        document = Document(
            filename="test_contract.txt",
            file_type=FileType.TXT,
            file_size=len(self.test_text.encode()),
            status=DocumentStatus.UPLOADED
        )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(self.test_text)
            temp_path = Path(f.name)
        
        try:
            # Process document
            result = self.text_service.process_document(document, temp_path)
            
            self.assertTrue(result["success"])
            processed_doc = result["data"]
            
            self.assertEqual(processed_doc["id"], document.id)
            self.assertEqual(processed_doc["status"], DocumentStatus.READY)
            self.assertIn("text_content", processed_doc)
            self.assertIn("chunks", processed_doc)
            self.assertIn("metadata", processed_doc)
            self.assertIn("stats", processed_doc)
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

class TestContractInfoExtraction(unittest.TestCase):
    """Test contract information extraction patterns"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.text_service = TextExtractionService()
    
    def test_contract_number_patterns(self):
        """Test different contract number patterns"""
        test_cases = [
            ("Contrato nº DCT-NEO165-000210", "DCT-NEO165-000210"),
            ("CONTRATO DCT-ABC123-456789", "DCT-ABC123-456789"),
            ("Contrato n° XYZ-123/456", "XYZ-123/456"),
            ("N° ABC-DEF-123456", "ABC-DEF-123456")
        ]
        
        for text, expected in test_cases:
            with self.subTest(text=text):
                result = self.text_service.extract_contract_specific_info(text)
                self.assertEqual(result["data"]["contract_number"], expected)
    
    def test_sla_patterns(self):
        """Test SLA time extraction patterns"""
        test_cases = [
            "SLA de 4 horas",
            "prazo de 24 horas", 
            "atendimento em 2 dias",
            "SLA de 30 minutos"
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                result = self.text_service.extract_contract_specific_info(text)
                self.assertGreater(len(result["data"]["sla_times"]), 0)
    
    def test_fiber_km_patterns(self):
        """Test fiber km extraction patterns"""
        test_cases = [
            "15,5 km de fibra",
            "fibra óptica de 20 km",
            "extensão de 10,2 km"
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                result = self.text_service.extract_contract_specific_info(text)
                self.assertGreater(len(result["data"]["fiber_km"]), 0)
    
    def test_penalty_patterns(self):
        """Test penalty value extraction patterns"""
        test_cases = [
            "multa de R$ 5.000,00",
            "penalidade de R$ 10.500,50",
            "valor da multa: R$ 1.000,00"
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                result = self.text_service.extract_contract_specific_info(text)
                self.assertGreater(len(result["data"]["penalty_values"]), 0)
    
    def test_duration_patterns(self):
        """Test contract duration extraction patterns"""
        test_cases = [
            "vigência de 24 meses",
            "prazo de 2 anos",
            "duração de 36 meses"
        ]
        
        for text in test_cases:
            with self.subTest(text=text):
                result = self.text_service.extract_contract_specific_info(text)
                self.assertGreater(len(result["data"]["contract_duration"]), 0)

if __name__ == '__main__':
    unittest.main()