from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.persona_manager import PersonaManager
from app.services.chat_engine import ChatEngine

router = APIRouter(prefix="/personas", tags=["Personas"])

class PersonaSelectRequest(BaseModel):
    user_id: str
    persona_name: str

class ActivePersonaRequest(BaseModel):
    user_id: str

# === List personas ===
@router.get("/list")
def list_personas():
    personas = PersonaManager.list_personas()
    if not personas:
        raise HTTPException(status_code=404, detail="No personas found")
    return {"personas": personas}

# === Select persona and clear context ===
@router.post("/select")
def select_persona(request: PersonaSelectRequest):
    """
    Switches the active persona for a given user, clears chat context,
    and preloads the new persona immediately.
    """
    try:
        PersonaManager.set_persona(request.user_id, request.persona_name)

        # 🧹 Clear old chat context
        ChatEngine.clear_context(request.user_id)

        # ⚡ Preload new persona data
        ChatEngine.preload_persona(request.user_id)

        return {
            "message": f"Persona switched to '{request.persona_name}', context cleared, and persona preloaded",
            "active_persona": PersonaManager.get_active_metadata(request.user_id)
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# === Get active persona ===
@router.post("/active")
def get_active_persona(request: ActivePersonaRequest):
    active = PersonaManager.get_active_metadata(request.user_id)
    if not active:
        raise HTTPException(status_code=404, detail="No active persona found")
    return {"active_persona": active}
