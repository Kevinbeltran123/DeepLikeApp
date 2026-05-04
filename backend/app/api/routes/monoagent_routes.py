from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.modes.monoagent.translator_agent import stream_translation
from app.schemas.translation_schemas import TranslateRequest

router = APIRouter(prefix="/api/monoagent", tags=["monoagent"])


@router.post("/translate")
async def translate(req: TranslateRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Texto vacio")
    return StreamingResponse(
        stream_translation(req.text, req.target_lang),
        media_type="text/event-stream",
    )
