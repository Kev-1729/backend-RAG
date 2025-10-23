"""
RAG (Retrieval Augmented Generation) service
Handles query processing and answer generation using vector similarity search
"""
import google.generativeai as genai
from typing import List, Dict, Any, Optional
import logging
from app.core.config import settings
from app.utils.supabase_client import supabase
from app.services.embedding_service import get_embedding_service
from app.models.schemas import QueryResponse

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-based question answering"""

    def __init__(self):
        """Initialize RAG service"""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.embedding_service = get_embedding_service()
        self.model_name = settings.GEMINI_CHAT_MODEL
        logger.info(f"RAGService initialized with model: {self.model_name}")

    async def query(self, query: str) -> QueryResponse:
        """
        Process a user query and generate an answer using RAG

        Args:
            query: User's question

        Returns:
            QueryResponse with answer and metadata
        """
        logger.info(f"\n{'='*50}")
        logger.info(f"[STEP 1] User query: '{query}'")

        try:
            # Detectar comandos especiales
            query_lower = query.lower().strip()

            # 1. Ayuda general
            help_keywords = ['ayuda', 'ayúdame', 'qué puedes hacer', 'que puedes hacer',
                           'qué temas', 'que temas', 'sobre qué', 'sobre que',
                           'de qué', 'de que', 'help', 'opciones', 'menú', 'menu']

            if any(keyword in query_lower for keyword in help_keywords):
                logger.info("[HELP] Help message requested")
                return QueryResponse(
                    answer="""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; margin-bottom: 15px;">
                        <h2 style="margin: 0 0 10px 0; font-size: 24px;">Asistente de Trámites Municipales</h2>
                        <p style="margin: 0; opacity: 0.9;">Tu guía inteligente para procedimientos del municipio</p>
                    </div>

                    <p><strong>📋 CONSULTAS FRECUENTES</strong></p>
                    <p>Haz clic o escribe una de estas opciones para obtener ayuda rápida:</p>

                    <div style="display: grid; gap: 10px; margin: 15px 0;">
                        <div style="background: #f0f9ff; padding: 12px; border-radius: 8px; border-left: 4px solid #3b82f6;">
                            <strong>1️⃣ Preguntas Frecuentes - Preguntas Frecuentes</strong><br/>
                            <em style="color: #64748b;">Consultas más comunes sobre trámites</em>
                        </div>

                        <div style="background: #fef3c7; padding: 12px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                            <strong>2️⃣ Ayuda con el RAG</strong><br/>
                            <em style="color: #64748b;">Aprende a hacer mejores preguntas</em>
                        </div>

                        <div style="background: #f0fdf4; padding: 12px; border-radius: 8px; border-left: 4px solid #10b981;">
                            <strong>3️⃣ Temas disponibles</strong><br/>
                            <em style="color: #64748b;">Lista de todos los temas que manejo</em>
                        </div>
                    </div>

                    <p style="margin-top: 20px;"><strong>💡 Ejemplos de preguntas directas:</strong></p>
                    <ul style="line-height: 1.8;">
                        <li>"¿Cómo saco una licencia de funcionamiento para una bodega?"</li>
                        <li>"¿Qué requisitos necesito para comercio ambulatorio?"</li>
                        <li>"¿Cuánto cuesta una licencia provisional?"</li>
                        <li>"¿Dónde descargo el formato de solicitud?"</li>
                    </ul>

                    <p style="background: #fef2f2; padding: 10px; border-radius: 6px; border-left: 3px solid #ef4444;">
                        ⚠️ <strong>Importante:</strong> Solo puedo responder preguntas sobre trámites municipales basándome en los documentos oficiales cargados.
                    </p>
                    """,
                    document_name="Sistema de Ayuda",
                    sources=[]
                )

            # 2. FAQ - Preguntas Frecuentes
            if 'faq' in query_lower or 'preguntas frecuentes' in query_lower or 'consultas frecuentes' in query_lower:
                logger.info("[FAQ] Frequently asked questions requested")
                return QueryResponse(
                    answer="""
                    <h3 style="color: #3b82f6; margin-bottom: 15px;">Preguntas Frecuentes</h3>

                    <details style="margin-bottom: 15px; padding: 12px; background: #f8fafc; border-radius: 8px;">
                        <summary style="cursor: pointer; font-weight: bold; color: #1e40af;">¿Qué tipos de licencias puedo solicitar?</summary>
                        <p style="margin-top: 10px; padding-left: 10px;">Puedes solicitar licencias de funcionamiento (bodegas, restaurantes, comercios), permisos de construcción, autorizaciones de comercio ambulatorio, y más. Pregúntame específicamente sobre el tipo que necesitas.</p>
                    </details>

                    <details style="margin-bottom: 15px; padding: 12px; background: #f8fafc; border-radius: 8px;">
                        <summary style="cursor: pointer; font-weight: bold; color: #1e40af;">¿Cuánto demora una licencia de funcionamiento?</summary>
                        <p style="margin-top: 10px; padding-left: 10px;">Los tiempos varían según el tipo de licencia. Pregúntame específicamente sobre la licencia que necesitas para darte información precisa sobre plazos.</p>
                    </details>

                    <details style="margin-bottom: 15px; padding: 12px; background: #f8fafc; border-radius: 8px;">
                        <summary style="cursor: pointer; font-weight: bold; color: #1e40af;">¿Qué documentos necesito presentar?</summary>
                        <p style="margin-top: 10px; padding-left: 10px;">Los requisitos dependen del trámite. Pregúntame sobre el trámite específico (ejemplo: "requisitos para licencia de bodega") para obtener la lista completa.</p>
                    </details>

                    <details style="margin-bottom: 15px; padding: 12px; background: #f8fafc; border-radius: 8px;">
                        <summary style="cursor: pointer; font-weight: bold; color: #1e40af;">¿Dónde descargo los formularios?</summary>
                        <p style="margin-top: 10px; padding-left: 10px;">Pregúntame sobre el formulario específico que necesitas (ejemplo: "formato de licencia de bodega") y te indicaré dónde encontrarlo.</p>
                    </details>

                    <details style="margin-bottom: 15px; padding: 12px; background: #f8fafc; border-radius: 8px;">
                        <summary style="cursor: pointer; font-weight: bold; color: #1e40af;">¿Cuáles son los costos de los trámites?</summary>
                        <p style="margin-top: 10px; padding-left: 10px;">Los costos varían según el tipo de trámite y categoría. Consulta específicamente sobre el trámite que te interesa.</p>
                    </details>

                    <p style="margin-top: 20px; padding: 12px; background: #dbeafe; border-radius: 8px;">
                        <strong>💬 ¿No encontraste tu pregunta?</strong><br/>
                        Escríbela directamente y te ayudaré con la información disponible.
                    </p>
                    """,
                    document_name="Preguntas Frecuentes",
                    sources=[]
                )

            # 3. Ayuda con el RAG
            if 'ayuda con el rag' in query_lower or 'como preguntar' in query_lower or 'cómo preguntar' in query_lower or 'mejores preguntas' in query_lower:
                logger.info("[RAG_HELP] RAG usage help requested")
                return QueryResponse(
                    answer="""
                    <h3 style="color: #f59e0b; margin-bottom: 15px;">🤖 Cómo usar el Asistente RAG</h3>

                    <div style="background: #fffbeb; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b; margin-bottom: 15px;">
                        <strong>¿Qué es RAG?</strong>
                        <p>RAG (Retrieval Augmented Generation) significa que busco información en documentos oficiales y genero respuestas basadas en esos datos reales.</p>
                    </div>

                    <h4 style="color: #10b981; margin-top: 20px;">✅ Consejos para mejores resultados:</h4>

                    <div style="background: #f0fdf4; padding: 12px; border-radius: 8px; margin: 10px 0;">
                        <strong>1. Sé específico</strong>
                        <ul>
                            <li>❌ Malo: "Necesito una licencia"</li>
                            <li>✅ Bueno: "¿Qué requisitos necesito para una licencia de bodega?"</li>
                        </ul>
                    </div>

                    <div style="background: #f0fdf4; padding: 12px; border-radius: 8px; margin: 10px 0;">
                        <strong>2. Usa palabras clave relacionadas</strong>
                        <ul>
                            <li>✅ "licencia", "permiso", "requisitos", "formulario", "trámite"</li>
                            <li>✅ "bodega", "restaurante", "comercio", "ambulante"</li>
                        </ul>
                    </div>

                    <div style="background: #f0fdf4; padding: 12px; border-radius: 8px; margin: 10px 0;">
                        <strong>3. Haz preguntas directas</strong>
                        <ul>
                            <li>✅ "¿Cómo saco...?"</li>
                            <li>✅ "¿Qué necesito para...?"</li>
                            <li>✅ "¿Cuánto cuesta...?"</li>
                            <li>✅ "¿Dónde encuentro...?"</li>
                        </ul>
                    </div>

                    <div style="background: #f0fdf4; padding: 12px; border-radius: 8px; margin: 10px 0;">
                        <strong>4. Una pregunta a la vez</strong>
                        <ul>
                            <li>❌ Malo: "¿Cómo saco licencia, cuánto cuesta y dónde la tramito?"</li>
                            <li>✅ Bueno: "¿Cómo saco una licencia de funcionamiento?" (luego pregunta el costo)</li>
                        </ul>
                    </div>

                    <h4 style="color: #ef4444; margin-top: 20px;">❌ Lo que NO puedo hacer:</h4>
                    <ul style="background: #fef2f2; padding: 15px; border-radius: 8px;">
                        <li>Responder preguntas fuera del ámbito municipal</li>
                        <li>Inventar información que no esté en los documentos</li>
                        <li>Procesar solicitudes o trámites directamente</li>
                        <li>Acceder a información personal o expedientes</li>
                    </ul>

                    <div style="background: #dbeafe; padding: 15px; border-radius: 8px; margin-top: 20px;">
                        <strong>💡 Tip Pro:</strong> Si no obtienes una buena respuesta, reformula tu pregunta de manera más específica o usa sinónimos.
                    </div>
                    """,
                    document_name="Guía de Uso del RAG",
                    sources=[]
                )

            # 4. Temas disponibles
            if 'temas disponibles' in query_lower or 'temas que manejas' in query_lower or 'sobre qué sabes' in query_lower:
                logger.info("[TOPICS] Available topics requested")
                return QueryResponse(
                    answer="""
                    <h3 style="color: #10b981; margin-bottom: 15px;">📚 Temas Disponibles</h3>

                    <div style="display: grid; gap: 12px;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 15px; border-radius: 8px; color: white;">
                            <strong style="font-size: 18px;">🏪 Licencias de Funcionamiento</strong>
                            <ul style="margin: 10px 0 0 20px; opacity: 0.95;">
                                <li>Licencias para bodegas</li>
                                <li>Licencias para restaurantes</li>
                                <li>Licencias para comercios en general</li>
                                <li>Licencias provisionales</li>
                            </ul>
                        </div>

                        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 15px; border-radius: 8px; color: white;">
                            <strong style="font-size: 18px;">🛒 Comercio y Permisos</strong>
                            <ul style="margin: 10px 0 0 20px; opacity: 0.95;">
                                <li>Autorización de comercio ambulatorio</li>
                                <li>Permisos de eventos</li>
                                <li>Ocupación de vía pública</li>
                            </ul>
                        </div>

                        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 15px; border-radius: 8px; color: white;">
                            <strong style="font-size: 18px;">📋 Documentación y Requisitos</strong>
                            <ul style="margin: 10px 0 0 20px; opacity: 0.95;">
                                <li>Formularios oficiales</li>
                                <li>Requisitos por tipo de trámite</li>
                                <li>Documentos necesarios</li>
                            </ul>
                        </div>

                        <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 15px; border-radius: 8px; color: white;">
                            <strong style="font-size: 18px;">⚖️ Normativa Legal</strong>
                            <ul style="margin: 10px 0 0 20px; opacity: 0.95;">
                                <li>Ordenanzas municipales</li>
                                <li>Leyes aplicables</li>
                                <li>Decretos y reglamentos</li>
                            </ul>
                        </div>

                        <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 15px; border-radius: 8px; color: #1f2937;">
                            <strong style="font-size: 18px;">⏱️ Procedimientos Administrativos</strong>
                            <ul style="margin: 10px 0 0 20px;">
                                <li>Plazos de aprobación</li>
                                <li>Costos y tasas</li>
                                <li>Pasos del trámite</li>
                            </ul>
                        </div>
                    </div>

                    <p style="margin-top: 20px; padding: 15px; background: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b;">
                        <strong>📌 Nota:</strong> La información disponible depende de los documentos oficiales que han sido cargados al sistema. Si no encuentro información sobre un tema, te lo indicaré.
                    </p>
                    """,
                    document_name="Catálogo de Temas",
                    sources=[]
                )

            # 1. Generate embedding for the query
            query_embedding = await self.embedding_service.generate_query_embedding(query)
            logger.info(f"[STEP 2] Query embedding generated (Dimensions: {len(query_embedding)})")

            # 2. Search for similar chunks in Supabase using vector similarity
            logger.info("[STEP 3] Searching for similar chunks in Supabase...")
            chunks = await self._search_similar_chunks(
                query_embedding,
                threshold=settings.RAG_SIMILARITY_THRESHOLD,
                limit=settings.RAG_TOP_K_RESULTS
            )

            if not chunks:
                logger.warning("[RESULT] No relevant chunks found in database")
                return QueryResponse(
                    answer="<p>Lo siento, no encontré información específica en mis documentos sobre tu consulta.</p><p>Si tu pregunta está relacionada con trámites municipales, te recomiendo:</p><ul><li>Reformular tu pregunta de manera más específica</li><li>Contactar directamente con la municipalidad</li><li>Verificar que la información esté disponible en los documentos cargados</li></ul>",
                    document_name=None,
                    sources=[]
                )

            logger.info(f"[RESULT] Found {len(chunks)} relevant chunks")
            logger.info(f"Most relevant document: {chunks[0].get('filename', 'Unknown')}")

            # 3. Build context from retrieved chunks
            context = self._build_context(chunks)

            # 4. Generate answer using Gemini
            logger.info("[STEP 4] Generating answer with Gemini...")
            answer = await self._generate_answer(query, context)

            logger.info("[STEP 5] Answer generated successfully")

            # Extract unique source documents
            sources = list(set([chunk.get('filename') for chunk in chunks if chunk.get('filename')]))

            return QueryResponse(
                answer=answer,
                document_name=chunks[0].get('filename', 'Desconocido'),
                sources=sources
            )

        except Exception as e:
            logger.error(f"[ERROR] RAG query failed: {e}", exc_info=True)
            return QueryResponse(
                answer='<p class="text-red-600">Ocurrió un error interno al procesar tu solicitud.</p>',
                document_name="",
                sources=[]
            )

    async def _search_similar_chunks(
        self,
        query_embedding: List[float],
        threshold: float = 0.4,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar document chunks using vector similarity

        Args:
            query_embedding: Query embedding vector
            threshold: Similarity threshold
            limit: Maximum number of results

        Returns:
            List of matching chunks with metadata
        """
        try:
            response = supabase.rpc(
                'search_similar_chunks',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': limit
                }
            ).execute()

            if response.data:
                return response.data
            return []

        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            raise

    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Build context string from retrieved chunks

        Args:
            chunks: List of document chunks

        Returns:
            Formatted context string
        """
        context_parts = []
        for chunk in chunks:
            chunk_text = chunk.get('chunk_text', '')
            filename = chunk.get('filename', 'Unknown')
            context_parts.append(f"[Fuente: {filename}]\n{chunk_text}")

        return "\n\n---\n\n".join(context_parts)

    async def _generate_answer(self, query: str, context: str) -> str:
        """
        Generate answer using Gemini with provided context

        Args:
            query: User's question
            context: Retrieved context from documents

        Returns:
            Generated answer text
        """
        prompt = f"""
