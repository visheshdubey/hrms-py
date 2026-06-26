"""Shared paths and constants for the ATS pipeline."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "resumes_to_process"
PROCESSED_DIR = BASE_DIR / "archive" / "processed"
FAILED_DIR = BASE_DIR / "archive" / "failed"
PROFILE_PICS_DIR = BASE_DIR / "archive" / "profile_pics"
CANDIDATES_JSON = BASE_DIR / "candidates_data.json"
REPORT_CSV = BASE_DIR / "vishesh_report.csv"

RESUME_EXTENSIONS = (".pdf", ".png", ".jpg", ".jpeg", ".docx")

SCORE_WEIGHT_SKILL = 0.50
SCORE_WEIGHT_EXPERIENCE = 0.20
SCORE_WEIGHT_EDUCATION = 0.15
SCORE_WEIGHT_CERTIFICATION = 0.15

MAX_THREADS = 5
GB_PER_THREAD = 1.2
