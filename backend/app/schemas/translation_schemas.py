from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    source_lang: str = Field(default="auto", description="ISO code or 'auto' for detection")
    target_lang: str = Field(default="en", description="ISO code of target language")


class HealthResponse(BaseModel):
    status: str
    model: str
    ollama_reachable: bool
    available_models: list[str] = []


class ModeInfo(BaseModel):
    id: str
    name: str
    description: str
    streams_tokens: bool
    streams_steps: bool
