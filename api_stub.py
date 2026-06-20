"""
ATS Backend — Development Stub
Mirrors the real api.py interface but returns plausible mock data
without requiring PyTorch / spaCy / EasyOCR.

Start with:  python -m uvicorn api_stub:app --reload --port 3001
"""

import os
import random
import hashlib
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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


def _mock_candidate(filename: str, job_id: str | None) -> dict:
    """Generate a deterministic-ish mock candidate from the filename."""
    seed = int(hashlib.md5(filename.encode()).hexdigest(), 16) % 10000
    rng = random.Random(seed)

    name = rng.choice(MOCK_NAMES)
    first, last = name.split(" ", 1)
    email = f"{first.lower()}.{last.lower().replace(' ', '')}@example.com"
    score = round(rng.uniform(55, 95), 1)
    skills = rng.choice(MOCK_SKILLS) + [rng.choice(["Git", "Linux", "AWS", "Redis"])]

    return {
        "filename": filename,
        "name": name,
        "email": email,
        "phone": f"+91 {rng.randint(7000000000, 9999999999)}",
        "location": rng.choice(["Bangalore", "Mumbai", "Delhi", "Hyderabad", "Pune"]),
        "education": f"B.Tech in Computer Science",
        "experience": f"{rng.randint(1, 8)} years",
        "skills": skills,
        "match_score": score,
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
        "certifications": [rng.choice(["AWS Certified", "GCP Associate", "CKA", ""])],
        "languages": ["English", rng.choice(["Hindi", "Tamil", "Telugu", "Kannada"])],
        "work_history": [
            {
                "title": rng.choice(MOCK_TITLES),
                "company": rng.choice(["Infosys", "Wipro", "TCS", "HCL", "Accenture"]),
                "duration": f"{rng.randint(1, 4)} years",
            }
        ],
        "fingerprint": hashlib.md5(filename.encode()).hexdigest(),
        "job_id": int(job_id) if job_id and job_id.isdigit() else None,
    }


@app.post("/api/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    job_id: str = Form(None),
    job_description: str = Form(None),
    expected_skills: str = Form(None),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    results = []
    for f in files:
        # Save the file so the real pipeline could process it later
        dest = os.path.join(UPLOAD_DIR, f.filename or "upload.pdf")
        content = await f.read()
        with open(dest, "wb") as fh:
            fh.write(content)

        results.append(_mock_candidate(f.filename or "resume.pdf", job_id))

    return {"candidates": results, "stub": True}


@app.get("/health")
def health():
    return {"status": "ok", "mode": "stub"}
