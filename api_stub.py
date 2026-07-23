"""
ATS Backend — Development Stub
Mirrors the real api.py /api/parse + /api/score contract without PyTorch / spaCy / EasyOCR.

Start with:  python -m uvicorn api_stub:app --reload --port 3001
"""

from __future__ import annotations

import hashlib
import os
import random
from pathlib import Path
from typing import Any, List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ats_auth import require_ats_api_key
from ats_response import candidate_to_extracted, parse_expected_skills

app = FastAPI(title="ATS Backend (Dev Stub)", description="Mock ATS server — no ML deps required")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "resumes_to_process")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MOCK_SKILLS = [
    ["Python", "FastAPI", "SQL"],
    ["React", "TypeScript", "Node.js"],
    ["Java", "Spring Boot", "Microservices"],
    ["Go", "Docker", "Kubernetes"],
    ["Machine Learning", "PyTorch", "NumPy"],
]

MOCK_NAMES = [
    "Arjun Sharma", "Priya Mehta", "Rahul Gupta", "Sneha Patel",
    "Vikram Singh", "Anita Rao", "Rohit Kumar", "Deepa Nair",
]

MOCK_TITLES = [
    "Software Engineer", "Senior Developer", "Full Stack Developer",
    "Backend Engineer", "Frontend Developer", "Data Engineer",
]

MOCK_UNIVERSITIES = [
    "IIT Delhi", "IIT Bombay", "BITS Pilani", "NIT Trichy",
    "VIT Vellore", "Delhi University",
]


def _safe_filename(name: str | None) -> str:
    base = Path(name or "resume.pdf").name
    cleaned = "".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in base).strip()
    return cleaned[:180] or "resume.pdf"


def _mock_candidate(filename: str, job_id: str | None, expected_skills: list | None = None) -> dict:
    """Generate a deterministic-ish mock candidate from the filename."""
    seed = int(hashlib.md5(filename.encode()).hexdigest(), 16) % 10000
    rng = random.Random(seed)

    name = rng.choice(MOCK_NAMES)
    first, last = name.split(" ", 1)
    email = f"{first.lower()}.{last.lower().replace(' ', '')}@example.com"
    skills = list(rng.choice(MOCK_SKILLS)) + [rng.choice(["Git", "Linux", "AWS", "Redis"])]
    if expected_skills:
        for skill in expected_skills[:3]:
            if skill and str(skill) not in skills:
                skills.append(str(skill))

    score = round(rng.uniform(55, 95), 1)
    if expected_skills:
        overlap = len({str(s).lower() for s in skills} & {str(s).lower() for s in expected_skills})
        score = min(95, 55 + overlap * 12)

    return {
        "filename": filename,
        "name": name,
        "email": email,
        "phone": f"+91 {rng.randint(7000000000, 9999999999)}",
        "location": rng.choice(["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Pune"]),
        "education": "B.Tech in Computer Science",
        "experience": f"{rng.randint(1, 8)} years",
        "skills": skills,
        "match_score": int(score),
        "status": "New",
        "summary": (
            f"{name} is an experienced {rng.choice(MOCK_TITLES)} "
            f"with strong expertise in {', '.join(skills[:2])}."
        ),
        "university": rng.choice(MOCK_UNIVERSITIES),
        "grad_year": str(rng.randint(2015, 2023)),
        "linkedin": f"https://linkedin.com/in/{first.lower()}{last.lower()}",
        "github": f"https://github.com/{first.lower()}{last.lower()}",
        "portfolio": "",
        "certifications": [c for c in [rng.choice(["AWS Certified", "GCP Associate", "CKA", ""])] if c],
        "languages": ["English", rng.choice(["Hindi", "Tamil", "Telugu", "Kannada"])],
        "work_history": [
            {
                "title": rng.choice(MOCK_TITLES),
                "company": rng.choice(["Infosys", "Wipro", "TCS", "HCL", "Accenture"]),
                "duration": f"{rng.randint(1, 4)} years",
            }
        ],
        "fingerprint": hashlib.md5(filename.encode()).hexdigest(),
        "job_id": int(job_id) if job_id and job_id.isdigit() else job_id,
    }


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
    if not file:
        raise HTTPException(status_code=400, detail="Resume file is required")

    skills_list = parse_expected_skills(expected_skills)
    filename = _safe_filename(file.filename)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    dest = os.path.join(UPLOAD_DIR, filename)
    with open(dest, "wb") as fh:
        fh.write(content)

    candidate = _mock_candidate(filename, job_id, skills_list)
    raw_text = content.decode("utf-8", errors="ignore") or candidate["summary"]
    extracted = candidate_to_extracted(candidate, raw_text)

    return {
        "success": True,
        "filename": filename,
        "extracted": extracted,
        "match_score": candidate["match_score"],
        "raw_text": raw_text[:50000],
        "algorithm_version": "hrms-py-stub",
        "job_id": job_id,
        "stub": True,
    }


@app.post("/api/score")
async def score_candidate(
    payload: ScoreRequest,
    _: None = Depends(require_ats_api_key),
):
    candidate = payload.candidate or {}
    skills = candidate.get("skills") or []
    expected = payload.expected_skills or []
    overlap = len({str(s).lower() for s in skills} & {str(s).lower() for s in expected}) if expected else 0
    base = int(candidate.get("match_score") or candidate.get("profileScore") or 70)
    score = min(100, base + overlap * 5) if expected else base
    return {
        "success": True,
        "match_score": score,
        "algorithm_version": "hrms-py-stub",
        "components": {
            "skillsWeight": 0.5,
            "experienceWeight": 0.2,
            "educationWeight": 0.15,
            "certificationsWeight": 0.15,
        },
        "matchedRequirements": [str(s) for s in expected if str(s).lower() in {str(x).lower() for x in skills}],
        "missingRequirements": [str(s) for s in expected if str(s).lower() not in {str(x).lower() for x in skills}],
        "warnings": [],
        "job_id": payload.job_id,
        "stub": True,
    }


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
    results = []
    for f in files:
        filename = _safe_filename(f.filename)
        dest = os.path.join(UPLOAD_DIR, filename)
        content = await f.read()
        with open(dest, "wb") as fh:
            fh.write(content)
        results.append(_mock_candidate(filename, job_id, skills_list))

    return {
        "success": True,
        "candidates": results,
        "stub": True,
        "job_id": job_id,
    }


@app.get("/health")
def health():
    return {"status": "ok", "mode": "stub"}
