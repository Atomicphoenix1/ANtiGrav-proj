import os
import sys
import json
import asyncio
import threading
import importlib.util
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

CORE_PATH = os.path.join(SCRIPT_DIR, "Super-Uploader_opus.py")
spec = importlib.util.spec_from_file_location("pipeline_core", CORE_PATH)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

SETTINGS_PATH = os.path.join(SCRIPT_DIR, "pipeline_state.json")
WEBUI_DIR = os.path.join(SCRIPT_DIR, "webui")
TEMP_DIR = os.path.join(SCRIPT_DIR, "webui_temp_uploads")

_pipeline_running = False
_pipeline_cancelled = False

DEFAULT_SETTINGS = {
    "gemini_api_key": core.GEMINI_API_KEY,
    "n8n_webhook_url": "",
    "n8n_log_bridge_enabled": True,
    "last_model": "gemini-3-flash-preview",
    "last_device": "cuda",
    "last_split_mode": "10 min",
    "last_custom_seconds": 600,
    "last_scope": "Singular",
    "last_operation": "Whisper + Gemini",
    "theme": "alchemist"
}


def load_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(data: dict):
    merged = dict(DEFAULT_SETTINGS)
    merged.update(data)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    return merged


class FileRef:
    def __init__(self, path: str):
        self.name = path


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(WEBUI_DIR, exist_ok=True)
    settings = load_settings()
    if settings.get("gemini_api_key"):
        core.set_gemini_api_key(settings["gemini_api_key"])
    core.set_n8n_log_bridge(settings.get("n8n_log_bridge_enabled", True))
    if settings.get("n8n_webhook_url"):
        core.set_n8n_webhook_url(settings["n8n_webhook_url"])
    yield


app = FastAPI(title="Super Uploader Pipeline", lifespan=lifespan)


@app.get("/api/settings")
def get_settings():
    return load_settings()


class SettingsBody(BaseModel):
    gemini_api_key: Optional[str] = None
    n8n_webhook_url: Optional[str] = None
    n8n_log_bridge_enabled: Optional[bool] = None
    last_model: Optional[str] = None
    last_device: Optional[str] = None
    last_split_mode: Optional[str] = None
    last_custom_seconds: Optional[int] = None
    last_scope: Optional[str] = None
    last_operation: Optional[str] = None
    theme: Optional[str] = None


@app.post("/api/settings")
def post_settings(body: SettingsBody):
    current = load_settings()
    update = body.model_dump(exclude_none=True)
    current.update(update)
    merged = save_settings(current)

    if body.gemini_api_key is not None:
        core.set_gemini_api_key(body.gemini_api_key)
    if body.n8n_log_bridge_enabled is not None:
        core.set_n8n_log_bridge(body.n8n_log_bridge_enabled)
    if body.n8n_webhook_url is not None:
        core.set_n8n_webhook_url(body.n8n_webhook_url)

    return merged


@app.post("/api/browse-folder")
def browse_folder():
    path = core.browse_folder()
    if not path:
        raise HTTPException(status_code=400, detail="No folder selected")
    return {"path": path}


@app.get("/api/pipeline/status")
def pipeline_status():
    return {"running": _pipeline_running}


@app.post("/api/pipeline/cancel")
def cancel_pipeline():
    global _pipeline_cancelled
    _pipeline_cancelled = True
    return {"cancelled": True}


def save_upload(upload: UploadFile) -> str:
    os.makedirs(TEMP_DIR, exist_ok=True)
    dest = os.path.join(TEMP_DIR, upload.filename or "upload")
    with open(dest, "wb") as f:
        f.write(upload.file.read())
    return dest


@app.post("/api/pipeline")
async def run_pipeline(
    op_mode: str = Form("Whisper + Gemini"),
    scope: str = Form("Singular"),
    device: str = Form("cuda"),
    gemini_model: str = Form("gemini-3-flash-preview"),
    split_mode: str = Form("10 min"),
    custom_seconds: int = Form(600),
    text_box: str = Form(""),
    folder_input: str = Form(""),
    single_audio: UploadFile = File(None),
    multi_audio: list[UploadFile] = File(None),
    single_txt: UploadFile = File(None),
    multi_txt: list[UploadFile] = File(None),
    srt_txt_file: UploadFile = File(None),
    srt_json_file: UploadFile = File(None),
):
    global _pipeline_running, _pipeline_cancelled

    if _pipeline_running:
        raise HTTPException(status_code=409, detail="Pipeline already running")

    _pipeline_running = True
    _pipeline_cancelled = False

    sa = None
    ma = None
    st = None
    mt = None
    srt_txt = None
    srt_json = None

    if single_audio:
        sa = FileRef(save_upload(single_audio))
    if multi_audio:
        ma = [FileRef(save_upload(f)) for f in multi_audio if f.filename]
    if single_txt:
        st = FileRef(save_upload(single_txt))
    if multi_txt:
        mt = [FileRef(save_upload(f)) for f in multi_txt if f.filename]
    if srt_txt_file:
        srt_txt = FileRef(save_upload(srt_txt_file))
    if srt_json_file:
        srt_json = FileRef(save_upload(srt_json_file))

    if not folder_input:
        folder_input = ""

    settings = load_settings()
    settings["last_model"] = gemini_model
    settings["last_device"] = device
    settings["last_split_mode"] = split_mode
    settings["last_custom_seconds"] = custom_seconds
    settings["last_scope"] = scope
    settings["last_operation"] = op_mode
    save_settings(settings)

    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()

    def run():
        global _pipeline_running, _pipeline_cancelled
        try:
            gen = core.execute_pipeline(
                op_mode, scope,
                sa, ma, folder_input,
                st, mt, text_box,
                device, gemini_model,
                split_mode, custom_seconds,
                srt_txt, srt_json
            )
            for log_batch in gen:
                if _pipeline_cancelled:
                    asyncio.run_coroutine_threadsafe(
                        queue.put(("status", "cancelled")), loop
                    )
                    return
                asyncio.run_coroutine_threadsafe(
                    queue.put(("log", log_batch)), loop
                )
            asyncio.run_coroutine_threadsafe(queue.put(("status", "completed")), loop)
        except Exception as e:
            asyncio.run_coroutine_threadsafe(
                queue.put(("error", str(e))), loop
            )
        finally:
            _pipeline_running = False
            _pipeline_cancelled = False

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

    async def event_generator():
        try:
            while True:
                try:
                    event_type, data = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    if _pipeline_cancelled:
                        yield f"data: {json.dumps({'status': 'cancelled'})}\n\n"
                        break
                    yield f"data: {json.dumps({'status': 'running'})}\n\n"
                    continue

                if event_type == "log":
                    yield f"data: {json.dumps({'log': data})}\n\n"
                elif event_type == "status":
                    yield f"data: {json.dumps({'status': data})}\n\n"
                    break
                elif event_type == "error":
                    yield f"data: {json.dumps({'error': data})}\n\n"
                    break
        finally:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/{full_path:path}")
async def serve_static(full_path: str):
    if full_path == "" or full_path == "/":
        file_path = os.path.join(WEBUI_DIR, "index.html")
    else:
        file_path = os.path.join(WEBUI_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(WEBUI_DIR, "index.html"))

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
