from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.modes.pipeline.translator import stream_translation
from app.schemas.translation_schemas import TranslateRequest

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/translate")
async def translate(req: TranslateRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Texto vacio")
    return StreamingResponse(
        stream_translation(req.text, req.source_lang, req.target_lang),
        media_type="text/event-stream",
    )
