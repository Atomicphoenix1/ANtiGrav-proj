import asyncio
import json
import os
from typing import Optional

from fastapi import FastAPI, Header, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from proxy import (
    event_bus, sessions,
    proxy_non_streaming, proxy_streaming,
)

app = FastAPI(title="OpenCode GUI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index():
    path = os.path.join(STATIC_DIR, "index.html")
    with open(path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


async def _resolve_session(
    session_id: Optional[str] = None,
    x_session_id: Optional[str] = None,
) -> str:
    sid = session_id or x_session_id
    if not sid or sid not in ("a", "b"):
        raise HTTPException(400, "Missing or invalid session. Use 'a' or 'b'. "
                                 "Pass via X-Session-Id header or /session/{id}/v1/... path.")
    return sid


@app.get("/events")
async def sse_events(session: str = Query("a")):
    if session not in ("a", "b"):
        raise HTTPException(400, "Session must be 'a' or 'b'")

    async def event_generator():
        q = event_bus.subscribe(session)
        try:
            while True:
                msg = await q.get()
                yield msg
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe(session, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.api_route(
    "/session/{session_id}/v1/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
)
async def proxy_path_based(session_id: str, path: str, request: Request):
    sid = await _resolve_session(session_id=session_id)
    return await _handle_proxy(request, sid, path)


@app.api_route(
    "/v1/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
)
async def proxy_header_based(path: str, request: Request,
                              x_session_id: Optional[str] = Header(None)):
    sid = await _resolve_session(x_session_id=x_session_id)
    return await _handle_proxy(request, sid, path)


async def _handle_proxy(request: Request, session_id: str, path: str):
    body = None
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type or "text/plain" in content_type:
        try:
            body = await request.json()
        except Exception:
            try:
                text = await request.body()
                if text:
                    body = json.loads(text)
            except Exception:
                body = None

    is_stream = isinstance(body, dict) and body.get("stream", False)

    if is_stream:
        status, gen, media_type, resp_headers = await proxy_streaming(
            request.method, path, dict(request.headers), body, session_id,
        )
        return StreamingResponse(
            gen,
            status_code=status,
            media_type=media_type,
            headers={k: v for k, v in resp_headers.items()
                     if k.lower() not in ("content-length", "transfer-encoding")},
        )
    else:
        status, data, media_type = await proxy_non_streaming(
            request.method, path, dict(request.headers), body, session_id,
        )
        if isinstance(data, str):
            return Response(content=data, status_code=status, media_type=media_type)
        return JSONResponse(content=data, status_code=status)


@app.post("/sessions/{session_id}/reset")
async def reset_session(session_id: str):
    if session_id not in ("a", "b"):
        raise HTTPException(400, "Session must be 'a' or 'b'")
    sessions[session_id].reset()
    await event_bus.publish(session_id, "metrics", sessions[session_id].to_dict())
    await event_bus.publish(session_id, "reset", {"session": session_id})
    return {"ok": True, "session": session_id}


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    if session_id not in ("a", "b"):
        raise HTTPException(400, "Session must be 'a' or 'b'")
    return sessions[session_id].to_dict()


@app.get("/sessions")
async def list_sessions():
    return {
        "a": sessions["a"].to_dict(),
        "b": sessions["b"].to_dict(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9876, reload=True)
