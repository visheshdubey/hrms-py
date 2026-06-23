from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import json
from typing import List
import shutil

import ats_main
import export_results

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


@app.post("/api/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    job_id: str = Form(None),
    job_description: str = Form(None),
    expected_skills: str = Form(None)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    skills_list = []
    if expected_skills:
        try:
            skills_list = json.loads(expected_skills)
        except Exception:
            skills_list = []

    uploaded_files = []
    try:
        # Save uploaded files
        for file in files:
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded_files.append(file.filename)
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
                    except:
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
                except:
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


if __name__ == "__main__":
    import uvicorn
    # Make sure we use port 8000 to match the Docker config
    print(f"\n [Server] ATS API server starting at http://localhost:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
