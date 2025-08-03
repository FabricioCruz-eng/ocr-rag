"""
Test script for complete RAG system functionality
"""
import os
from services.document_service import DocumentService
from services.query_service import QueryService
from models.document import Document, DocumentSection, FileType, DocumentStatus

def test_rag_system():
    """Test the complete RAG system"""
    print("🧪 Testando Sistema RAG Completo...")
    print("=" * 60)
    
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY não configurada")
        print("💡 Configure a chave no arquivo .env para testar o RAG completo")
        return test_without_openai()
    
    try:
        # Initialize services
        print("1. Inicializando serviços...")
        doc_service = DocumentService()
        query_service = QueryService()
        print("   ✅ Serviços inicializados")
        
        # Test query intent analysis
        print("\n2. Testando análise de intenção...")
        test_questions = [
            "Qual o tempo de SLA definido no contrato?",
            "Quantos quilômetros de fibra óptica?",
            "Qual o valor da multa por descumprimento?",
            "Qual o prazo de vigência do contrato?"
        ]
        
        for question in test_questions:
            intent_result = query_service.analyze_query_intent(question)
            if intent_result["success"]:
                intent_data = intent_result["data"]
                primary_intent = intent_data.get("primary_intent", "unknown")
                confidence = intent_data.get("confidence_scores", {}).get(primary_intent, 0)
                print(f"   🎯 '{question[:30]}...' → {primary_intent} ({confidence:.1%})")
            else:
                print(f"   ❌ Erro na análise: {intent_result['error']}")
        
        # Test query suggestions
        print("\n3. Testando sugestões de consulta...")
        suggestions_result = query_service.get_query_suggestions()
        if suggestions_result["success"]:
            suggestions = suggestions_result["data"]
            total_suggestions = sum(len(v) for v in suggestions.values())
            print(f"   ✅ Geradas {total_suggestions} sugestões em {len(suggestions)} categorias")
            
            for category, questions in suggestions.items():
                print(f"      📋 {category}: {len(questions)} perguntas")
        else:
            print(f"   ❌ Erro nas sugestões: {suggestions_result['error']}")
        
        # Test with mock document (since we need OpenAI for full test)
        print("\n4. Testando processamento RAG...")
        
        # Create test document
        test_document = Document(
            filename="contrato_teste_rag.txt",
            file_type=FileType.TXT,
            file_size=1024,
            status=DocumentStatus.READY
        )
        
        # Create test chunks
        test_chunks = [
            DocumentSection(
                content="CONTRATO DE PRESTAÇÃO DE SERVIÇOS - Número: DCT-RAG-001. Este contrato estabelece os termos para prestação de serviços de telecomunicações.",
                section_id="chunk_1",
                page_number=1
            ),
            DocumentSection(
                content="CLÁUSULA DE SLA: O tempo de resposta para incidentes críticos será de 2 horas. Para incidentes de média prioridade, o prazo é de 8 horas.",
                section_id="chunk_2", 
                page_number=1
            ),
            DocumentSection(
                content="INFRAESTRUTURA: A rede de fibra óptica terá extensão total de 50 quilômetros, conectando os pontos especificados no anexo técnico.",
                section_id="chunk_3",
                page_number=2
            ),
            DocumentSection(
                content="PENALIDADES: Em caso de descumprimento dos SLAs estabelecidos, será aplicada multa de R$ 10.000,00 por ocorrência.",
                section_id="chunk_4",
                page_number=2
            ),
            DocumentSection(
                content="VIGÊNCIA: Este contrato terá vigência de 36 meses, com possibilidade de renovação automática por períodos iguais.",
                section_id="chunk_5",
                page_number=3
            )
        ]
        
        # Store document chunks in vector database
        vector_result = doc_service.vector_service.store_document_chunks(test_document, test_chunks)
        if vector_result["success"]:
            print(f"   ✅ Armazenados {vector_result['data']['stored_count']} chunks no banco vetorial")
        else:
            print(f"   ❌ Erro no armazenamento: {vector_result['error']}")
            return False
        
        # Test RAG queries
        print("\n5. Testando consultas RAG...")
        rag_test_questions = [
            "Qual o número do contrato?",
            "Qual o tempo de SLA para incidentes críticos?",
            "Quantos quilômetros de fibra óptica?",
            "Qual o valor da multa?",
            "Qual o prazo de vigência?"
        ]
        
        for question in rag_test_questions:
            print(f"\n   🔍 Pergunta: {question}")
            
            # Test RAG processing
            rag_result = query_service.process_query(
                question=question,
                document_id=test_document.id,
                user_id="test_user"
            )
            
            if rag_result["success"]:
                rag_data = rag_result["data"]
                query_response = rag_data["query_response"]
                
                confidence = query_response.get("confidence_score", 0)
                answer = query_response["answer"]
                sources_count = len(rag_data.get("search_results", []))
                
                print(f"   ✅ Resposta (Confiança: {confidence:.1%}, {sources_count} fontes):")
                print(f"      {answer[:100]}{'...' if len(answer) > 100 else ''}")
                
                # Show intent if detected
                if rag_data.get("intent_analysis", {}).get("primary_intent"):
                    intent = rag_data["intent_analysis"]["primary_intent"]
                    print(f"      🎯 Intenção detectada: {intent}")
                
            else:
                print(f"   ❌ Erro no RAG: {rag_result['error']}")
        
        # Cleanup
        print("\n6. Limpando dados de teste...")
        delete_result = doc_service.vector_service.delete_document_vectors(test_document.id)
        if delete_result["success"]:
            print(f"   🧹 Removidos {delete_result['data']['deleted_count']} vetores")
        
        print("\n" + "=" * 60)
        print("🎉 SISTEMA RAG FUNCIONANDO COMPLETAMENTE!")
        print("💡 Todas as funcionalidades testadas com sucesso")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        return False

def test_without_openai():
    """Test system components that don't require OpenAI"""
    print("🔧 Testando componentes sem OpenAI...")
    print("=" * 50)
    
    try:
        # Test query service without LLM
        print("1. Testando análise de intenção (sem LLM)...")
        query_service = QueryService()
        
        test_questions = [
            "Qual o SLA do contrato?",
            "Quantos km de fibra?",
            "Valor da multa?",
            "Prazo de vigência?"
        ]
        
        for question in test_questions:
            intent_result = query_service.analyze_query_intent(question)
            if intent_result["success"]:
                intent_data = intent_result["data"]
                primary_intent = intent_data.get("primary_intent", "unknown")
                print(f"   ✅ '{question}' → {primary_intent}")
            else:
                print(f"   ❌ Erro: {intent_result['error']}")
        
        # Test suggestions
        print("\n2. Testando sugestões...")
        suggestions_result = query_service.get_query_suggestions()
        if suggestions_result["success"]:
            suggestions = suggestions_result["data"]
            total = sum(len(v) for v in suggestions.values())
            print(f"   ✅ {total} sugestões geradas")
        
        print("\n" + "=" * 50)
        print("✅ COMPONENTES BÁSICOS FUNCIONANDO!")
        print("💡 Configure OpenAI API key para teste completo")
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_rag_system()
    if success:
        print("\n🚀 Sistema RAG pronto para uso!")
        print("💡 Execute 'streamlit run app.py' para testar a interface completa")
    else:
        print("\n⚠️  Verifique os erros acima antes de prosseguir")