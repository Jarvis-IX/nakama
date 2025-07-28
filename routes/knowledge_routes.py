from fastapi import APIRouter, HTTPException, File, UploadFile, Depends, Form, BackgroundTasks, status
from pydantic import BaseModel
import os
import traceback

# Import the dependency and controller
from api import get_rag_controller
from controllers.rag_controller import RAGController
from utils.file_utils import ensure_directory_exists

router = APIRouter(
    tags=["Knowledge Base"],
    responses={404: {"description": "Not found"}},
)

class AddTextRequest(BaseModel):
    text: str
    source: str = "text_input"

class AddKnowledgeResponse(BaseModel):
    message: str
    documents_added: int

@router.post("/knowledge/add/text", response_model=AddKnowledgeResponse)
async def add_text(
    request: AddTextRequest,
    rag_controller: RAGController = Depends(get_rag_controller)
):
    """
    Adds a piece of text to the knowledge base.
    """
    if not rag_controller:
        raise HTTPException(status_code=503, detail="RAG controller is not available.")
    
    try:
        success, count = rag_controller.add_knowledge(request.text, {"source": request.source})
        if success:
            return {"message": "Text added to knowledge base successfully.", "documents_added": count}
        else:
            raise HTTPException(status_code=500, detail="Failed to add text to knowledge base.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge/add/file", response_model=AddKnowledgeResponse, status_code=status.HTTP_202_ACCEPTED)
async def add_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    rag_controller: RAGController = Depends(get_rag_controller)
):
    """
    Adds a file (e.g., .txt, .md) to the knowledge base.
    The file is temporarily saved, processed, and then deleted.
    """
    if not rag_controller:
        raise HTTPException(status_code=503, detail="RAG controller is not available.")

    if not file.filename.endswith(('.txt', '.md', '.pdf')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .txt, .md, or .pdf file.")
    
    temp_storage_path = os.getenv('TEMP_STORAGE_PATH', './temp-storage')
    ensure_directory_exists(temp_storage_path)
    file_path = os.path.join(temp_storage_path, file.filename)

    try:
        # Save the uploaded file temporarily
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # Add the slow processing to a background task
        background_tasks.add_task(rag_controller.add_file_knowledge, file_path)
        
        # Return an immediate response to the user
        return {"message": f"File '{file.filename}' accepted and is being processed in the background.", "documents_added": 0}

    except Exception as e:
        # Log the full traceback for detailed debugging
        full_traceback = traceback.format_exc()
        # Return the full traceback in the response for easy debugging
        raise HTTPException(status_code=500, detail=f"An error occurred: {full_traceback}")
    # The cleanup must now happen inside the controller method after processing is done
    # so we remove the finally block here.
