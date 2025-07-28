from fastapi import APIRouter, Body
from pydantic import BaseModel
from app.services.chat_engine import ChatEngine
from fastapi.responses import StreamingResponse, JSONResponse
from app.services.elevenlabs_tts import synthesize_reply_as_stream

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    message: str
    mode: str
    voice_enabled: bool = True  # ✅ Toggle flag

class ChatResponse(BaseModel):
    reply: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    print(f"📩 [/chat/] message received from {request.user_id} | voice_enabled={request.voice_enabled}")
    result = await ChatEngine.generate_reply(
        user_id=request.user_id,
        message=request.message,
        mode=request.mode,
    )
    return ChatResponse(**result)

@router.post("/speak")
async def chat_speak_endpoint(request: ChatRequest):
    print(f"📡 [/chat/speak] Received TTS request | voice_enabled={request.voice_enabled}")

    result = await ChatEngine.generate_reply(
        user_id=request.user_id,
        message=request.message,
        mode=request.mode,
    )

    if not request.voice_enabled:
        print("🔇 [BACKEND] voice_enabled is FALSE — skipping ElevenLabs. No API call made.")
        return JSONResponse(
            content={"skipped": True, "reason": "voice disabled"},
            status_code=200
        )

    print(f"🗣️ [BACKEND] voice_enabled is TRUE — sending to ElevenLabs: \"{result['reply'][:60]}...\"")
    audio_stream = synthesize_reply_as_stream(result["reply"])
    return StreamingResponse(
        content=audio_stream,
        media_type="audio/mpeg",
        status_code=200
    )

@router.post("/speak-from-text")
def speak_from_text(reply: str = Body(..., embed=True)):
    print(f"📨 [BACKEND] /speak-from-text called with reply: \"{reply[:60]}...\"")
    audio_stream = synthesize_reply_as_stream(reply)
    return StreamingResponse(
        content=audio_stream,
        media_type="audio/mpeg",
        status_code=200
    )
