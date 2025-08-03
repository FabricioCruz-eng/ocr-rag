"""
Query service for RAG (Retrieval-Augmented Generation) functionality
"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from openai import OpenAI

from services.base_service import BaseService
from services.vector_service import VectorService
from models.document import QueryResponse, DocumentSection
from config import config

class QueryService(BaseService):
    """Service for processing natural language queries using RAG"""
    
    def __init__(self):
        super().__init__()
        self.vector_service = VectorService()
        self.openai_client = None
        self._initialize_openai()
    
    def _initialize_openai(self):
        """Initialize OpenAI client"""
        try:
            if config.OPENAI_API_KEY:
                self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
                self.log_info("OpenAI client initialized successfully")
            else:
                self.log_warning("OpenAI API key not configured")
        except Exception as e:
            self.log_error(f"Failed to initialize OpenAI client: {str(e)}")
    
    def process_query(self, question: str, document_id: str, user_id: str = "default_user", top_k: int = 5) -> Dict[str, Any]:
        """
        Process a natural language query using RAG
        
        Args:
            question: User's natural language question
            document_id: Document ID to search within
            user_id: User identifier
            top_k: Number of relevant chunks to retrieve
            
        Returns:
            Dictionary with RAG response
        """
        try:
            # Step 1: Analyze query intent
            intent_analysis = self.analyze_query_intent(question)
            
            # Step 2: Perform semantic search
            search_result = self.vector_service.semantic_search(
                query=question,
                document_id=document_id,
                top_k=top_k
            )
            
            if not search_result["success"]:
                return search_result
            
            search_results = search_result["data"]["results"]
            
            # Step 3: Generate response using LLM
            if search_results and self.openai_client:
                response_result = self._generate_llm_response(question, search_results, intent_analysis)
                
                if response_result["success"]:
                    # Create QueryResponse object
                    query_response = QueryResponse(
                        question=question,
                        answer=response_result["data"]["answer"],
                        sources=[self._result_to_document_section(result) for result in search_results],
                        confidence_score=response_result["data"].get("confidence_score", 0.8)
                    )
                    
                    return self.success_response(
                        data={
                            "query_response": query_response.model_dump(),
                            "search_results": search_results,
                            "intent_analysis": intent_analysis["data"] if intent_analysis["success"] else {},
                            "total_results": len(search_results)
                        },
                        message="Consulta processada com sucesso usando RAG"
                    )
                else:
                    # Fallback to search results only
                    return self._create_fallback_response(question, search_results)
            else:
                # Fallback to search results only
                return self._create_fallback_response(question, search_results)
                
        except Exception as e:
            return self.handle_error(e, "query processing")
    
    def _generate_llm_response(self, question: str, search_results: List[Dict], intent_analysis: Dict) -> Dict[str, Any]:
        """
        Generate response using LLM based on retrieved context
        
        Args:
            question: User's question
            search_results: Retrieved relevant chunks
            intent_analysis: Query intent analysis
            
        Returns:
            Dictionary with LLM response
        """
        try:
            # Prepare context from search results
            context_chunks = []
            for i, result in enumerate(search_results[:3], 1):  # Use top 3 results
                relevance = result["relevance_score"]
                content = result["content"]
                metadata = result.get("metadata", {})
                page_num = metadata.get("page_number", 0)
                
                chunk_info = f"[Trecho {i} - Relevância: {relevance:.1%}"
                if page_num > 0:
                    chunk_info += f" - Página {page_num}"
                chunk_info += f"]\n{content}\n"
                
                context_chunks.append(chunk_info)
            
            context = "\n".join(context_chunks)
            
            # Create system prompt for contract analysis
            system_prompt = self._create_system_prompt(intent_analysis)
            
            # Create user prompt
            user_prompt = f"""
Pergunta do usuário: {question}

Contexto relevante do contrato:
{context}

Por favor, responda à pergunta baseando-se exclusivamente no contexto fornecido. Se a informação não estiver disponível no contexto, diga claramente que não foi possível encontrar essa informação no documento.

Inclua referências específicas aos trechos relevantes em sua resposta.
"""
            
            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more factual responses
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Calculate confidence score based on relevance scores
            avg_relevance = sum(r["relevance_score"] for r in search_results[:3]) / min(3, len(search_results))
            confidence_score = min(0.95, avg_relevance * 1.1)  # Boost slightly but cap at 95%
            
            self.log_info(f"LLM response generated successfully for query: {question[:50]}...")
            
            return self.success_response(
                data={
                    "answer": answer,
                    "confidence_score": confidence_score,
                    "context_used": len(context_chunks)
                },
                message="Resposta gerada com sucesso"
            )
            
        except Exception as e:
            return self.handle_error(e, "LLM response generation")
    
    def _create_system_prompt(self, intent_analysis: Dict) -> str:
        """Create system prompt based on query intent"""
        base_prompt = """Você é um assistente especializado em análise de contratos de operadoras de telecomunicações, com foco em:

