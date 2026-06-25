import time
import json as json_lib
import httpx
import logging
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from database import log_request, get_stats, get_recent_requests
from optimizer import optimize_anthropic_payload, optimize_openai_payload, compress_history
import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cachepilot")

app = FastAPI(title="CachePilot", description="Prompt Caching Proxy Server")

# Allow CORS for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP Client for forwarding requests
http_client = httpx.AsyncClient(timeout=60.0)

# Paths for static dashboard
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Helper to proxy headers
def get_forward_headers(request_headers: dict, provider: str) -> dict:
    headers = {}
    
    # Forward auth headers
    if provider == "anthropic":
        headers["x-api-key"] = request_headers.get("x-api-key") or config.ANTHROPIC_API_KEY
        headers["anthropic-version"] = request_headers.get("anthropic-version", "2023-06-01")
        headers["content-type"] = "application/json"
    elif provider == "openai":
        auth = request_headers.get("authorization")
        if not auth and config.OPENAI_API_KEY:
            auth = f"Bearer {config.OPENAI_API_KEY}"
        if auth:
            headers["authorization"] = auth
        headers["content-type"] = "application/json"
    
    # Clean up empty headers
    headers = {k: v for k, v in headers.items() if v}
    return headers

def parse_client_app(headers: dict) -> str:
    ua = headers.get("user-agent", "").lower()
    
    if "antigravity" in ua:
        return "Antigravity IDE"
    elif "vscode" in ua or "vs-code" in ua or "code" in ua:
        return "VS Code Agent"
    elif "minimax" in ua:
        return "MiniMax Agent"
    elif "cursor" in ua:
        return "Cursor Agent"
    elif "python-requests" in ua or "httpx" in ua or "python" in ua:
        return "Python Script/Test"
        
    # Check all headers for hints
    for k, v in headers.items():
        val = str(v).lower()
        if "antigravity" in val:
            return "Antigravity IDE"
        if "vscode" in val:
            return "VS Code Agent"
            
    return "Other App/Agent"

# --- LLM Proxy Endpoints ---

@app.post("/v1/messages")
async def proxy_anthropic(request: Request):
    """
    Proxy Anthropic Messages API
    """
    start_time = time.time()
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    model = body.get("model", "unknown-claude")
    
    # Apply automatic cache optimization
    optimized_body = optimize_anthropic_payload(body)
    
    # Apply history compression if needed
    if "messages" in optimized_body and isinstance(optimized_body["messages"], list):
        original_len = len(optimized_body["messages"])
        optimized_body["messages"] = compress_history(
            optimized_body["messages"], 
            limit=config.HISTORY_COMPRESSION_THRESHOLD
        )
        if len(optimized_body["messages"]) < original_len:
            logger.info(f"Compressed Anthropic history from {original_len} to {len(optimized_body['messages'])} messages.")
            
    headers = get_forward_headers(request.headers, "anthropic")
    if not headers.get("x-api-key"):
        return JSONResponse(
            status_code=401,
            content={"error": {"type": "authentication_error", "message": "No Anthropic API Key provided."}}
        )

    client_app = parse_client_app(dict(request.headers))

    try:
        response = await http_client.post(
            "https://api.anthropic.com/v1/messages",
            json=optimized_body,
            headers=headers
        )
        latency = int((time.time() - start_time) * 1000)
        
        # Parse usage stats
        res_data = response.json()
        input_tokens = 0
        cached_tokens = 0
        output_tokens = 0
        
        if "usage" in res_data:
            usage = res_data["usage"]
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            # Anthropic gives details of cache hits
            cached_tokens = usage.get("cache_read_input_tokens", 0)

        # Always log (even errors) with raw payloads
        raw_req_str = json_lib.dumps(optimized_body, indent=2, ensure_ascii=False)
        raw_res_str = json_lib.dumps(res_data, indent=2, ensure_ascii=False)
        log_request(
            provider="Anthropic",
            model=model,
            endpoint="/v1/messages",
            input_tokens=input_tokens,
            cached_input_tokens=cached_tokens,
            output_tokens=output_tokens,
            latency_ms=latency,
            status_code=response.status_code,
            client_app=client_app,
            raw_request=raw_req_str,
            raw_response=raw_res_str
        )
            
        resp_headers = dict(response.headers)
        resp_headers.pop("content-encoding", None)
        resp_headers.pop("content-length", None)
        resp_headers.pop("transfer-encoding", None)
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=resp_headers
        )
        
    except Exception as e:
        logger.error(f"Error proxying Anthropic request: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": {"type": "api_error", "message": str(e)}}
        )

