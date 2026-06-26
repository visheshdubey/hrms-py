from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import shutil
import uuid
from typing import List

import ats_main
import export_results
from config import CANDIDATES_JSON, UPLOAD_DIR
from serialization import normalize_candidates

app = FastAPI(title="ATS Backend System", description="FastAPI Server for Resume Analysis")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _load_candidates() -> list[dict]:
    if not CANDIDATES_JSON.exists():
        return []

    with open(CANDIDATES_JSON, "r", encoding="utf-8") as file:
        candidates = json.load(file)

    return normalize_candidates(candidates)


@app.post("/api/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    job_id: str = Form(None),
    job_description: str = Form(None),
    expected_skills: str = Form(None),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    skills_list: list[str] = []
    if expected_skills:
        try:
            parsed = json.loads(expected_skills)
            skills_list = parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            skills_list = []

    uploaded_files: list[str] = []
    try:
        for file in files:
            safe_name = os.path.basename(file.filename or "resume.pdf")
            file_path = UPLOAD_DIR / f"{uuid.uuid4().hex}_{safe_name}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_files.append(safe_name)

        ats_main.run_ats_pipeline(
            expected_skills=skills_list,
            job_id=job_id,
            job_description=job_description,
        )
        export_results.export_candidates_report()

        candidates_out = _load_candidates()
        return {
            "success": True,
            "message": f"{len(uploaded_files)} resume(s) processed by AI pipeline.",
            "files": uploaded_files,
            "candidates": candidates_out,
            "job_id": job_id,
        }
    except Exception as error:
        print(f" [Error] Python pipeline error: {error}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Python pipeline failed: {error}",
                "files": uploaded_files,
            },
        )


@app.get("/api/candidates")
def get_candidates():
    if not CANDIDATES_JSON.exists():
        return {"candidates": []}

    try:
        candidates = _load_candidates()
        candidates.sort(key=lambda candidate: candidate.get("match_score", 0), reverse=True)
        return {"candidates": candidates}
    except Exception as error:
        print(f"JSON data error: {error}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to read candidates", "detail": str(error)},
        )


@app.get("/api/system-status")
def system_status():
    if not CANDIDATES_JSON.exists():
        return {"online": False, "message": "JSON file not found", "candidateCount": 0}

    try:
        with open(CANDIDATES_JSON, "r", encoding="utf-8") as file:
            candidates = json.load(file)

        count = len(candidates)
        return {
            "online": True,
            "message": f"System Online: {count} Candidates Indexed",
            "candidateCount": count,
        }
    except Exception as error:
        return {"online": False, "message": f"Error: {error}", "candidateCount": 0}


if __name__ == "__main__":
    import uvicorn

    print("\n [Server] ATS API server starting at http://localhost:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
