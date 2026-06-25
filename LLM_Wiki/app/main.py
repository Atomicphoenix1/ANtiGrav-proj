import os
import re
from datetime import datetime
import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Security, status, Header, Query
from pydantic import BaseModel, Field

from app.config import settings
from app.github_client import github_client
from app.rag import rag_system

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Startup/Shutdown lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the vector index from GitHub on start
    try:
        if settings.GITHUB_TOKEN and settings.GITHUB_REPO:
            await rag_system.initialize_index()
        else:
            logger.warning("GitHub configurations missing. In-memory index starts empty.")
    except Exception as e:
        logger.error(f"Startup initialization failed: {e}")
    yield

app = FastAPI(
    title="Antigravity Telegram LLM Wiki RAG API",
    description="Stateless FastAPI backend connecting Telegram, N8N, Gemini, and Obsidian.",
    version="1.0.0",
    lifespan=lifespan
)

# Request Models
class QARecord(BaseModel):
    question: str = Field(..., description="The original question text from Telegram.")
    answer: str = Field(..., description="The answer given by the Mufti.")
    asker_id: Optional[str] = Field(None, description="The Telegram user ID of the asker.")
    message_id: Optional[str] = Field(None, description="Telegram message ID for tracing/linking.")

# Security dependency
def verify_token(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    token: Optional[str] = Query(None, description="Access token via query param as alternative")
):
    valid_token = settings.SECURITY_TOKEN
    # Allow passing via custom header or query parameter
    if x_api_key == valid_token or token == valid_token:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Invalid or missing security token"
    )

def slugify_arabic(text: str, max_words: int = 6) -> str:
    """
    Cleans and slugifies Arabic and English text to create valid and readable filenames.
    """
    # Remove common punctuation and markdown (including Arabic question mark)
    text = re.sub(r"[❓💡!#\?؟*`\[\]\(\)\"\']", "", text)
    # Replace whitespace and underscores with single hyphen
    text = re.sub(r"[\s_]+", "-", text)
    # Filter to alphanumeric, Arabic characters, and hyphens
    cleaned = re.sub(r"[^\w\u0600-\u06FF-]", "", text)
    # Split, limit words, and rejoin
    words = [w for w in cleaned.split("-") if w]
    return "-".join(words[:max_words])

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Antigravity LLM Wiki API",
        "documents_indexed": len(rag_system.documents)
    }

@app.get("/search", dependencies=[Depends(verify_token)])
async def search(
    q: str = Query(..., description="The question/query to search for."),
    threshold: float = Query(0.6, description="Similarity threshold (0.0 to 1.0).")
):
    """
    Searches the vault index for matching Q&As and answers using Gemini.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    result = await rag_system.search_and_answer(q, similarity_threshold=threshold)
    return result

@app.post("/add-qa", dependencies=[Depends(verify_token)])
async def add_qa(record: QARecord):
    """
    Formats the Q&A, writes to the private Obsidian GitHub repo, and updates the RAG index.
    """
    question_clean = record.question.replace("❓", "").strip()
    answer_clean = record.answer.replace("💡", "").strip()
    
    if not question_clean or not answer_clean:
        raise HTTPException(status_code=400, detail="Question and answer cannot be empty.")
    
    # Generate metadata
    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # Create filename
    slug = slugify_arabic(question_clean)
    filename = f"fatwa-{timestamp_str}-{slug}.md"
    
    subfolder = settings.OBSIDIAN_SUBFOLDER.strip("/")
    file_path = f"{subfolder}/{filename}" if subfolder else filename
    
    # Render frontmatter & markdown
    # Escape quotes in frontmatter
    escaped_question = question_clean.replace('"', '\\"')
    
    md_content = f"""---
date: {today_str}
asker_id: "{record.asker_id or 'unknown'}"
message_id: "{record.message_id or 'none'}"
question: "{escaped_question}"
tags: [fatwa, telegram]
---

# Question
{question_clean}

# Answer
{answer_clean}
"""
    
    # Commit to GitHub
    commit_msg = f"Add fatwa: {question_clean[:30]}..."
    success = await github_client.create_or_update_file(file_path, md_content, commit_msg)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save markdown to GitHub repository.")
    
    # Hot-update local vector search index
    await rag_system.add_document(filename, file_path, md_content)
    
    return {
        "status": "success",
        "message": "Q&A committed and indexed successfully",
        "file_path": file_path,
        "filename": filename
    }

@app.post("/reindex", dependencies=[Depends(verify_token)])
async def reindex():
    """
    Force-refreshes the in-memory document vector index from the GitHub repository.
    """
    await rag_system.initialize_index()
    return {
        "status": "success",
        "message": f"Index successfully reloaded. Total indexed: {len(rag_system.documents)} documents."
    }

if __name__ == "__main__":
    import uvicorn
    # Start uvicorn server locally
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
