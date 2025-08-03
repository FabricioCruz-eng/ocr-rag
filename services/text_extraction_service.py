"""
Text extraction service for different document formats with OCR support
"""
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO
import tempfile
import os

# Document processing libraries
import PyPDF2
from docx import Document as DocxDocument
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

# Configure Tesseract path based on environment
import platform
import subprocess

def configure_tesseract():
    """Configure Tesseract path based on environment"""
    system = platform.system().lower()
    
    if system == "windows":
        # Windows local development
        tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            return True
    elif system == "linux":
        # Linux production (Railway, Heroku, etc.)
        try:
            # Try common Linux paths for Tesseract
            common_paths = [
                '/usr/bin/tesseract',
                '/usr/local/bin/tesseract',
                'tesseract'  # In PATH
            ]
            
            for path in common_paths:
                try:
                    if path == 'tesseract':
                        result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            pytesseract.pytesseract.tesseract_cmd = 'tesseract'
                            return True
                    else:
                        if os.path.exists(path):
                            pytesseract.pytesseract.tesseract_cmd = path
                            return True
                except:
                    continue
        except:
            pass
    
    return False

# Configure Tesseract on import
TESSERACT_AVAILABLE = configure_tesseract()

from services.base_service import BaseService
from models.document import Document, DocumentSection, DocumentStatus
from config import config

