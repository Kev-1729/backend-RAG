# Backend - Asistente de Trámites Municipales

API REST construida con **FastAPI** que implementa un sistema RAG (Retrieval Augmented Generation) para responder consultas sobre trámites municipales utilizando IA.

## 🚀 Tecnologías

- **FastAPI** - Framework web moderno y rápido
- **Python 3.11** - Lenguaje de programación
- **Google Gemini AI** - Modelos de embeddings y generación de texto
  - `text-embedding-004` - Embeddings de 768 dimensiones
  - `gemini-2.0-flash-exp` - Generación de respuestas
- **Supabase** - Base de datos PostgreSQL con soporte vectorial (pgvector)
- **pypdf** - Procesamiento de documentos PDF
- **Docker** - Containerización

## 📋 Requisitos Previos

- Python 3.11+
- Docker y Docker Compose (opcional)
- Cuenta de Supabase
- API Key de Google Gemini

## ⚙️ Configuración

### 1. Variables de Entorno

Crear archivo `.env` en el directorio `backend_python/`:

```env
# Supabase
SUPABASE_URL=tu_supabase_url
SUPABASE_KEY=tu_supabase_anon_key

# Google Gemini AI
GEMINI_API_KEY=tu_gemini_api_key
GEMINI_EMBEDDING_MODEL=text-embedding-004
GEMINI_CHAT_MODEL=gemini-2.0-flash-exp

# Servidor
HOST=0.0.0.0
PORT=8000
DEBUG=True

# RAG Configuration
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_SIMILARITY_THRESHOLD=0.4
RAG_TOP_K_RESULTS=5
```

### 2. Base de Datos Supabase

Ejecutar el script SQL en Supabase para crear las tablas:

```bash
# El archivo está en la raíz del proyecto
supabase_setup_768.sql
```

Este script crea:
- Tabla `documents` - Metadatos de documentos
- Tabla `document_chunks` - Chunks de texto con embeddings (768 dimensiones)
- Función `search_similar_chunks` - Búsqueda por similitud vectorial

## 🐳 Ejecución con Docker (Recomendado)

```bash
# Construir y ejecutar
docker-compose up --build

# En segundo plano
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

El servidor estará disponible en: `http://localhost:8000`

## 🐍 Ejecución Local (Desarrollo)

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar servidor
python main.py
```

El servidor estará disponible en: `http://localhost:8000`

## 📁 Estructura del Proyecto

```
backend_python/
├── app/
│   ├── core/              # Configuración y aplicación
│   │   ├── app.py         # Factory de FastAPI
│   │   └── config.py      # Settings con Pydantic
│   ├── api/               # Endpoints
│   │   └── rag_routes.py  # Rutas del RAG
│   ├── services/          # Lógica de negocio
│   │   ├── rag_service.py        # Procesamiento de queries
│   │   ├── embedding_service.py  # Generación de embeddings
│   │   └── pdf_processor.py      # Procesamiento de PDFs
│   ├── models/            # Schemas Pydantic
│   │   └── schemas.py
│   ├── utils/             # Utilidades
│   │   └── supabase_client.py
│   └── scripts/           # Scripts de utilidad
│       ├── process_pdfs.py    # Procesar PDFs en batch
│       └── clear_database.py  # Limpiar base de datos
├── main.py                # Punto de entrada
├── requirements.txt       # Dependencias Python
├── Dockerfile            # Imagen Docker
└── docker-compose.yml    # Orquestación Docker
```

## 📚 Endpoints de la API

### Health Check
```
GET /health
```

### Query RAG
```
POST /api/rag/query
Body: {
  "query": "¿Cómo solicito una licencia de funcionamiento?"
}
```

### Procesar PDF
```
POST /api/rag/process-pdf
Body: {
  "file_path": "/path/to/document.pdf",
  "filename": "document.pdf",
  "category": "comercio"
}
```

### Procesar Múltiples PDFs
```
POST /api/rag/process-batch
Body: {
  "file_paths": ["/path/to/doc1.pdf", "/path/to/doc2.pdf"],
  "category": "normativa"
}
```

### Estadísticas
```
GET /api/rag/stats
```

### Documentación Interactiva

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔄 Procesamiento de PDFs

### Procesar documentos en batch

1. Colocar PDFs en la carpeta `documentos_a_procesar/` (en la raíz del proyecto)

2. Ejecutar el script:

```bash
python -m app.scripts.process_pdfs
```

Este script:
- Detecta automáticamente el tipo de documento
- Aplica estrategia de chunking inteligente
- Genera embeddings con Gemini
- Almacena en Supabase

### Limpiar base de datos

```bash
python -m app.scripts.clear_database
```

## 🧠 Estrategia de Chunking Inteligente

El sistema utiliza 3 estrategias según el tipo de documento:

1. **Documentos pequeños (≤5 páginas)**: Sin división - mantiene coherencia completa
2. **Documentos legales**: División por artículos usando regex
3. **Documentos grandes**: División semántica por párrafos (max 1500 caracteres)

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=app
```

## 🔍 Logs

Los logs se muestran en formato:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Nivel de log configurado: `INFO`

## 📝 Notas Importantes

- Las embeddings son de **768 dimensiones** (Gemini text-embedding-004)
- El sistema usa **deduplicación por SHA256** para evitar procesar el mismo PDF dos veces
- El rate limiting de embeddings es de **100ms entre requests**
- El threshold de similitud por defecto es **0.4**
- Se recuperan los **top 5 chunks** más relevantes por query

## 🐛 Troubleshooting

### Error de conexión a Supabase
Verificar que `SUPABASE_URL` y `SUPABASE_KEY` sean correctos en `.env`

### Error de API de Gemini
Verificar que `GEMINI_API_KEY` sea válida y tenga cuota disponible

### Puerto 8000 ocupado
Cambiar `PORT` en `.env` o liberar el puerto 8000

## 📄 Licencia

Este proyecto es privado y pertenece a la Municipalidad de Carabayllo.
