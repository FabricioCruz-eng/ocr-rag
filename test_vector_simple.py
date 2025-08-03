"""
Simple test for vector service functionality
"""
import os
from services.vector_service import VectorService
from models.document import Document, DocumentSection, FileType, DocumentStatus

def test_vector_service():
    """Test basic vector service functionality"""
    print("🧪 Testando VectorService...")
    print("=" * 50)
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY não configurada")
        print("💡 Configure a chave no arquivo .env para testar")
        return False
    
    try:
        # Initialize service
        print("1. Inicializando VectorService...")
        vector_service = VectorService()
        print("   ✅ Serviço inicializado")
        
        # Test health check
        print("\n2. Verificando saúde do serviço...")
        health_result = vector_service.health_check()
        if health_result["success"]:
            health_data = health_result["data"]
            print(f"   ✅ ChromaDB: {'✅' if health_data['details']['chromadb_connected'] else '❌'}")
            print(f"   ✅ OpenAI: {'✅' if health_data['details']['openai_connected'] else '❌'}")
            print(f"   ✅ Collection: {'✅' if health_data['details']['collection_accessible'] else '❌'}")
        else:
            print(f"   ❌ Health check falhou: {health_result['error']}")
        
        # Test embeddings
        print("\n3. Testando criação de embeddings...")
        test_texts = ["Contrato de fibra óptica", "SLA de 4 horas", "Multa de R$ 5.000"]
        embeddings = vector_service.create_embeddings(test_texts)
        print(f"   ✅ Criados {len(embeddings)} embeddings")
        print(f"   📊 Dimensão: {len(embeddings[0]) if embeddings else 0}")
        
        # Test document storage
        print("\n4. Testando armazenamento de documento...")
        test_document = Document(
            filename="test_contract.pdf",
            file_type=FileType.PDF,
            file_size=1024,
            status=DocumentStatus.READY
        )
        
        test_chunks = [
            DocumentSection(
                content="Este contrato define SLA de 4 horas para atendimento",
                section_id="chunk_1"
            ),
            DocumentSection(
                content="A rede de fibra óptica tem extensão de 25 km",
                section_id="chunk_2"
            ),
            DocumentSection(
                content="Multa por descumprimento: R$ 5.000,00",
                section_id="chunk_3"
            )
        ]
        
        store_result = vector_service.store_document_chunks(test_document, test_chunks)
        if store_result["success"]:
            print(f"   ✅ Armazenados {store_result['data']['stored_count']} chunks")
        else:
            print(f"   ❌ Erro no armazenamento: {store_result['error']}")
            return False
        
        # Test semantic search
        print("\n5. Testando busca semântica...")
        search_queries = [
            "Qual o tempo de SLA?",
            "Quantos quilômetros de fibra?",
            "Valor da multa"
        ]
        
        for query in search_queries:
            search_result = vector_service.semantic_search(query, top_k=2)
            if search_result["success"]:
                results = search_result["data"]["results"]
                print(f"   🔍 '{query}': {len(results)} resultado(s)")
                if results:
                    top_result = results[0]
                    similarity = top_result["relevance_score"]
                    print(f"      📊 Melhor match: {similarity:.1%} - {top_result['content'][:50]}...")
            else:
                print(f"   ❌ Erro na busca: {search_result['error']}")
        
        # Test collection stats
        print("\n6. Verificando estatísticas da coleção...")
        stats_result = vector_service.get_collection_stats()
        if stats_result["success"]:
            stats = stats_result["data"]
            print(f"   📊 Total chunks: {stats['total_chunks']}")
            print(f"   📄 Documentos únicos: {stats['unique_documents']}")
        
        # Cleanup
        print("\n7. Limpando dados de teste...")
        delete_result = vector_service.delete_document_vectors(test_document.id)
        if delete_result["success"]:
            print(f"   🧹 Removidos {delete_result['data']['deleted_count']} vetores")
        
        print("\n" + "=" * 50)
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("💡 VectorService está funcionando corretamente")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_vector_service()
    if success:
        print("\n🚀 Sistema de vetorização pronto para uso!")
        print("💡 Execute 'streamlit run app.py' para testar a interface completa")
    else:
        print("\n⚠️  Verifique os erros acima antes de prosseguir")