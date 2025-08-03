#!/usr/bin/env python3
"""
Debug do sistema de vetores para identificar problemas
"""
import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from services.vector_service import VectorService
from services.document_service import DocumentService
from models.document import Document, DocumentSection, DocumentStatus
import uuid

def test_vector_service():
    """Teste do serviço de vetores"""
    print("🔍 Testando Serviço de Vetores...")
    
    try:
        # Inicializar serviço
        vector_service = VectorService()
        print("✅ VectorService inicializado")
        
        # Teste de health check
        health_result = vector_service.health_check()
        print(f"🏥 Health Check: {health_result}")
        
        if health_result["success"]:
            health_data = health_result["data"]
            print(f"   - ChromaDB: {'✅' if health_data['details']['chromadb_connected'] else '❌'}")
            print(f"   - OpenAI: {'✅' if health_data['details']['openai_connected'] else '❌'}")
            print(f"   - Collection: {'✅' if health_data['details']['collection_accessible'] else '❌'}")
            print(f"   - Total docs: {health_data['details']['total_documents']}")
        
        # Teste de embeddings
        print("\n📊 Testando criação de embeddings...")
        test_texts = ["Contrato de SLA", "Tempo de atendimento 24 horas"]
        embeddings = vector_service.create_embeddings(test_texts)
        print(f"✅ Criados {len(embeddings)} embeddings")
        print(f"   - Dimensão: {len(embeddings[0]) if embeddings else 0}")
        
        # Teste de armazenamento
        print("\n💾 Testando armazenamento de chunks...")
        
        # Criar documento de teste
        test_doc = Document(
            id=str(uuid.uuid4()),
            filename="test_contract.pdf",
            file_type="pdf",
            file_size=1024,
            user_id="test_user",
            status=DocumentStatus.READY
        )
        
        # Criar chunks de teste
        test_chunks = [
            DocumentSection(
                content="Este contrato estabelece SLA de 24 horas para atendimento.",
                section_id="chunk_1",
                page_number=1
            ),
            DocumentSection(
                content="A multa por descumprimento será de R$ 10.000,00.",
                section_id="chunk_2", 
                page_number=1
            )
        ]
        
        # Armazenar chunks
        store_result = vector_service.store_document_chunks(test_doc, test_chunks)
        print(f"📦 Resultado do armazenamento: {store_result}")
        
        if store_result["success"]:
            print(f"✅ Armazenados {store_result['data']['stored_count']} chunks")
            
            # Teste de busca semântica
            print("\n🔍 Testando busca semântica...")
            search_result = vector_service.semantic_search(
                query="qual o tempo de SLA?",
                document_id=test_doc.id,
                top_k=2
            )
            
            print(f"🔍 Resultado da busca: {search_result}")
            
            if search_result["success"]:
                results = search_result["data"]["results"]
                print(f"✅ Encontrados {len(results)} resultados")
                
                for i, result in enumerate(results, 1):
                    print(f"   {i}. Relevância: {result['relevance_score']:.2f}")
                    print(f"      Conteúdo: {result['content'][:100]}...")
            
            # Limpar dados de teste
            print("\n🧹 Limpando dados de teste...")
            delete_result = vector_service.delete_document_vectors(test_doc.id)
            print(f"🗑️ Resultado da limpeza: {delete_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de vetores: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_document_service():
    """Teste do serviço de documentos"""
    print("\n📄 Testando Serviço de Documentos...")
    
    try:
        doc_service = DocumentService()
        print("✅ DocumentService inicializado")
        
        # Verificar se há documentos
        docs_result = doc_service.list_documents("test_user")
        print(f"📋 Documentos existentes: {docs_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de documentos: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Função principal"""
    print("🚀 Debug do Sistema de Vetores")
    print("=" * 50)
    
    # Verificar variáveis de ambiente
    print("🔧 Verificando configuração...")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"✅ OPENAI_API_KEY configurada (termina em: ...{openai_key[-10:]})")
    else:
        print("❌ OPENAI_API_KEY não configurada")
        return False
    
    # Verificar diretórios
    chroma_path = Path("./chroma_db")
    if chroma_path.exists():
        print(f"✅ Diretório ChromaDB existe: {chroma_path}")
    else:
        print(f"⚠️ Diretório ChromaDB não existe: {chroma_path}")
        chroma_path.mkdir(exist_ok=True)
        print("✅ Diretório ChromaDB criado")
    
    # Executar testes
    tests = [
        ("Vector Service", test_vector_service),
        ("Document Service", test_document_service)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro crítico em {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 Resumo dos Testes:")
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    if passed == total:
        print(f"\n🎉 Todos os testes passaram! ({passed}/{total})")
        print("✅ Sistema de vetores está funcionando corretamente!")
    else:
        print(f"\n⚠️ {passed}/{total} testes passaram")
        print("🔧 Verifique os erros acima para corrigir os problemas")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)