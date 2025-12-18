from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import google.generativeai as genai
import os
from datetime import datetime
from typing import Optional

router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"],
    responses={404: {"description": "Not found"}},
)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None
    print("Warning: GEMINI_API_KEY not found in environment variables")

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: str
    error: Optional[str] = None

@router.post("/send", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to the Gemini chatbot and get a response.
    """
    if not model:
        raise HTTPException(status_code=503, detail="Chatbot service unavailable (API key missing)")

    try:
        # Create a chat session if needed (simplified for now, stateless per request)
        # In a real app, we might want to maintain history based on session_id
        
        chat = model.start_chat(history=[])
        response = chat.send_message(request.message)
        
        return ChatResponse(
            response=response.text,
            session_id=request.session_id or "new_session",
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        print(f"Error communicating with Gemini: {e}")
        raise HTTPException(status_code=500, detail=f"Error communicating with chatbot service: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Check the health of the chatbot service.
    """
    return {
        "status": "online",
        "gemini_available": model is not None,
        "message": "Chatbot service is running"
    }
