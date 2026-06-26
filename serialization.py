"""Normalize candidate records for API responses."""

import json
from typing import Any


def normalize_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    skills = candidate.get("skills", [])
    if isinstance(skills, str):
        try:
            candidate["skills"] = json.loads(skills) if skills else []
        except json.JSONDecodeError:
            candidate["skills"] = []

    experience = candidate.get("experience", "Fresher")
    if isinstance(experience, list) and experience:
        candidate["experience"] = experience[0]
    elif not experience:
        candidate["experience"] = "Fresher"

    return candidate


def normalize_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [normalize_candidate(candidate) for candidate in candidates]