Eres un asistente virtual experto en trámites de la Municipalidad de Carabayllo.
Tu objetivo es ayudar a los ciudadanos a entender los procedimientos y requisitos para realizar trámites municipales.

IMPORTANTE: SOLO puedes responder preguntas relacionadas con trámites municipales, licencias, permisos, ordenanzas y procedimientos del municipio.

Analiza la pregunta del usuario:
1. Si la pregunta NO está relacionada con trámites municipales (por ejemplo: matemáticas, recetas de cocina, deportes, entretenimiento, etc.), responde:
   "<p>Lo siento, solo puedo ayudarte con consultas relacionadas a <strong>trámites municipales</strong>. Por favor, pregúntame sobre licencias, permisos, requisitos o procedimientos del municipio.</p>"

2. Si la pregunta SÍ está relacionada con trámites municipales, responde basándote ÚNICAMENTE en el contexto proporcionado.

INSTRUCCIONES PARA RESPUESTAS VÁLIDAS:
- Usa un lenguaje claro y amigable
- Estructura la respuesta con HTML simple (párrafos <p>, listas <ul>, <ol>, negrita <strong>)
- Si la información no está en el contexto, indica claramente que no tienes esa información
- Menciona los documentos fuente cuando sea relevante
- Si hay pasos o requisitos, preséntalos en una lista ordenada

CONTEXTO DE DOCUMENTOS MUNICIPALES:
{context}

PREGUNTA DEL USUARIO: {query}

RESPUESTA:
""".strip()

        try:
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Error generating answer with Gemini: {e}")
            raise


# Singleton instance
_rag_service: RAGService = None


def get_rag_service() -> RAGService:
    """Get singleton RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
