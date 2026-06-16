import json
import csv
import os

def generate_vishesh_report():
    json_path = 'candidates_data.json'
    
    if not os.path.exists(json_path):
        print("No candidates found (JSON missing). Run main.py first!")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            candidates = json.load(f)
            
        if not candidates:
            print("No candidates found in the JSON file. Run main.py first!")
            return

        # 2. Print a clean summary to the Terminal for immediate proof
        print("\n" + "="*60)
        print(" [Start] ATS EXTRACTION RESULTS — 18-LAYER PIPELINE ")
        print("="*60)
        
        rows = []
        for c in candidates:
            filename = c.get('filename', 'Unknown')
            name = c.get('name', 'Unknown')
            email = c.get('email', 'Not Found')
            phone = c.get('phone', 'Not Found')
            location = c.get('location', 'Not Found')
            
            exp_list = c.get('experience', [])
            experience = exp_list[0] if isinstance(exp_list, list) and exp_list else 'Fresher'
            
            education = c.get('education', 'Not Found')
            
            skills_list = c.get('skills', [])
            skills = ", ".join(skills_list) if isinstance(skills_list, list) else str(skills_list)
            
            match_score = c.get('match_score', 0)
            status = c.get('status', 'Processed')

            # New fields
            linkedin = c.get('linkedin', '')
            github = c.get('github', '')
            portfolio = c.get('portfolio', '')

            certs_list = c.get('certifications', [])
            certifications = ", ".join(certs_list) if isinstance(certs_list, list) else str(certs_list)

            langs_list = c.get('languages', [])
            languages = ", ".join(langs_list) if isinstance(langs_list, list) else str(langs_list)

            summary = c.get('summary', '')[:200]  # Truncate for CSV readability
            university = c.get('university', '')
            grad_year = c.get('grad_year', '')

            work_history_list = c.get('work_history', [])
            work_history = "; ".join(
                [f"{w.get('title', '')} @ {w.get('company', '')} ({w.get('duration', '')})" 
                 for w in work_history_list]
            ) if isinstance(work_history_list, list) else ""

            rows.append([
                name, email, phone, location, experience, education, skills,
                match_score, status, linkedin, github, portfolio,
                certifications, languages, summary, university, grad_year,
                work_history, filename
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

        # 3. Export to an Excel-friendly CSV file
        csv_filename = 'vishesh_report.csv'
        with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write the column headers
            writer.writerow([
                'Name', 'Email', 'Phone', 'Location', 'Experience', 'Education',
                'Skills', 'Match Score', 'Status', 'LinkedIn', 'GitHub', 'Portfolio',
                'Certifications', 'Languages', 'Summary', 'University', 'Graduation Year',
                'Work History', 'Filename'
            ])
            # Write all the data
            writer.writerows(rows)

        print(f"\n [Success] Successfully exported {len(rows)} processed profiles!")
        print(f" [Folder] A new file named '{csv_filename}' has been created in your folder.")
        print(f" [Columns] 19 columns including all 18 extraction layers.")

    except Exception as e:
        print(f"Error reading JSON: {e}")

if __name__ == "__main__":
    generate_vishesh_report()