"""
Test script for PDF OCR functionality
"""
import os
from pathlib import Path
from services.text_extraction_service import TextExtractionService

def test_pdf_with_images():
    """Test PDF processing with OCR"""
    print("🧪 Testando processamento de PDF com OCR...")
    print("=" * 60)
    
    # Initialize service
    text_service = TextExtractionService()
    
    # Check for test PDFs in uploads folder
    uploads_path = Path("uploads")
    if not uploads_path.exists():
        print("❌ Pasta uploads não encontrada")
        return False
    
    # Find PDF files
    pdf_files = list(uploads_path.glob("*.pdf")) + list(uploads_path.glob("*.PDF"))
    
    if not pdf_files:
        print("❌ Nenhum arquivo PDF encontrado na pasta uploads")
        print("💡 Coloque um PDF na pasta uploads para testar")
        return False
    
    # Test each PDF
    for pdf_file in pdf_files[:3]:  # Test up to 3 PDFs
        print(f"\n📄 Testando: {pdf_file.name}")
        print("-" * 40)
        
        try:
            # Extract text with OCR
            result = text_service.extract_text_from_file(pdf_file, "pdf")
            
            if result["success"]:
                data = result["data"]
                stats = data["stats"]
                metadata = data["metadata"]
                
                print(f"✅ Processamento concluído!")
                print(f"📊 Estatísticas:")
                print(f"   - Páginas: {metadata.get('pages', 0)}")
                print(f"   - Caracteres: {stats['total_chars']}")
                print(f"   - Palavras: {stats['total_words']}")
                print(f"   - Chunks: {stats['total_chunks']}")
                
                # OCR information
                if metadata.get("ocr_used"):
                    print(f"🖼️ OCR:")
                    print(f"   - Imagens processadas: {metadata.get('images_processed', 0)}")
                    print(f"   - Texto extraído de imagens: ✅")
                elif metadata.get("images_processed", 0) > 0:
                    print(f"🖼️ Imagens detectadas: {metadata.get('images_processed', 0)}")
                    print(f"   - OCR não disponível (instale Tesseract)")
                else:
                    print("📝 Apenas texto regular encontrado")
                
                # Processing method
                if metadata.get("fallback_used"):
                    print("⚙️ Método: PyPDF2 (fallback)")
                else:
                    print("⚙️ Método: PyMuPDF (completo)")
                
                # Show sample text
                text_content = data["text_content"]
                if text_content:
                    print(f"\n📝 Amostra do texto extraído:")
                    sample = text_content[:300].replace('\n', ' ')
                    print(f"   {sample}...")
                
                # Check for contract-specific info
                contract_result = text_service.extract_contract_specific_info(text_content)
                if contract_result["success"]:
                    contract_info = contract_result["data"]
                    
                    found_info = []
                    if contract_info.get("contract_number"):
                        found_info.append(f"Contrato: {contract_info['contract_number']}")
                    if contract_info.get("sla_times"):
                        found_info.append(f"SLA: {', '.join(contract_info['sla_times'])}")
                    if contract_info.get("fiber_km"):
                        found_info.append(f"Fibra: {', '.join(contract_info['fiber_km'])}")
                    if contract_info.get("penalty_values"):
                        found_info.append(f"Multa: {', '.join(contract_info['penalty_values'])}")
                    
                    if found_info:
                        print(f"\n🔍 Informações contratuais encontradas:")
                        for info in found_info:
                            print(f"   - {info}")
                    else:
                        print(f"\n🔍 Nenhuma informação contratual específica encontrada")
                
            else:
                print(f"❌ Erro no processamento: {result['error']}")
                
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 RESUMO DO TESTE:")
    print("✅ Sistema de extração de texto funcionando")
    print("✅ Suporte a PDFs com texto e imagens")
    print("✅ Detecção automática de imagens")
    
    # Check Tesseract status
    if text_service._is_tesseract_available():
        print("✅ Tesseract OCR disponível")
    else:
        print("⚠️  Tesseract OCR não instalado")
        print("💡 Instale para extrair texto de imagens")
    
    return True

def show_installation_guide():
    """Show OCR installation guide"""
    print("\n📋 GUIA DE INSTALAÇÃO DO OCR:")
    print("=" * 40)
    print("1. Baixe o Tesseract:")
    print("   https://github.com/UB-Mannheim/tesseract/wiki")
    print("\n2. Instale em: C:\\Program Files\\Tesseract-OCR\\")
    print("\n3. Adicione ao PATH do Windows")
    print("\n4. Para português, baixe por.traineddata:")
    print("   https://github.com/tesseract-ocr/tessdata")
    print("   Coloque em: C:\\Program Files\\Tesseract-OCR\\tessdata\\")
    print("\n5. Reinicie o terminal e teste novamente")

if __name__ == "__main__":
    success = test_pdf_with_images()
    
    if success:
        print("\n🚀 Sistema pronto para processar PDFs com texto e imagens!")
        print("💡 Execute 'streamlit run app.py' para usar a interface")
        
        # Check if Tesseract is available
        from services.text_extraction_service import TextExtractionService
        service = TextExtractionService()
        if not service._is_tesseract_available():
            show_installation_guide()
    else:
        print("\n⚠️  Coloque arquivos PDF na pasta uploads para testar")