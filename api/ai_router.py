from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from django.contrib.auth.models import User

from api.auth import get_current_user
from api.ai_controller import AIController
from api.schemas.ai_schema import AIChatRequest, AIChatResponse, AIChatHistoryResponse

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post("/chat", response_model=AIChatResponse)
def chat_endpoint(payload: AIChatRequest, current_user: User = Depends(get_current_user)):
    try:
        result = AIController.process_chat(
            user=current_user,
            user_message=payload.message,
            platform_code=payload.platform,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/chat/stream")
def chat_stream_endpoint(payload: AIChatRequest, current_user: User = Depends(get_current_user)):
    try:
        return StreamingResponse(
            AIController.process_chat_stream(
                user=current_user,
                user_message=payload.message,
                platform_code=payload.platform,
            ),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/history", response_model=AIChatHistoryResponse)
def chat_history(current_user: User = Depends(get_current_user)):
    history = AIController.fetch_history(current_user)
    return {"success": True, "history": history}
