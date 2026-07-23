"""
Normalize ATS candidate payloads to the Hono ExtractedResumeData shape.
Used by the full API and the local stub so both expose the same /api/parse contract.
"""
from __future__ import annotations

import json
from typing import Any


def candidate_to_extracted(candidate: dict, raw_text: str = "") -> dict:
    email = candidate.get("email") or ""
    if str(email).lower() in ("not found",):
        email = ""
    phone = candidate.get("phone") or ""
    if str(phone).lower() in ("not found",):
        phone = ""
    experience = candidate.get("experience") or ""
    if isinstance(experience, list):
        experience = experience[0] if experience else "Fresher"
    skills = candidate.get("skills") or []
    if isinstance(skills, str):
        try:
            skills = json.loads(skills) if skills else []
        except Exception:
            skills = []
    certifications = candidate.get("certifications") or []
    languages = candidate.get("languages") or []
    work_history = candidate.get("work_history") or []
    normalized_wh = []
    for entry in work_history:
        if not isinstance(entry, dict):
            continue
        normalized_wh.append({
            "title": str(entry.get("title") or ""),
            "company": str(entry.get("company") or ""),
            "duration": str(entry.get("duration") or ""),
        })

    text = raw_text or candidate.get("raw_text") or ""
    missing = []
    for field, value in (
        ("name", candidate.get("name")),
        ("email", email),
        ("phone", phone),
        ("skills", skills),
    ):
        if not value:
            missing.append(field)

    match_score = int(candidate.get("match_score") or 0)
    profile_score = match_score if match_score > 0 else max(0, 100 - len(missing) * 15)

    links = []
    for key in ("linkedin", "github", "portfolio"):
        if candidate.get(key):
            links.append(str(candidate[key]))

    return {
        "name": str(candidate.get("name") or ""),
        "email": email,
        "emails": [email] if email else [],
        "phone": phone,
        "phones": [phone] if phone else [],
        "location": str(candidate.get("location") or ""),
        "education": str(candidate.get("education") or ""),
        "experience": str(experience or ""),
        "skills": [str(s) for s in skills],
        "linkedin": str(candidate.get("linkedin") or ""),
        "github": str(candidate.get("github") or ""),
        "portfolio": str(candidate.get("portfolio") or ""),
        "summary": str(candidate.get("summary") or ""),
        "university": str(candidate.get("university") or ""),
        "gradYear": str(candidate.get("grad_year") or candidate.get("gradYear") or ""),
        "certifications": [str(c) for c in certifications if c],
        "languages": [str(lang) for lang in languages if lang],
        "workHistory": normalized_wh,
        "links": links,
        "fingerprint": str(candidate.get("fingerprint") or ""),
        "missingFields": missing,
        "warnings": [],
        "ocrRecommended": len(text.replace(" ", "")) < 300 or len(missing) >= 5,
        "profileScore": profile_score,
        "textLength": len(text),
    }


def parse_expected_skills(raw: str | None) -> list[Any]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except Exception:
        return []
