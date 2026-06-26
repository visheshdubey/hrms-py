import csv
import json

from config import CANDIDATES_JSON, REPORT_CSV


def export_candidates_report() -> str | None:
    if not CANDIDATES_JSON.exists():
        print("No candidates found (JSON missing). Run the ATS pipeline first.")
        return None

    try:
        with open(CANDIDATES_JSON, "r", encoding="utf-8") as file:
            candidates = json.load(file)

        if not candidates:
            print("No candidates found in the JSON file. Run the ATS pipeline first.")
            return None

        print("\n" + "=" * 60)
        print(" [Start] ATS EXTRACTION RESULTS — 18-LAYER PIPELINE ")
        print("=" * 60)

        rows = []
        for candidate in candidates:
            filename = candidate.get("filename", "Unknown")
            name = candidate.get("name", "Unknown")
            email = candidate.get("email", "Not Found")
            phone = candidate.get("phone", "Not Found")
            location = candidate.get("location", "Not Found")

            experience_list = candidate.get("experience", [])
            experience = (
                experience_list[0]
                if isinstance(experience_list, list) and experience_list
                else "Fresher"
            )

            education = candidate.get("education", "Not Found")
            skills_list = candidate.get("skills", [])
            skills = ", ".join(skills_list) if isinstance(skills_list, list) else str(skills_list)
            match_score = candidate.get("match_score", 0)
            status = candidate.get("status", "Processed")
            linkedin = candidate.get("linkedin", "")
            github = candidate.get("github", "")
            portfolio = candidate.get("portfolio", "")

            certifications_list = candidate.get("certifications", [])
            certifications = (
                ", ".join(certifications_list)
                if isinstance(certifications_list, list)
                else str(certifications_list)
            )

            languages_list = candidate.get("languages", [])
            languages = (
                ", ".join(languages_list)
                if isinstance(languages_list, list)
                else str(languages_list)
            )

            summary = candidate.get("summary", "")[:200]
            university = candidate.get("university", "")
            grad_year = candidate.get("grad_year", "")

            work_history_list = candidate.get("work_history", [])
            work_history = (
                "; ".join(
                    [
                        f"{work.get('title', '')} @ {work.get('company', '')} ({work.get('duration', '')})"
                        for work in work_history_list
                    ]
                )
                if isinstance(work_history_list, list)
                else ""
            )

            rows.append([
                name, email, phone, location, experience, education, skills,
                match_score, status, linkedin, github, portfolio,
                certifications, languages, summary, university, grad_year,
                work_history, filename,
            ])

            print(f"File:          {filename}")
            print(f"Name:          {name}")
            print(f"Email:         {email}")
            print(f"Phone:         {phone}")
            print(f"Location:      {location}")
            print(f"Experience:    {experience}")
            print(f"Education:     {education}")
            print(f"University:    {university}")
            print(f"Grad Year:     {grad_year}")
            print(f"Skills:        {skills[:80]}...")
            print(f"Certifications:{certifications[:60]}")
            print(f"Languages:     {languages}")
            print(f"LinkedIn:      {linkedin}")
            print(f"GitHub:        {github}")
            print(f"Score:         {match_score}% Match")
            print("-" * 60)

        with open(REPORT_CSV, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "Name", "Email", "Phone", "Location", "Experience", "Education",
                "Skills", "Match Score", "Status", "LinkedIn", "GitHub", "Portfolio",
                "Certifications", "Languages", "Summary", "University", "Graduation Year",
                "Work History", "Filename",
            ])
            writer.writerows(rows)

        print(f"\n [Success] Successfully exported {len(rows)} processed profiles!")
        print(f" [Folder] Report saved to '{REPORT_CSV}'.")
        return str(REPORT_CSV)

    except Exception as error:
        print(f"Error reading JSON: {error}")
        return None


def generate_vishesh_report() -> str | None:
    """Backward-compatible alias for existing callers."""
    return export_candidates_report()


if __name__ == "__main__":
    export_candidates_report()
