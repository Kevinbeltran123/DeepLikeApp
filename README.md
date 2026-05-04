# DeepLikeApp

Traductor estilo DeepL implementado en tres arquitecturas comparables sobre un mismo backend y frontend. El objetivo es contrastar cómo cambia el código (y no solo el resultado) cuando se pasa de un *pipeline* fijo a un *mono-agente* con bucle ReAct y luego a un *multi-agente* con orquestador.

Modelo: **Qwen 2.5 14B** corriendo localmente vía **Ollama**. Sin claves de API, sin red.

---

## Arquitectura

```
┌─────────────────┐         SSE          ┌──────────────────────────────┐
│    Frontend     │ ◄─────────────────── │           Backend            │
│  React + Vite   │                      │           FastAPI            │
│                 │  POST /api/<mode>    │                              │
│  ModeSelector   │ ───────────────────► │  /api/pipeline/translate     │
│   - pipeline    │                      │  /api/monoagent/translate    │
│   - monoagent   │                      │  /api/multiagent/translate   │
│   - multiagent  │                      │                              │
│                 │                      │  modes/                      │
│  AgentTrace     │                      │   ├ pipeline/                │
│  (modos 2 y 3)  │                      │   ├ monoagent/  (LangChain)  │
└─────────────────┘                      │   └ multiagent/ (4 agentes)  │
                                         └───────────────┬──────────────┘
                                                         │
                                                  ┌──────▼──────┐
                                                  │   Ollama    │
                                                  │  Qwen 2.5   │
                                                  └─────────────┘
```

Los tres modos viven en `backend/app/modes/` como módulos hermanos. Comparten infraestructura (cliente Ollama, detector de idioma, registro de idiomas) pero cada uno es legible en aislamiento — abrir `pipeline/translator.py` muestra el flujo completo sin tener que leer abstracciones compartidas.

### Diferencias clave entre modos

| | Pipeline | Mono-agente | Multi-agente |
|---|---|---|---|
| Quién decide el orden | El código | El LLM (ReAct) | El orquestador (código) |
| LLMs involucrados | 1 | 1 (en bucle) | 2-3 (un agente por rol) |
| Streaming | Token a token | Pasos del bucle | Pasos por agente |
| Extensibilidad | Editar el código | Añadir un `@tool` | Añadir un agente |
| Predecibilidad | Total | Variable (autonomía) | Total (orden fijo) |

---

## Estructura

```
DeepLikeApp/
├── backend/
│   ├── app/
│   │   ├── main.py                composition root FastAPI
│   │   ├── config.py              settings via pydantic-settings
│   │   ├── domain/                tipos puros (sin framework)
│   │   ├── infrastructure/        Ollama client, langdetect
│   │   ├── modes/
│   │   │   ├── pipeline/          flujo fijo
│   │   │   ├── monoagent/         LangChain ReAct + tools
│   │   │   └── multiagent/        orquestador + 4 agentes
│   │   ├── api/routes/            endpoints HTTP
│   │   └── schemas/               Pydantic request/response
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── components/            UI (ModeSelector, AgentTrace, ...)
        ├── hooks/                 useTranslationStream, useLanguages
        ├── services/              cliente HTTP + parser SSE
        ├── types/                 contrato de eventos espejo del backend
        └── styles/                CSS global
```

---

## Requisitos

- Python 3.12 (LangChain 0.3 todavía no es compatible con Python 3.14)
- Node.js 20+ y npm
- Ollama con el modelo `qwen2.5:14b` (o ajusta `LLM_MODEL` en `.env`)

```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Descargar Qwen
ollama pull qwen2.5:14b

# Verificar
ollama run qwen2.5:14b "Hola"
```

---

## Setup

```bash
make setup
```

Equivalente manual:

```bash
# Backend
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Frontend
cd ../frontend
npm install
```

## Ejecución

En dos terminales:

```bash
# Terminal 1 — backend
make backend
# o: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
make frontend
# o: cd frontend && npm run dev
```

Abrir http://localhost:5173

---

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET  | `/api/health` | Estado del backend y Ollama |
| GET  | `/api/languages` | Mapa código → nombre nativo |
| GET  | `/api/modes` | Información de los tres modos |
| POST | `/api/pipeline/translate` | Stream SSE — pipeline fijo |
| POST | `/api/monoagent/translate` | Stream SSE — bucle ReAct |
| POST | `/api/multiagent/translate` | Stream SSE — orquestador 4 agentes |

Todos los endpoints de traducción aceptan:

```json
{ "text": "...", "source_lang": "auto", "target_lang": "en" }
```

Y emiten eventos SSE definidos en [`backend/app/domain/events.py`](backend/app/domain/events.py) (espejo en [`frontend/src/types/events.ts`](frontend/src/types/events.ts)).

### Ejemplo con curl

```bash
curl -N -X POST http://localhost:8000/api/multiagent/translate \
  -H 'Content-Type: application/json' \
  -d '{"text":"El paciente presenta diagnostico cronico","target_lang":"en"}'
```

---

## Personalización

Hay tres puntos donde tu criterio cambia el comportamiento (todos marcados con `TODO(student)` en el código):

1. **Prompts del traductor** — registro formal/casual, estricto/permisivo
   - `backend/app/modes/pipeline/prompt_builder.py`
   - `backend/app/modes/multiagent/agents/translator_agent.py`

2. **Diccionarios de dominio** — qué dominios y términos identifica el `Terminologo`
   - `backend/app/modes/multiagent/agents/terminology_agent.py`
   - `backend/app/modes/monoagent/tools.py` (`_DOMAIN_TERMS`)

3. **Umbrales de calidad** — qué considera "traducción aceptable" el revisor
   - `backend/app/modes/multiagent/agents/reviewer_agent.py` (`_MIN_LENGTH_RATIO`, `_MAX_LENGTH_RATIO`)
   - `backend/app/modes/monoagent/tools.py` (`check_translation_quality`)

---

## Variables de entorno

`backend/.env`:

```
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=qwen2.5:14b
LLM_TEMPERATURE=0.1
LLM_TIMEOUT_SECONDS=180
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:4173
```