@app.post("/v1/chat/completions")
async def proxy_openai(request: Request):
    """
    Proxy OpenAI API (Supports OpenAI, Gemini via base_url overrides, and others)
    """
    start_time = time.time()
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    model = body.get("model", "unknown-model")
    
    # If the user targets Gemini, or has custom settings, we can log it accordingly
    is_gemini = "gemini" in model.lower()
    provider = "Gemini" if is_gemini else "OpenAI"
    
    # For now, let's pass-through optimized payloads
    optimized_body = optimize_openai_payload(body)
    
    # Apply history compression if needed
    if "messages" in optimized_body and isinstance(optimized_body["messages"], list):
        original_len = len(optimized_body["messages"])
        optimized_body["messages"] = compress_history(
            optimized_body["messages"], 
            limit=config.HISTORY_COMPRESSION_THRESHOLD
        )
        if len(optimized_body["messages"]) < original_len:
            logger.info(f"Compressed OpenAI/Gemini history from {original_len} to {len(optimized_body['messages'])} messages.")
            
    headers = get_forward_headers(request.headers, "openai")
    
    # Determine upstream URL (Gemini OpenAI Compatibility vs OpenAI)
    upstream_url = "https://api.openai.com/v1/chat/completions"
    if is_gemini:
        # If accessing Gemini via Google OpenAI Compatibility:
        gemini_key = config.GEMINI_API_KEY
        current_auth = headers.get("authorization", "")
        if current_auth.startswith("Bearer "):
            token = current_auth.split(" ", 1)[1].strip()
            if token and token != "":
                gemini_key = token
        
        upstream_url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        headers["authorization"] = f"Bearer {gemini_key}"
            
    if not headers.get("authorization"):
        return JSONResponse(
            status_code=401,
            content={"error": {"message": "No Authorization Bearer token provided."}}
        )

    client_app = parse_client_app(dict(request.headers))

    try:
        response = await http_client.post(
            upstream_url,
            json=optimized_body,
            headers=headers
        )
        latency = int((time.time() - start_time) * 1000)
        
        # Parse usage stats
        res_data = response.json()
        input_tokens = 0
        cached_tokens = 0
        output_tokens = 0
        
        if "usage" in res_data:
            usage = res_data["usage"]
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            # OpenAI / Gemini usage details format
            prompt_details = usage.get("prompt_tokens_details", {})
            cached_tokens = prompt_details.get("cached_tokens", 0)

        # Always log (even errors) with raw payloads
        raw_req_str = json_lib.dumps(optimized_body, indent=2, ensure_ascii=False)
        raw_res_str = json_lib.dumps(res_data, indent=2, ensure_ascii=False)
        log_request(
            provider=provider,
            model=model,
            endpoint="/v1/chat/completions",
            input_tokens=input_tokens,
            cached_input_tokens=cached_tokens,
            output_tokens=output_tokens,
            latency_ms=latency,
            status_code=response.status_code,
            client_app=client_app,
            raw_request=raw_req_str,
            raw_response=raw_res_str
        )
            
        resp_headers = dict(response.headers)
        resp_headers.pop("content-encoding", None)
        resp_headers.pop("content-length", None)
        resp_headers.pop("transfer-encoding", None)
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=resp_headers
        )
        
    except Exception as e:
        logger.error(f"Error proxying OpenAI/Gemini request: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e)}}
        )


# --- Telemetry Dashboard API Endpoints ---

@app.get("/api/stats")
def api_get_stats():
    return get_stats()

@app.get("/api/requests")
def api_get_requests(limit: int = 20):
    return get_recent_requests(limit)

# --- Serving Dashboard Frontend UI ---

# Fallback to serve index.html for UI root
@app.get("/")
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "CachePilot is running. Please create static/index.html to view dashboard."}

# Mount static folder for CSS, JS, etc.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()
