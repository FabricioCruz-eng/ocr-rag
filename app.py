"""
Main Streamlit application for LLM RAG Contract Analyzer
"""
import streamlit as st
import os
from pathlib import Path
from services.document_service import DocumentService
from models.document import Document

# Configure page
st.set_page_config(
    page_title="Analisador de Contratos LLM RAG",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
@st.cache_resource
def get_document_service():
    return DocumentService()

def main():
    """Main application function"""
    st.markdown("""
    <h1 style="font-size: 30px; color:#e9775d;">♾️ Analisador de Contratos Claro</h1>
""",unsafe_allow_html=True)
    st.markdown("Sistema de análise de contratos utilizando LLM - Large Language Models e RAG - Retrieval-Augmented Generation")
    
    
    # Initialize document service
    doc_service = get_document_service()
    
    # Initialize session state
    if 'uploaded_document' not in st.session_state:
        st.session_state.uploaded_document = None
    if 'upload_result' not in st.session_state:
        st.session_state.upload_result = None
    
    # Sidebar for configuration and document management
    with st.sidebar:
        st.header("🎡 Configuração")
        
        # Check if OpenAI API key is configured
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            st.error("⚠️ Configure sua chave da API OpenAI no arquivo .env")
            st.info("1. Copie .env.example para .env\n2. Adicione sua chave da OpenAI")
            return
        else:
            st.success("✅ API OpenAI configurada")
        
        st.markdown("---")
        
        # Document management
        st.header("📁 Documentos")
        
        # List existing documents
        docs_result = doc_service.list_documents()
        if docs_result["success"] and docs_result["data"]["count"] > 0:
            st.info(f"📊 {docs_result['data']['count']} arquivo(s) no sistema")
            
            with st.expander("Ver arquivos existentes"):
                for file_info in docs_result["data"]["files"]:
                    st.text(f"📄 {file_info['filename']}")
                    st.caption(f"Tamanho: {file_info['size']/1024:.1f} KB | Modificado: {file_info['modified'].strftime('%d/%m/%Y %H:%M')}")
        else:
            st.info("Nenhum documento encontrado")
    
    # Main content area
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("⚡ Upload do Documento")
        st.info("Faça upload de contratos em PDF, DOCX ou TXT para análise")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Escolha um arquivo",
            type=['pdf', 'docx', 'txt'],
            help="Tamanho máximo: 50MB"
        )
        
        if uploaded_file:
            # Display file information
            file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
            st.info(f"📄 **{uploaded_file.name}**")
            st.caption(f"Tamanho: {file_size_mb:.2f} MB | Tipo: {uploaded_file.type}")
            
            # Upload button
            if st.button("📤 Processar Upload", type="primary"):
                with st.spinner("Processando upload..."):
                    # Get file content
                    file_content = uploaded_file.getvalue()
                    
                    # Upload document
                    result = doc_service.upload_document(
                        file_content=file_content,
                        filename=uploaded_file.name,
                        user_id="default_user"
                    )
                    
                    # Store result in session state
                    st.session_state.upload_result = result
                    
                    if result["success"]:
                        st.success("✅ " + result["message"])
                        
                        # Process complete document (text + vectors)
                        with st.spinner("Processando documento (texto + vetorização)..."):
                            text_result = doc_service.process_document_complete(result["data"])
                            
                            if text_result["success"]:
                                st.session_state.uploaded_document = text_result["data"]["document"]
                                st.session_state.contract_info = text_result["data"]["contract_info"]
                                st.session_state.processing_stats = text_result["data"]["processing_stats"]
                                
                                st.success("✅ Texto extraído com sucesso!")
                                
                                # Display processing stats
                                stats = text_result["data"]["processing_stats"]
                                metadata = text_result["data"]["document"]["metadata"]
                                
                                st.info(f"📊 **Estatísticas**: {stats['total_chars']} caracteres, {stats['total_words']} palavras, {stats['total_chunks']} chunks")
                                
                                # Show OCR information if images were processed
                                if metadata.get("ocr_used"):
                                    st.success(f"🖼️ **OCR**: {metadata['images_processed']} imagem(ns) processada(s) com texto extraído!")
                                elif metadata.get("images_processed", 0) > 0:
                                    st.warning(f"🖼️ **Imagens**: {metadata.get('images_processed', 0)} imagem(ns) detectada(s) - Instale Tesseract para extrair texto")
                                
                                # Show PDF processing method
                                if metadata.get("fallback_used"):
                                    st.info("⚙️ **Processamento**: Método de fallback usado (PyPDF2)")
                                elif metadata.get("format") == "pdf":
                                    st.success("⚙️ **Processamento**: PyMuPDF usado (suporte completo a imagens)")
                                
                                # Display vector info if available
                                vector_info = text_result["data"].get("vector_info", {})
                                if vector_info.get("vectors_stored"):
                                    st.success(f"🔍 **Vetorização**: {vector_info['chunks_vectorized']} chunks vetorizados")
                                    st.session_state.vectors_available = True
                                else:
                                    st.warning("⚠️ **Vetorização falhou**: Busca semântica não disponível")
                                    st.session_state.vectors_available = False
                                
                                # Display contract info if found
                                contract_info = text_result["data"]["contract_info"]
                                if any(contract_info.values()):
                                    st.success("🔍 **Informações contratuais identificadas!**")
                                    
                                    col_info1, col_info2 = st.columns(2)
                                    with col_info1:
                                        if contract_info.get("contract_number"):
                                            st.caption(f"📄 Contrato: {contract_info['contract_number']}")
                                        if contract_info.get("sla_times"):
                                            st.caption(f"⏱️ SLA: {', '.join(contract_info['sla_times'])}")
                                    
                                    with col_info2:
                                        if contract_info.get("fiber_km"):
                                            st.caption(f"🔌 Fibra: {', '.join(contract_info['fiber_km'])}")
                                        if contract_info.get("penalty_values"):
                                            st.caption(f"💰 Multa: {', '.join(contract_info['penalty_values'])}")
                                
                                st.rerun()  # Refresh to update sidebar
                            else:
                                st.error("❌ Erro na extração de texto: " + text_result["error"])
                    else:
                        st.error("❌ " + result["error"])
        
        # Show current document status
        if st.session_state.uploaded_document:
            st.markdown("---")
            st.success("📄 Documento carregado e pronto!")
            doc = st.session_state.uploaded_document
            st.caption(f"ID: {doc['id'][:8]}... | Status: {doc['status']}")
    
    with col2:
        st.header("📒 Consulta ao Documento")
        
        if st.session_state.uploaded_document:
            # Show document content preview
            if hasattr(st.session_state, 'contract_info') and st.session_state.contract_info:
                with st.expander("🔍 Aguardando Pergunta para interação", expanded=True):
                    contract_info = st.session_state.contract_info
                    
                    if contract_info.get("contract_number"):
                        st.success(f"📄 **Número do Contrato**: {contract_info['contract_number']}")
                    
                    if contract_info.get("sla_times"):
                        st.info(f"⏱️ **Tempos de SLA**: {', '.join(contract_info['sla_times'])}")
                    
                    if contract_info.get("fiber_km"):
                        st.info(f"� **FibraR Óptica**: {', '.join(contract_info['fiber_km'])}")
                    
                    if contract_info.get("penalty_values"):
                        st.warning(f"💰 **Valores de Multa**: {', '.join(contract_info['penalty_values'])}")
                    
                    if contract_info.get("contract_duration"):
                        st.info(f"📅 **Duração do Contrato**: {', '.join(contract_info['contract_duration'])}")
            
            # Query interface
            question = st.text_input(
                "Faça uma pergunta sobre o contrato:",
                placeholder="Ex: Quero saber o número do contrato e trechos sobre SLA"
            )
            
            # Query analysis and suggestions
            if question and not st.button("▶️ Analisar"):
                # Show query intent analysis
                intent_result = doc_service.analyze_query_intent(question)
                if intent_result["success"]:
                    intent_data = intent_result["data"]
                    if intent_data.get("primary_intent"):
                        intent_emoji = {
                            "sla_query": "⏱️",
                            "fiber_query": "🔌", 
                            "penalty_query": "💰",
                            "duration_query": "📅",
                            "contract_info": "📄"
                        }
                        primary_intent = intent_data["primary_intent"]
                        emoji = intent_emoji.get(primary_intent, "🔍")
                        st.info(f"{emoji} **Detectei**: Pergunta sobre {primary_intent.replace('_', ' ')}")
            
            #if st.button("🔍 Analisar", key="analyze_button"):
                if question:
                    with st.spinner("Processando consulta com RAG (Retrieval-Augmented Generation)..."):
                        doc = st.session_state.uploaded_document
                        document_id = doc.get("id")
                        
                        # Check if vectors are available
                        vectors_available = getattr(st.session_state, 'vectors_available', False)
                        
                        if vectors_available and document_id:
                            # Use full RAG system
                            rag_result = doc_service.query_document(
                                document_id=document_id,
                                question=question,
                                user_id="default_user"
                            )
                            
                            st.markdown("### 🤖 Resposta RAG:")
                            st.markdown(f"**Pergunta:** {question}")
                            st.markdown("---")
                            
                            if rag_result["success"]:
                                rag_data = rag_result["data"]
                                query_response = rag_data["query_response"]
                                
                                # Show LLM-generated answer
                                confidence = query_response.get("confidence_score", 0.8)
                                confidence_color = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
                                
                                st.success(f"{confidence_color} **Resposta** (Confiança: {confidence:.1%}):")
                                st.markdown(query_response["answer"])
                                
                                # Show sources used
                                if rag_data.get("search_results"):
                                    with st.expander(f"📚 Fontes Consultadas ({len(rag_data['search_results'])} trechos)", expanded=False):
                                        for i, result in enumerate(rag_data["search_results"], 1):
                                            similarity = result["relevance_score"]
                                            metadata = result.get("metadata", {})
                                            page_num = metadata.get("page_number", 0)
                                            
                                            st.markdown(f"**Fonte {i}** - Relevância: {similarity:.1%}" + 
                                                      (f" (Página {page_num})" if page_num > 0 else ""))
                                            st.text(result["content"][:300] + "..." if len(result["content"]) > 300 else result["content"])
                                            st.markdown("---")
                                
                                # Show intent analysis if available
                                if rag_data.get("intent_analysis"):
                                    intent_data = rag_data["intent_analysis"]
                                    if intent_data.get("primary_intent"):
                                        st.info(f"🎯 **Tipo de consulta identificado**: {intent_data['primary_intent'].replace('_', ' ').title()}")
                                
                                # Show processing stats
                                st.caption(f"🔍 Processamento: {rag_data.get('total_results', 0)} chunks analisados | "
                                         f"{'LLM ativo' if not rag_data.get('fallback_mode') else 'Modo fallback'}")
                                
                            else:
                                st.error(f"❌ Erro no processamento RAG: {rag_result['error']}")
                                
                                # Fallback to simple search
                                st.warning("🔄 Tentando busca semântica simples...")
                                search_result = doc_service.search_document(
                                    document_id=document_id,
                                    query=question,
                                    top_k=3
                                )
                                
                                if search_result["success"] and search_result["data"]["results"]:
                                    results = search_result["data"]["results"]
                                    st.info(f"✅ Encontrei {len(results)} resultado(s) com busca semântica:")
                                    
                                    for i, result in enumerate(results, 1):
                                        similarity = result["relevance_score"]
                                        with st.expander(f"📄 Resultado {i} - Similaridade: {similarity:.1%}", expanded=i==1):
                                            st.text(result["content"].strip())
                        
                        else:
                            # Fallback to simple text search
                            st.warning("⚠️ Usando busca simples (vetores não disponíveis)")
                            
                            text_content = doc.get("text_content", "")
                            if text_content:
                                # Simple text search
                                question_lower = question.lower()
                                relevant_sections = []
                                lines = text_content.split('\n')
                                
                                for i, line in enumerate(lines):
                                    if any(keyword in line.lower() for keyword in question_lower.split()):
                                        # Get context (line before and after)
                                        start = max(0, i-1)
                                        end = min(len(lines), i+2)
                                        context = '\n'.join(lines[start:end])
                                        relevant_sections.append(context)
                                
                                st.markdown("### 📋 Resposta:")
                                st.markdown(f"**Pergunta:** {question}")
                                st.markdown("---")
                                
                                if relevant_sections:
                                    st.success("✅ Encontrei informações relevantes (busca simples):")
                                    
                                    for i, section in enumerate(relevant_sections[:3], 1):
                                        with st.expander(f"📄 Trecho {i}", expanded=i==1):
                                            st.text(section.strip())
                                else:
                                    st.warning("❌ Não encontrei informações específicas.")
                            else:
                                st.error("❌ Texto do documento não disponível")
                else:
                    st.warning("Por favor, digite uma pergunta")
        else:
            st.info("📤 Faça upload de um documento para começar a análise")
            
            # Show intelligent query suggestions
            st.markdown("### 💡 Sugestões de Consulta:")
            
            # Get query suggestions from service
            suggestions_result = doc_service.get_query_suggestions()
            if suggestions_result["success"]:
                suggestions = suggestions_result["data"]
                
                # Create tabs for different types of questions
                tab1, tab2, tab3, tab4 = st.tabs(["⏱️ SLA", "🔌 Fibra", "💰 Multas", "📅 Prazos"])
                
                with tab1:
                    for question in suggestions.get("sla_questions", []):
                        if st.button(question, key=f"sla_{question}"):
                            st.session_state.suggested_question = question
                
                with tab2:
                    for question in suggestions.get("fiber_questions", []):
                        if st.button(question, key=f"fiber_{question}"):
                            st.session_state.suggested_question = question
                
                with tab3:
                    for question in suggestions.get("penalty_questions", []):
                        if st.button(question, key=f"penalty_{question}"):
                            st.session_state.suggested_question = question
                
                with tab4:
                    for question in suggestions.get("duration_questions", []):
                        if st.button(question, key=f"duration_{question}"):
                            st.session_state.suggested_question = question
            else:
                # Fallback to static examples
                st.markdown("- *Qual o tempo de SLA definido no contrato?*")
                st.markdown("- *Quantos quilômetros de fibra estão inclusos?*")
                st.markdown("- *Qual o valor da multa por descumprimento?*")
                st.markdown("- *Qual o prazo de vigência do contrato?*")
    
    # Footer
    st.markdown("---")
    st.markdown("**Status**: ✅ Upload e validação | ✅ Extração de texto | ✅ Sistema RAG | 🤖🧑🏼‍💻 Análise de cláusulas")

if __name__ == "__main__":
    main()

st.markdown("""---""")
st.markdown("""

Automação desenvolvida e mantida por fabricio.cruz@claro.com.br
            
### Dados Utilizados

Os arquivos utilizados:

1. 🗃️ Repositório de contratos Swap Operadoras
2. 🔖 Roma""")

# Adicionando rodapé com informações de direitos autorais
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: white; background-color: #262730; padding: 10px;">
        Copyright © 2025 Todos os direitos reservados - Claro Brasil
    </div>
    """, 
    unsafe_allow_html=True
)     