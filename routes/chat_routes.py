from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import logging

# Import the dependency and controller
from api import get_rag_controller
from controllers.rag_controller import RAGController

router = APIRouter(
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)

class ChatRequest(BaseModel):
    query: str
    use_context: bool = True
    similarity_threshold: float = 0.5
    max_context_docs: int = 5

@router.post("/chat/stream")
async def stream_chat(
    chat_request: ChatRequest,
    rag_controller: RAGController = Depends(get_rag_controller)
):
    """
    Handles a user's chat query and streams the response back.
    This endpoint uses the RAG (Retrieval-Augmented Generation) pipeline to generate a response.
    
    - **query**: The question to ask the AI.
    - **use_context**: Whether to use retrieved documents as context.
    - **similarity_threshold**: The minimum similarity score for a document to be included.
    - **max_context_docs**: The maximum number of context documents to use.
    """
    if not rag_controller:
        raise HTTPException(status_code=503, detail="RAG controller is not available.")

    # The controller's stream_response method is a generator that handles its own exceptions.
    response_generator = rag_controller.stream_response(
        question=chat_request.query,
        use_context=chat_request.use_context,
        similarity_threshold=chat_request.similarity_threshold,
        max_context_docs=chat_request.max_context_docs
    )
    return StreamingResponse(response_generator, media_type="text/event-stream")
