"""
/chat — the main conversational endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.auth.dependencies import get_current_user, CurrentUser
from app.graph.agent import build_agent_for_user

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    language: str = "en"


class ChatResponse(BaseModel):
    response: str

@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, current_user: CurrentUser = Depends(get_current_user)):
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="message must not be empty")

    agent = build_agent_for_user(current_user, language=payload.language)
    config = {"configurable": {"thread_id": current_user.user_id}}

    result = agent.invoke(
        {"messages": [HumanMessage(content=payload.message)]},
        config=config,
    )

    final_message = result["messages"][-1]
    return ChatResponse(response=final_message.content)