- Tempos de SLA (Service Level Agreement)
- Extensão de fibra óptica em quilômetros
- Valores de multas e penalidades
- Prazos e vigência de contratos
- Cláusulas de rescisão e renovação

Instruções:
1. Responda sempre em português brasileiro
2. Base suas respostas EXCLUSIVAMENTE no contexto fornecido
3. Seja preciso e objetivo
4. Cite os trechos específicos quando relevante
5. Se a informação não estiver no contexto, diga claramente
6. Para valores monetários, mantenha o formato original (R$)
7. Para prazos, seja específico (horas, dias, meses, anos)
8. Destaque informações críticas como SLA e multas"""
        
        # Add specific guidance based on intent
        if intent_analysis.get("success") and intent_analysis.get("data"):
            intent_data = intent_analysis["data"]
            
            if intent_data.get("intent_type") == "sla_query":
                base_prompt += "\n\nFoco especial: Esta pergunta é sobre SLA. Procure por tempos de resposta, prazos de atendimento e níveis de serviço."
            elif intent_data.get("intent_type") == "fiber_query":
                base_prompt += "\n\nFoco especial: Esta pergunta é sobre fibra óptica. Procure por extensão em km, capacidade e especificações técnicas."
            elif intent_data.get("intent_type") == "penalty_query":
                base_prompt += "\n\nFoco especial: Esta pergunta é sobre multas e penalidades. Procure por valores monetários e condições de aplicação."
            elif intent_data.get("intent_type") == "duration_query":
                base_prompt += "\n\nFoco especial: Esta pergunta é sobre prazos e vigência. Procure por durações, datas de início/fim e condições de renovação."
        
        return base_prompt
    
    def _create_fallback_response(self, question: str, search_results: List[Dict]) -> Dict[str, Any]:
        """Create fallback response when LLM is not available"""
        if search_results:
            # Create simple response based on search results
            answer = f"Encontrei {len(search_results)} trecho(s) relevante(s) no documento:\n\n"
            
            for i, result in enumerate(search_results[:3], 1):
                relevance = result["relevance_score"]
                content = result["content"][:200] + "..." if len(result["content"]) > 200 else result["content"]
                answer += f"{i}. (Relevância: {relevance:.1%})\n{content}\n\n"
            
            confidence_score = max(r["relevance_score"] for r in search_results) if search_results else 0.5
        else:
            answer = "Não encontrei informações relevantes no documento para responder sua pergunta."
            confidence_score = 0.0
        
        query_response = QueryResponse(
            question=question,
            answer=answer,
            sources=[self._result_to_document_section(result) for result in search_results],
            confidence_score=confidence_score
        )
        
        return self.success_response(
            data={
                "query_response": query_response.model_dump(),
                "search_results": search_results,
                "total_results": len(search_results),
                "fallback_mode": True
            },
            message="Consulta processada usando busca semântica (sem LLM)"
        )
    
    def _result_to_document_section(self, result: Dict) -> DocumentSection:
        """Convert search result to DocumentSection"""
        metadata = result.get("metadata", {})
        
        return DocumentSection(
            content=result["content"],
            page_number=metadata.get("page_number"),
            section_id=metadata.get("chunk_id", "unknown"),
            relevance_score=result["relevance_score"]
        )
    
    def analyze_query_intent(self, question: str) -> Dict[str, Any]:
        """
        Analyze the intent of a user query
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with intent analysis
        """
        try:
            question_lower = question.lower()
            
            # Define intent patterns
            intent_patterns = {
                "sla_query": [
                    r'\bsla\b', r'tempo.*resposta', r'prazo.*atendimento', 
                    r'nivel.*serviço', r'disponibilidade', r'uptime'
                ],
                "fiber_query": [
                    r'\bfibra\b', r'\bkm\b', r'quilometr', r'extensão', 
                    r'rede', r'cabo', r'infraestrutura'
                ],
                "penalty_query": [
                    r'\bmulta\b', r'penalidade', r'sanção', r'valor.*multa',
                    r'descumprimento', r'infração'
                ],
                "duration_query": [
                    r'\bprazo\b', r'vigência', r'duração', r'período',
                    r'renovação', r'vencimento', r'término'
                ],
                "contract_info": [
                    r'número.*contrato', r'contrato.*n', r'identificação',
                    r'partes', r'contratante', r'contratada'
                ]
            }
            
            # Analyze intent
            detected_intents = []
            confidence_scores = {}
            
            for intent_type, patterns in intent_patterns.items():
                matches = 0
                for pattern in patterns:
                    if re.search(pattern, question_lower):
                        matches += 1
                
                if matches > 0:
                    confidence = min(1.0, matches / len(patterns) * 2)  # Boost confidence
                    detected_intents.append(intent_type)
                    confidence_scores[intent_type] = confidence
            
            # Determine primary intent
            primary_intent = None
            if detected_intents:
                primary_intent = max(detected_intents, key=lambda x: confidence_scores[x])
            
            # Extract key entities
            entities = self._extract_entities(question)
            
            intent_data = {
                "primary_intent": primary_intent,
                "all_intents": detected_intents,
                "confidence_scores": confidence_scores,
                "entities": entities,
                "question_type": self._classify_question_type(question)
            }
            
            return self.success_response(
                data=intent_data,
                message="Análise de intenção concluída"
            )
            
        except Exception as e:
            return self.handle_error(e, "query intent analysis")
    
    def _extract_entities(self, question: str) -> Dict[str, List[str]]:
        """Extract entities from question"""
        entities = {
            "numbers": [],
            "time_units": [],
            "monetary_values": [],
            "contract_refs": []
        }
        
        # Extract numbers
        numbers = re.findall(r'\b\d+(?:[.,]\d+)?\b', question)
        entities["numbers"] = numbers
        
        # Extract time units
        time_units = re.findall(r'\b\d+\s*(horas?|dias?|meses?|anos?|minutos?)\b', question.lower())
        entities["time_units"] = time_units
        
        # Extract monetary values
        monetary = re.findall(r'R\$\s*\d+(?:[.,]\d+)*', question)
        entities["monetary_values"] = monetary
        
        # Extract contract references
        contract_refs = re.findall(r'contrato\s*n?[°º]?\s*[\w\-/]+', question.lower())
        entities["contract_refs"] = contract_refs
        
        return entities
    
    def _classify_question_type(self, question: str) -> str:
        """Classify the type of question"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['qual', 'quais', 'que', 'o que']):
            return "what"
        elif any(word in question_lower for word in ['quanto', 'quantos', 'quantas']):
            return "how_much"
        elif any(word in question_lower for word in ['quando', 'que horas', 'que dia']):
            return "when"
        elif any(word in question_lower for word in ['onde', 'em que local']):
            return "where"
        elif any(word in question_lower for word in ['como', 'de que forma']):
            return "how"
        elif any(word in question_lower for word in ['por que', 'porque', 'motivo']):
            return "why"
        else:
            return "general"
    
    def get_query_suggestions(self, document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get suggested queries for a document
        
        Args:
            document_id: Optional document ID
            
        Returns:
            Dictionary with query suggestions
        """
        try:
            # Base suggestions for contract analysis
            suggestions = {
                "sla_questions": [
                    "Qual o tempo de SLA definido no contrato?",
                    "Quais são os prazos de atendimento para incidentes?",
                    "Qual o nível de disponibilidade garantido?"
                ],
                "fiber_questions": [
                    "Quantos quilômetros de fibra óptica estão inclusos?",
                    "Qual a extensão da rede contratada?",
                    "Quais as especificações técnicas da fibra?"
                ],
                "penalty_questions": [
                    "Qual o valor da multa por descumprimento?",
                    "Quais são as penalidades previstas?",
                    "Em que situações se aplicam multas?"
                ],
                "duration_questions": [
                    "Qual o prazo de vigência do contrato?",
                    "Quando o contrato pode ser renovado?",
                    "Qual a duração mínima do acordo?"
                ],
                "general_questions": [
                    "Qual o número do contrato?",
                    "Quem são as partes contratantes?",
                    "Quais os principais termos do acordo?"
                ]
            }
            
            # If document_id is provided, could customize suggestions based on document content
            # For now, return all suggestions
            
            return self.success_response(
                data=suggestions,
                message="Sugestões de consulta geradas"
            )
            
        except Exception as e:
            return self.handle_error(e, "query suggestions")
    
    def get_query_history(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get query history for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of queries to return
            
        Returns:
            Dictionary with query history
        """
        try:
            # This would typically query a database
            # For now, return empty history
            history = []
            
            return self.success_response(
                data={
                    "history": history,
                    "total_queries": len(history),
                    "user_id": user_id
                },
                message="Histórico de consultas recuperado"
            )
            
        except Exception as e:
            return self.handle_error(e, "query history retrieval")