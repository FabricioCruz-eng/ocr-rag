"""
Test ChromaDB functionality without OpenAI
"""
import chromadb
from chromadb.config import Settings
import numpy as np

def test_chromadb():
    """Test basic ChromaDB functionality"""
    print("🧪 Testando ChromaDB...")
    print("=" * 50)
    
    try:
        # Initialize ChromaDB
        print("1. Inicializando ChromaDB...")
        client = chromadb.PersistentClient(
            path="./test_chroma_db",
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        print("   ✅ Cliente ChromaDB inicializado")
        
        # Create collection
        print("\n2. Criando coleção...")
        collection = client.get_or_create_collection(
            name="test_collection",
            metadata={"description": "Test collection"}
        )
        print("   ✅ Coleção criada")
        
        # Test data
        print("\n3. Preparando dados de teste...")
        documents = [
            "Este contrato define SLA de 4 horas para atendimento",
            "A rede de fibra óptica tem extensão de 25 km",
            "Multa por descumprimento: R$ 5.000,00"
        ]
        
        # Create fake embeddings (normally would come from OpenAI)
        embeddings = [
            np.random.rand(384).tolist(),  # Fake embedding dimension
            np.random.rand(384).tolist(),
            np.random.rand(384).tolist()
        ]
        
        ids = ["doc1", "doc2", "doc3"]
        metadatas = [
            {"type": "sla", "document_id": "contract_1"},
            {"type": "fiber", "document_id": "contract_1"},
            {"type": "penalty", "document_id": "contract_1"}
        ]
        
        print("   ✅ Dados preparados")
        
        # Store in ChromaDB
        print("\n4. Armazenando no ChromaDB...")
        collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print("   ✅ Documentos armazenados")
        
        # Test retrieval
        print("\n5. Testando recuperação...")
        results = collection.get(
            ids=["doc1", "doc2"],
            include=["documents", "metadatas"]
        )
        
        print(f"   ✅ Recuperados {len(results['documents'])} documentos")
        for i, doc in enumerate(results["documents"]):
            print(f"      📄 Doc {i+1}: {doc[:50]}...")
        
        # Test query (with fake query embedding)
        print("\n6. Testando busca...")
        query_embedding = np.random.rand(384).tolist()
        
        search_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=2,
            include=["documents", "metadatas", "distances"]
        )
        
        print(f"   ✅ Busca retornou {len(search_results['documents'][0])} resultados")
        for i, doc in enumerate(search_results["documents"][0]):
            distance = search_results["distances"][0][i]
            print(f"      🔍 Resultado {i+1}: distância={distance:.3f}")
            print(f"         {doc[:50]}...")
        
        # Test collection stats
        print("\n7. Verificando estatísticas...")
        count = collection.count()
        print(f"   📊 Total de documentos: {count}")
        
        # Cleanup
        print("\n8. Limpando dados de teste...")
        client.delete_collection(name="test_collection")
        print("   🧹 Coleção removida")
        
        print("\n" + "=" * 50)
        print("🎉 CHROMADB FUNCIONANDO PERFEITAMENTE!")
        print("💡 O banco vetorial está pronto para uso")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_chromadb()
    if success:
        print("\n🚀 ChromaDB validado com sucesso!")
        print("💡 Configure uma chave OpenAI válida para testar embeddings reais")
    else:
        print("\n⚠️  Verifique os erros acima")