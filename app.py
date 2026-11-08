"""FastAPI app for VeriAgent."""
import os
import shutil
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import agent
import provenance

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CSV = os.path.join(HERE, "data", "glacier_lakes_sample.csv")
os.makedirs(provenance.RUNS_DIR, exist_ok=True)

app = FastAPI(title="VeriAgent")
app.mount("/runs", StaticFiles(directory=provenance.RUNS_DIR), name="runs")


@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "static", "index.html"))


@app.post("/api/run")
def run(question: str = Form(...), file: UploadFile | None = File(None)):
    if file is None or not file.filename:
        return agent.run_task(question, DEFAULT_CSV)
    tmp = tempfile.mkdtemp(prefix="veriagent_upload_")
    path = os.path.join(tmp, os.path.basename(file.filename) or "upload.csv")
    try:
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        return agent.run_task(question, path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    rec = provenance.load_record(run_id) if run_id.isalnum() else None
    if rec is None:
        raise HTTPException(404, "Run not found")
    return rec
