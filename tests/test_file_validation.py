"""
Unit tests for file validation functionality
"""
import unittest
import tempfile
import os
from pathlib import Path

from utils.file_utils import (
    validate_file_type, validate_file_size, get_file_hash,
    generate_safe_filename, get_file_info
)
from services.document_service import DocumentService

class TestFileValidation(unittest.TestCase):
    """Test file validation functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.document_service = DocumentService()
        self.test_content = b"Test file content for validation"
    
    def test_validate_file_type_valid(self):
        """Test valid file types"""
        valid_files = [
            "contract.pdf",
            "document.docx", 
            "text.txt",
            "CONTRACT.PDF",  # Test case insensitive
            "Document.DOCX"
        ]
        
        for filename in valid_files:
            with self.subTest(filename=filename):
                self.assertTrue(validate_file_type(filename))
    
    def test_validate_file_type_invalid(self):
        """Test invalid file types"""
        invalid_files = [
            "image.jpg",
            "spreadsheet.xlsx",
            "presentation.pptx",
            "archive.zip",
            "executable.exe",
            "no_extension"
        ]
        
        for filename in invalid_files:
            with self.subTest(filename=filename):
                self.assertFalse(validate_file_type(filename))
    
    def test_validate_file_size_valid(self):
        """Test valid file sizes"""
        valid_sizes = [
            1024,  # 1KB
            1024 * 1024,  # 1MB
            10 * 1024 * 1024,  # 10MB
            49 * 1024 * 1024,  # 49MB (under limit)
        ]
        
        for size in valid_sizes:
            with self.subTest(size=size):
                self.assertTrue(validate_file_size(size))
    
    def test_validate_file_size_invalid(self):
        """Test invalid file sizes"""
        invalid_sizes = [
            51 * 1024 * 1024,  # 51MB (over limit)
            100 * 1024 * 1024,  # 100MB
            1024 * 1024 * 1024,  # 1GB
        ]
        
        for size in invalid_sizes:
            with self.subTest(size=size):
                self.assertFalse(validate_file_size(size))
    
    def test_get_file_hash(self):
        """Test file hash generation"""
        content1 = b"Test content 1"
        content2 = b"Test content 2"
        content1_duplicate = b"Test content 1"
        
        hash1 = get_file_hash(content1)
        hash2 = get_file_hash(content2)
        hash1_dup = get_file_hash(content1_duplicate)
        
        # Different content should have different hashes
        self.assertNotEqual(hash1, hash2)
        
        # Same content should have same hash
        self.assertEqual(hash1, hash1_dup)
        
        # Hash should be MD5 format (32 characters)
        self.assertEqual(len(hash1), 32)
        self.assertTrue(all(c in '0123456789abcdef' for c in hash1))
    
    def test_generate_safe_filename(self):
        """Test safe filename generation"""
        test_cases = [
            ("contract.pdf", "abc12345", "contract_abc12345.pdf"),
            ("My Contract!@#.docx", "def67890", "My Contract_def67890.docx"),
            ("file with spaces.txt", "ghi11111", "file with spaces_ghi11111.txt"),
        ]
        
        for original, hash_val, expected_pattern in test_cases:
            with self.subTest(original=original):
                result = generate_safe_filename(original, hash_val)
                # Check that it contains the hash
                self.assertIn(hash_val[:8], result)
                # Check that it has the right extension
                self.assertTrue(result.endswith(Path(original).suffix))
    
    def test_get_file_info_valid(self):
        """Test file info extraction for valid files"""
        filename = "contract.pdf"
        file_size = 1024 * 1024  # 1MB
        
        is_valid, error_msg, info = get_file_info(filename, file_size)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
        self.assertEqual(info["filename"], filename)
        self.assertEqual(info["size"], file_size)
        self.assertEqual(info["extension"], "pdf")
        self.assertEqual(info["size_mb"], 1.0)
    
    def test_get_file_info_invalid_type(self):
        """Test file info extraction for invalid file type"""
        filename = "image.jpg"
        file_size = 1024
        
        is_valid, error_msg, info = get_file_info(filename, file_size)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
        self.assertIn("não suportado", error_msg)
    
    def test_get_file_info_invalid_size(self):
        """Test file info extraction for invalid file size"""
        filename = "contract.pdf"
        file_size = 60 * 1024 * 1024  # 60MB (over limit)
        
        is_valid, error_msg, info = get_file_info(filename, file_size)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
        self.assertIn("muito grande", error_msg)

class TestDocumentService(unittest.TestCase):
    """Test document service functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.document_service = DocumentService()
        self.test_content = b"Test contract content for upload testing"
    
    def test_validate_file_success(self):
        """Test successful file validation"""
        filename = "test_contract.pdf"
        file_size = 1024
        
        is_valid, error_msg, info = self.document_service.validate_file(filename, file_size)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
        self.assertIn("filename", info)
        self.assertIn("size", info)
    
    def test_validate_file_failure(self):
        """Test file validation failure"""
        filename = "test_image.jpg"  # Invalid type
        file_size = 1024
        
        is_valid, error_msg, info = self.document_service.validate_file(filename, file_size)
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)
    
    def test_upload_document_success(self):
        """Test successful document upload"""
        filename = "test_contract.pdf"
        
        result = self.document_service.upload_document(
            self.test_content, filename, "test_user"
        )
        
        self.assertTrue(result["success"])
        self.assertIn("document", result["data"])
        self.assertIn("file_path", result["data"])
        
        # Cleanup
        doc_data = result["data"]
        if "file_path" in doc_data:
            file_path = Path(doc_data["file_path"])
            if file_path.exists():
                file_path.unlink()
    
    def test_upload_document_invalid_type(self):
        """Test document upload with invalid file type"""
        filename = "test_image.jpg"
        
        result = self.document_service.upload_document(
            self.test_content, filename, "test_user"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_upload_document_too_large(self):
        """Test document upload with file too large"""
        filename = "large_contract.pdf"
        large_content = b"x" * (60 * 1024 * 1024)  # 60MB
        
        result = self.document_service.upload_document(
            large_content, filename, "test_user"
        )
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)

if __name__ == '__main__':
    unittest.main()