from fastapi import APIRouter

from app.config import get_settings
from app.domain.languages import display_map
from app.infrastructure.llm.ollama_client import OllamaClient
from app.schemas.translation_schemas import HealthResponse, ModeInfo

router = APIRouter(prefix="/api", tags=["meta"])


_MODES = [
    ModeInfo(
        id="pipeline",
        name="Pipeline LLM",
        description="Flujo fijo: detect -> prompt -> LLM -> stream. El codigo decide todo.",
        streams_tokens=True,
        streams_steps=False,
    ),
    ModeInfo(
        id="monoagent",
        name="Mono-agente ReAct",
        description="LangChain ReAct: el LLM elige que tool usar en cada iteracion.",
        streams_tokens=False,
        streams_steps=True,
    ),
    ModeInfo(
        id="multiagent",
        name="Multi-agente orquestado",
        description="Cuatro agentes especializados coordinados por un orquestador secuencial.",
        streams_tokens=False,
        streams_steps=True,
    ),
]


@router.get("/languages")
def get_languages():
    return display_map()


@router.get("/modes", response_model=list[ModeInfo])
def get_modes():
    return _MODES


@router.get("/health", response_model=HealthResponse)
async def health():
    settings = get_settings()
    client = OllamaClient()
    try:
        models = await client.list_models()
        return HealthResponse(
            status="ok",
            model=settings.llm_model,
            ollama_reachable=True,
            available_models=models,
        )
    except Exception:
        return HealthResponse(
            status="degraded",
            model=settings.llm_model,
            ollama_reachable=False,
            available_models=[],
        )
