from fastapi import FastAPI, Form, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from processor import TranscriptProcessor
import os
import json

app = FastAPI()

# Setup templates and static files
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/process")
async def process_transcript(
    transcript: str = Form(...),
    replacements_json: str = Form("[]")
):
    # Parse replacements
    try:
        replacements = json.loads(replacements_json)
    except:
        replacements = []

    processor = TranscriptProcessor(
        font_name='aaagoldenlotus',
        font_size=18,
        bold_all=True,
        red_italics=True
    )

    for r in replacements:
        if r.get("find") and r.get("replace"):
            processor.add_replacement(r["find"], r["replace"])

    docx_stream = processor.process(transcript)

    return StreamingResponse(
        docx_stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=transcript_processed.docx"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
