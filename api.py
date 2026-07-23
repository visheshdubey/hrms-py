from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import os
import json
import tempfile
import shutil
from typing import List, Optional, Any
from pathlib import Path

import ats_main
import export_results
from ats_auth import require_ats_api_key
from ats_response import candidate_to_extracted, parse_expected_skills

app = FastAPI(title="ATS Backend System", description="FastAPI Server for Resume Analysis")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "candidates_data.json")
UPLOAD_DIR = os.path.join(BASE_DIR, "resumes_to_process")

os.makedirs(UPLOAD_DIR, exist_ok=True)


def _safe_filename(name: str | None) -> str:
    base = Path(name or "resume.pdf").name
    cleaned = "".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in base).strip()
    return cleaned[:180] or "resume.pdf"


class ScoreRequest(BaseModel):
    candidate: dict[str, Any] = Field(default_factory=dict)
    job_description: Optional[str] = None
    expected_skills: Optional[list[Any]] = None
    job_id: Optional[str] = None


@app.post("/api/parse")
async def parse_resume(
    file: UploadFile = File(...),
    job_id: str = Form(None),
    job_description: str = Form(None),
    expected_skills: str = Form(None),
    _: None = Depends(require_ats_api_key),
):
    """Single-file parse for Hono — isolated temp dir, no shared JSON overwrite."""
    if not file:
        raise HTTPException(status_code=400, detail="Resume file is required")

    skills_list = parse_expected_skills(expected_skills)
    filename = _safe_filename(file.filename)
    tmp_dir = tempfile.mkdtemp(prefix="ats-parse-")
    try:
        file_path = os.path.join(tmp_dir, filename)
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        result = ats_main.parse_resume_for_api(
            file_path,
            filename,
            expected_skills=skills_list,
            job_id=job_id,
            job_description=job_description,
        )
        if result.get("status") != "success":
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": result.get("error") or "Parse failed",
                    "filename": filename,
                },
            )
        return {
            "success": True,
            "filename": filename,
            "extracted": result["extracted"],
            "match_score": result.get("match_score"),
            "raw_text": result.get("raw_text") or "",
            "algorithm_version": result.get("algorithm_version") or "hrms-py",
            "job_id": job_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f" [Error] /api/parse failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Python parse failed: {str(e)}"},
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@app.post("/api/score")
async def score_candidate(
    payload: ScoreRequest,
    _: None = Depends(require_ats_api_key),
):
    """Score an already-extracted candidate profile against a job description."""
    try:
        result = ats_main.score_candidate_for_api(
            payload.candidate,
            expected_skills=payload.expected_skills or [],
            job_description=payload.job_description,
        )
        return {"success": True, **result, "job_id": payload.job_id}
    except Exception as e:
        print(f" [Error] /api/score failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Python score failed: {str(e)}"},
        )


@app.post("/api/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    job_id: str = Form(None),
    job_description: str = Form(None),
    expected_skills: str = Form(None),
    _: None = Depends(require_ats_api_key),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    skills_list = parse_expected_skills(expected_skills)

    uploaded_files = []
    try:
        # Save uploaded files
        for file in files:
            safe = _safe_filename(file.filename)
            file_path = os.path.join(UPLOAD_DIR, safe)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_files.append(safe)
        # Process resumes
        ats_main.run_ats_pipeline(expected_skills=skills_list, job_id=job_id, job_description=job_description)
        export_results.generate_vishesh_report()

        # Fetch results
        candidates_out = []
        if os.path.exists(JSON_PATH):
            with open(JSON_PATH, 'r', encoding='utf-8') as f:
                candidates_out = json.load(f)

            for c in candidates_out:
                skills = c.get("skills", [])
                if isinstance(skills, str):
                    try:
                        c["skills"] = json.loads(skills) if skills else []
                    except Exception:
                        c["skills"] = []

                exp = c.get("experience", "Fresher")
                if isinstance(exp, list) and len(exp) > 0:
                    c["experience"] = exp[0]
                elif not exp:
                    c["experience"] = "Fresher"

        return {
            "success": True,
            "message": f"{len(uploaded_files)} resume(s) processed by AI pipeline.",
            "files": uploaded_files,
            "candidates": candidates_out,
            "job_id": job_id,
        }
    except Exception as e:
        print(f" [Error] Python pipeline error: {str(e)}")
        return JSONResponse(status_code=500, content={
            "success": False,
            "error": f"Python pipeline failed: {str(e)}",
            "files": uploaded_files
        })


@app.get("/api/candidates")
def get_candidates():
    if not os.path.exists(JSON_PATH):
        return {"candidates": []}

    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            candidates = json.load(f)

        # Sort by match_score DESC
        candidates.sort(key=lambda x: x.get("match_score", 0), reverse=True)

        # Parse skills and experience formatting
        for c in candidates:
            skills = c.get("skills", [])
            if isinstance(skills, str):
                try:
                    c["skills"] = json.loads(skills) if skills else []
                except Exception:
                    c["skills"] = []

            exp = c.get("experience", "Fresher")
            if isinstance(exp, list) and len(exp) > 0:
                c["experience"] = exp[0]
            elif not exp:
                c["experience"] = "Fresher"

        return {"candidates": candidates}

    except Exception as e:
        print(f"JSON data error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": "Failed to read candidates", "detail": str(e)})


@app.get("/api/system-status")
def system_status():
    if not os.path.exists(JSON_PATH):
        return {"online": False, "message": "JSON file not found", "candidateCount": 0}

    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            candidates = json.load(f)

        count = len(candidates)
        return {
            "online": True,
            "message": f"System Online: {count} Candidates Indexed",
            "candidateCount": count
        }
    except Exception as e:
        return {"online": False, "message": f"Error: {str(e)}", "candidateCount": 0}


@app.get("/health")
def health():
    return {"status": "ok", "mode": "full"}


if __name__ == "__main__":
    import uvicorn
    # Make sure we use port 8000 to match the Docker config
    print(f"\n [Server] ATS API server starting at http://localhost:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
