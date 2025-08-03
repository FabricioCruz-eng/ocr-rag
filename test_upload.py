"""
Test script for document upload functionality
"""
import os
from services.document_service import DocumentService

def test_upload_functionality():
    """Test the upload functionality with sample data"""
    print("🧪 Testando funcionalidade de upload...")
    print("=" * 50)
    
    # Initialize service
    doc_service = DocumentService()
    
    # Test cases
    test_cases = [
        {
            "name": "PDF válido",
            "filename": "contrato_teste.pdf",
            "content": b"Conteudo de teste para contrato PDF",
            "should_pass": True
        },
        {
            "name": "DOCX válido", 
            "filename": "documento_teste.docx",
            "content": b"Conteudo de teste para documento DOCX",
            "should_pass": True
        },
        {
            "name": "TXT válido",
            "filename": "texto_teste.txt", 
            "content": b"Conteudo de teste para arquivo TXT",
            "should_pass": True
        },
        {
            "name": "Tipo inválido",
            "filename": "imagem_teste.jpg",
            "content": b"Conteudo de teste para imagem",
            "should_pass": False
        },
        {
            "name": "Arquivo muito grande",
            "filename": "arquivo_grande.pdf",
            "content": b"x" * (60 * 1024 * 1024),  # 60MB
            "should_pass": False
        }
    ]
    
    # Run tests
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testando: {test_case['name']}")
        print(f"   Arquivo: {test_case['filename']}")
        print(f"   Tamanho: {len(test_case['content'])/1024:.1f} KB")
        
        # Test upload
        result = doc_service.upload_document(
            file_content=test_case["content"],
            filename=test_case["filename"],
            user_id="test_user"
        )
        
        # Check result
        if test_case["should_pass"]:
            if result["success"]:
                print("   ✅ PASSOU - Upload realizado com sucesso")
                passed += 1
                
                # Cleanup - remove uploaded file
                if "file_path" in result["data"]:
                    file_path = result["data"]["file_path"]
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"   🧹 Arquivo de teste removido: {file_path}")
            else:
                print(f"   ❌ FALHOU - Deveria passar mas falhou: {result['error']}")
        else:
            if not result["success"]:
                print(f"   ✅ PASSOU - Rejeitado corretamente: {result['error']}")
                passed += 1
            else:
                print("   ❌ FALHOU - Deveria ser rejeitado mas passou")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 RESUMO DOS TESTES:")
    print(f"   Total: {total}")
    print(f"   Passou: {passed}")
    print(f"   Falhou: {total - passed}")
    print(f"   Taxa de sucesso: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("⚠️  Alguns testes falharam")
    
    return passed == total

def test_file_validation():
    """Test file validation functions"""
    print("\n🔍 Testando validação de arquivos...")
    print("=" * 30)
    
    from utils.file_utils import validate_file_type, validate_file_size, get_file_info
    
    # Test file type validation
    print("1. Testando validação de tipo de arquivo:")
    valid_files = ["contract.pdf", "doc.docx", "text.txt"]
    invalid_files = ["image.jpg", "sheet.xlsx", "no_extension"]
    
    for filename in valid_files:
        result = validate_file_type(filename)
        print(f"   {filename}: {'✅' if result else '❌'}")
    
    for filename in invalid_files:
        result = validate_file_type(filename)
        print(f"   {filename}: {'❌' if not result else '✅'} (rejeitado)")
    
    # Test file size validation
    print("\n2. Testando validação de tamanho:")
    sizes = [
        (1024, "1 KB"),
        (1024*1024, "1 MB"), 
        (10*1024*1024, "10 MB"),
        (60*1024*1024, "60 MB")
    ]
    
    for size, desc in sizes:
        result = validate_file_size(size)
        status = "✅" if result else "❌"
        print(f"   {desc}: {status}")

if __name__ == "__main__":
    # Run validation tests
    test_file_validation()
    
    # Run upload tests
    success = test_upload_functionality()
    
    if success:
        print("\n🚀 Sistema de upload está funcionando corretamente!")
        print("💡 Próximo passo: Execute 'streamlit run app.py' para testar a interface")
    else:
        print("\n⚠️  Verifique os erros acima antes de prosseguir")