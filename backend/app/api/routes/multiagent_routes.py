from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.modes.multiagent.orchestrator import TranslationOrchestrator
from app.schemas.translation_schemas import TranslateRequest

router = APIRouter(prefix="/api/multiagent", tags=["multiagent"])


@router.post("/translate")
async def translate(req: TranslateRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Texto vacio")
    orchestrator = TranslationOrchestrator()
    return StreamingResponse(
        orchestrator.run(req.text, req.target_lang),
        media_type="text/event-stream",
    )