class TextExtractionService(BaseService):
    """Service for extracting text from various document formats"""
    
    def __init__(self):
        super().__init__()
        self.chunk_size = config.CHUNK_SIZE
        self.chunk_overlap = config.CHUNK_OVERLAP
    
    def extract_text_from_file(self, file_path: Path, file_type: str) -> Dict[str, Any]:
        """
        Extract text from file based on its type
        
        Args:
            file_path: Path to the file
            file_type: Type of file (pdf, docx, txt)
            
        Returns:
            Dictionary with extraction result
        """
        try:
            if not file_path.exists():
                return self.handle_error(
                    Exception(f"Arquivo não encontrado: {file_path}"),
                    "file extraction"
                )
            
            # Extract text based on file type
            if file_type.lower() == 'pdf':
                text_content, metadata = self._extract_from_pdf(file_path)
            elif file_type.lower() == 'docx':
                text_content, metadata = self._extract_from_docx(file_path)
            elif file_type.lower() == 'txt':
                text_content, metadata = self._extract_from_txt(file_path)
            else:
                return self.handle_error(
                    Exception(f"Tipo de arquivo não suportado: {file_type}"),
                    "file extraction"
                )
            
            # Clean and process text
            cleaned_text = self._clean_text(text_content)
            
            # Create text chunks
            chunks = self._create_text_chunks(cleaned_text)
            
            self.log_info(f"Text extracted successfully from {file_path.name}")
            self.log_info(f"Extracted {len(cleaned_text)} characters in {len(chunks)} chunks")
            
            return self.success_response(
                data={
                    "text_content": cleaned_text,
                    "chunks": chunks,
                    "metadata": metadata,
                    "stats": {
                        "total_chars": len(cleaned_text),
                        "total_words": len(cleaned_text.split()),
                        "total_chunks": len(chunks),
                        "avg_chunk_size": len(cleaned_text) // len(chunks) if chunks else 0
                    }
                },
                message="Texto extraído com sucesso"
            )
            
        except Exception as e:
            return self.handle_error(e, "text extraction")
    
    def _extract_from_pdf(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract text from PDF file with OCR support for images"""
        text_content = ""
        metadata = {"pages": 0, "format": "pdf", "ocr_used": False, "images_processed": 0}
        
        try:
            # Use PyMuPDF for better PDF handling
            pdf_document = fitz.open(str(file_path))
            metadata["pages"] = len(pdf_document)
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                
                # Add page marker
                text_content += f"\n--- PÁGINA {page_num + 1} ---\n"
                
                # Extract regular text
                page_text = page.get_text()
                if page_text.strip():
                    text_content += page_text + "\n"
                    self.log_info(f"Extracted text from page {page_num + 1}: {len(page_text)} chars")
                
                # Extract text from images using OCR
                image_list = page.get_images()
                if image_list:
                    self.log_info(f"Found {len(image_list)} images on page {page_num + 1}")
                    
                    for img_index, img in enumerate(image_list):
                        try:
                            # Extract image
                            xref = img[0]
                            pix = fitz.Pixmap(pdf_document, xref)
                            
                            # Convert to PIL Image if needed
                            if pix.n - pix.alpha < 4:  # GRAY or RGB
                                img_data = pix.tobytes("png")
                                pil_image = Image.open(BytesIO(img_data))
                                
                                # Perform OCR
                                ocr_text = self._extract_text_from_image(pil_image)
                                
                                if ocr_text.strip():
                                    text_content += f"\n[TEXTO EXTRAÍDO DA IMAGEM {img_index + 1}]\n"
                                    text_content += ocr_text + "\n"
                                    metadata["ocr_used"] = True
                                    metadata["images_processed"] += 1
                                    self.log_info(f"OCR extracted {len(ocr_text)} chars from image {img_index + 1} on page {page_num + 1}")
                            
                            pix = None  # Free memory
                            
                        except Exception as e:
                            self.log_warning(f"Error processing image {img_index + 1} on page {page_num + 1}: {str(e)}")
                            continue
            
            # Extract metadata
            pdf_metadata = pdf_document.metadata
            if pdf_metadata:
                metadata.update({
                    "title": pdf_metadata.get('title', ''),
                    "author": pdf_metadata.get('author', ''),
                    "subject": pdf_metadata.get('subject', ''),
                    "creator": pdf_metadata.get('creator', '')
                })
            
            pdf_document.close()
            
        except Exception as e:
            # Fallback to PyPDF2 if PyMuPDF fails
            self.log_warning(f"PyMuPDF failed, falling back to PyPDF2: {str(e)}")
            return self._extract_from_pdf_fallback(file_path)
        
        return text_content, metadata
    
    def _extract_from_pdf_fallback(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Fallback PDF extraction using PyPDF2"""
        text_content = ""
        metadata = {"pages": 0, "format": "pdf", "fallback_used": True}
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata["pages"] = len(pdf_reader.pages)
                
                # Extract text from each page
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content += f"\n--- PÁGINA {page_num + 1} ---\n"
                            text_content += page_text + "\n"
                    except Exception as e:
                        self.log_warning(f"Error extracting page {page_num + 1}: {str(e)}")
                        continue
                
                # Extract metadata if available
                if pdf_reader.metadata:
                    metadata.update({
                        "title": pdf_reader.metadata.get('/Title', ''),
                        "author": pdf_reader.metadata.get('/Author', ''),
                        "subject": pdf_reader.metadata.get('/Subject', ''),
                        "creator": pdf_reader.metadata.get('/Creator', '')
                    })
                    
        except Exception as e:
            raise Exception(f"Erro ao processar PDF: {str(e)}")
        
        return text_content, metadata
    
    def _extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from image using OCR"""
        try:
            # Check if Tesseract is available
            if not self._is_tesseract_available():
                self.log_warning("Tesseract OCR não está disponível. Instale para extrair texto de imagens.")
                return "[IMAGEM DETECTADA - INSTALE TESSERACT PARA EXTRAIR TEXTO]"
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_image_for_ocr(image)
            
            # Try multiple OCR configurations for better results
            configs = [
                ('Portuguese + PSM 6', r'--oem 3 --psm 6 -l por'),
                ('Portuguese + PSM 3', r'--oem 3 --psm 3 -l por'),
                ('English + PSM 6', r'--oem 3 --psm 6'),
                ('Default', r'--psm 6')
            ]
            
            best_text = ""
            best_confidence = 0
            
            for config_name, config in configs:
                try:
                    text = pytesseract.image_to_string(processed_image, config=config)
                    text = text.strip()
                    
                    if text and len(text) > len(best_text):
                        best_text = text
                        self.log_info(f"OCR success with {config_name}: {len(text)} chars")
                        break  # Use first successful result
                        
                except Exception as e:
                    self.log_warning(f"OCR failed with {config_name}: {str(e)}")
                    continue
            
            if best_text:
                return best_text
            else:
                self.log_warning("All OCR configurations failed")
                return "[IMAGEM DETECTADA - OCR FALHOU]"
            
        except Exception as e:
            self.log_warning(f"OCR completely failed: {str(e)}")
            return "[IMAGEM DETECTADA - OCR FALHOU]"
    
    def _is_tesseract_available(self) -> bool:
        """Check if Tesseract is available"""
        global TESSERACT_AVAILABLE
        
        if not TESSERACT_AVAILABLE:
            return False
            
        try:
            # Test if Tesseract actually works
            import subprocess
            cmd = pytesseract.pytesseract.tesseract_cmd
            if isinstance(cmd, str):
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                return result.returncode == 0
            return False
        except:
            return False
    
    def _preprocess_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Preprocess image to improve OCR accuracy"""
        try:
            # Convert to RGB first if needed, then to grayscale
            if image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')
            
            # Convert to grayscale for better OCR
            if image.mode != 'L':
                image = image.convert('L')
            
            # Resize if too small (OCR works better on larger images)
            width, height = image.size
            min_size = 600  # Increased minimum size for better OCR
            
            if width < min_size or height < min_size:
                scale_factor = max(min_size / width, min_size / height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                self.log_info(f"Image resized from {width}x{height} to {new_width}x{new_height}")
            
            # Apply contrast enhancement
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)  # Slight contrast boost
            
            # Apply sharpening
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)  # Slight sharpening
            
            return image
            
        except Exception as e:
            self.log_warning(f"Image preprocessing failed: {str(e)}")
            return image
    
    def _extract_from_docx(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract text from DOCX file"""
        text_content = ""
        metadata = {"format": "docx", "paragraphs": 0}
        
        try:
            doc = DocxDocument(file_path)
            
            # Extract text from paragraphs
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
                    text_content += para.text + "\n"
            
            metadata["paragraphs"] = len(paragraphs)
            
            # Extract metadata from document properties
            if hasattr(doc, 'core_properties'):
                core_props = doc.core_properties
                metadata.update({
                    "title": core_props.title or '',
                    "author": core_props.author or '',
                    "subject": core_props.subject or '',
                    "created": str(core_props.created) if core_props.created else '',
                    "modified": str(core_props.modified) if core_props.modified else ''
                })
                
        except Exception as e:
            raise Exception(f"Erro ao processar DOCX: {str(e)}")
        
        return text_content, metadata
    
    def _extract_from_txt(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract text from TXT file"""
        metadata = {"format": "txt", "encoding": "utf-8"}
        
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            text_content = ""
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        text_content = file.read()
                        metadata["encoding"] = encoding
                        break
                except UnicodeDecodeError:
                    continue
            
            if not text_content:
                raise Exception("Não foi possível decodificar o arquivo de texto")
                
            metadata["lines"] = len(text_content.split('\n'))
            
        except Exception as e:
            raise Exception(f"Erro ao processar TXT: {str(e)}")
        
        return text_content, metadata
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page markers for cleaner text
        text = re.sub(r'--- PÁGINA \d+ ---', '', text)
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _create_text_chunks(self, text: str) -> List[DocumentSection]:
        """
        Create text chunks for vector embedding
        
        Args:
            text: Full text content
            
        Returns:
            List of DocumentSection objects
        """
        if not text:
            return []
        
        chunks = []
        words = text.split()
        
        # Calculate words per chunk (approximate)
        words_per_chunk = self.chunk_size // 5  # Assuming average 5 chars per word
        overlap_words = self.chunk_overlap // 5
        
        start_idx = 0
        chunk_num = 1
        
        while start_idx < len(words):
            # Get chunk words
            end_idx = min(start_idx + words_per_chunk, len(words))
            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)
            
            # Create document section
            section = DocumentSection(
                content=chunk_text,
                section_id=f"chunk_{chunk_num}",
                start_char=self._get_char_position(text, start_idx, words),
                end_char=self._get_char_position(text, end_idx - 1, words)
            )
            
            chunks.append(section)
            
            # Move to next chunk with overlap
            start_idx = max(start_idx + words_per_chunk - overlap_words, start_idx + 1)
            chunk_num += 1
            
            # Prevent infinite loop
            if start_idx >= len(words):
                break
        
        return chunks
    
    def _get_char_position(self, text: str, word_idx: int, words: List[str]) -> int:
        """Get character position for a word index"""
        if word_idx >= len(words):
            return len(text)
        
        # Approximate character position
        chars_before = sum(len(word) + 1 for word in words[:word_idx])  # +1 for space
        return min(chars_before, len(text))
    
    def process_document(self, document: Document, file_path: Path) -> Dict[str, Any]:
        """
        Process a document and extract text with chunking
        
        Args:
            document: Document model
            file_path: Path to the document file
            
        Returns:
            Dictionary with processing result
        """
        try:
            # Extract text
            extraction_result = self.extract_text_from_file(file_path, document.file_type)
            
            if not extraction_result["success"]:
                return extraction_result
            
            # Update document with extracted content
            extracted_data = extraction_result["data"]
            
            # This would typically update the document in a database
            # For now, we'll return the processed data
            processed_document = {
                "id": document.id,
                "filename": document.filename,
                "status": DocumentStatus.READY,
                "text_content": extracted_data["text_content"],
                "chunks": [chunk.model_dump() for chunk in extracted_data["chunks"]],
                "metadata": extracted_data["metadata"],
                "stats": extracted_data["stats"]
            }
            
            self.log_info(f"Document processed successfully: {document.id}")
            
            return self.success_response(
                data=processed_document,
                message="Documento processado com sucesso"
            )
            
        except Exception as e:
            return self.handle_error(e, "document processing")
    
    def extract_contract_specific_info(self, text: str) -> Dict[str, Any]:
        """
        Extract contract-specific information using regex patterns
        
        Args:
            text: Full text content
            
        Returns:
            Dictionary with extracted contract information
        """
        try:
            contract_info = {
                "contract_number": None,
                "sla_times": [],
                "fiber_km": [],
                "penalty_values": [],
                "contract_duration": [],
                "parties": []
            }
            
            # Contract number patterns
            contract_patterns = [
                r'contrato\s+n[°º]?\s*(\w+[-/]\w+[-/]\w+)',
                r'contrato\s+(\w+[-/]\w+[-/]\w+)',
                r'n[°º]\s*(\w+[-/]\w+[-/]\w+)'
            ]
            
            for pattern in contract_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    contract_info["contract_number"] = match.group(1)
                    break
            
            # SLA time patterns
            sla_patterns = [
                r'sla\s+.*?(\d+)\s*(horas?|dias?|minutos?)',
                r'prazo\s+.*?(\d+)\s*(horas?|dias?|minutos?)',
                r'atendimento\s+.*?(\d+)\s*(horas?|dias?|minutos?)',
                r'(\d+)\s*(horas?|dias?|minutos?)\s+para.*?(incidente|atendimento|sla)',
                r'será\s+de\s+(\d+)\s*(horas?|dias?|minutos?)'
            ]
            
            for pattern in sla_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    contract_info["sla_times"].append(f"{match.group(1)} {match.group(2)}")
            
            # Fiber km patterns
            fiber_patterns = [
                r'(\d+(?:,\d+)?)\s*km\s+de\s+fibra',
                r'fibra\s+(?:óptica\s+)?.*?(\d+(?:,\d+)?)\s*km',
                r'extensão\s+de\s+(\d+(?:,\d+)?)\s*km',
                r'será\s+de\s+(\d+(?:,\d+)?)\s*km'
            ]
            
            for pattern in fiber_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    contract_info["fiber_km"].append(match.group(1) + " km")
            
            # Penalty value patterns
            penalty_patterns = [
                r'multa\s+de\s+r\$\s*(\d+(?:\.\d{3})*(?:,\d{2})?)',
                r'penalidade\s+de\s+r\$\s*(\d+(?:\.\d{3})*(?:,\d{2})?)',
                r'valor\s+da\s+multa\s*:\s*r\$\s*(\d+(?:\.\d{3})*(?:,\d{2})?)'
            ]
            
            for pattern in penalty_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    contract_info["penalty_values"].append(f"R$ {match.group(1)}")
            
            # Contract duration patterns
            duration_patterns = [
                r'vigência\s+de\s+(\d+)\s*(anos?|meses?)',
                r'prazo\s+de\s+(\d+)\s*(anos?|meses?)',
                r'duração\s+de\s+(\d+)\s*(anos?|meses?)'
            ]
            
            for pattern in duration_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    contract_info["contract_duration"].append(f"{match.group(1)} {match.group(2)}")
            
            return self.success_response(
                data=contract_info,
                message="Informações contratuais extraídas"
            )
            
        except Exception as e:
            return self.handle_error(e, "contract info extraction")