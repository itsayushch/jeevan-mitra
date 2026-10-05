"""Refresh a small, auditable NQR snapshot. Run from backend; no batch data is inferred."""
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

RECORDS = [10422, 10741, 13370, 13356, 13295, 13360, 14080]


def clean(value):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def fetch_record(client, record_id):
    url = f"https://www.nqr.gov.in/qualifications/{record_id}"
    response = client.get(url)
    response.raise_for_status()
    source = response.text
    text = clean(source)
    title = clean(re.search(r"<h1[^>]*>(.*?)</h1>", source, re.S)[1])
    code = clean(re.search(r"NQR Code:\s*<span[^>]*>(.*?)</span>", source, re.S)[1])
    tables = re.findall(r"<table[^>]*>(.*?)</table>", source, re.S)
    rows = [[[clean(cell) for cell in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
             for row in re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.S)] for table in tables]
    routes = [dict(zip(["education", "completion", "experience", "training"], row)) for row in rows[0][1:]]
    # Matching uses only an unambiguous school-entry route, never assumes work experience.
    grades = [int(re.match(r"(\d+)", r["education"])[1]) for r in routes
              if re.match(r"\d+th$", r["education"]) and r["experience"] == "No Experience"
              and r["completion"] in ("None", "Passed", "Completed") and r["training"] in ("None", "Equivalent")]
    if not grades:
        raise ValueError(f"No supported school-entry route for {title}")
    grade = min(grades)
    valid_to = datetime.strptime(re.search(r"Valid Till:\s*(\d{2}/\d{2}/\d{4})", text)[1], "%d/%m/%Y").date().isoformat()
    level = float(re.search(r"Level\s+Level\s+([\d.]+)", text)[1])
    hours = int(re.search(r"Notional Hours Maximum\s*:\s*(\d+)", text)[1])
    minimum = int(re.search(r"Notional Hours.*?Minimum\s*:\s*(\d+)", text)[1])
    if hours != minimum:
        raise ValueError(f"Variable duration needs review: {title}")
    return {"record_id": record_id, "title": title, "nqr_code": code,
            "sector": re.search(r"Valid Till:.*?Sector\s+(.+?)\s+Level", text)[1], "nsqf_level": level,
            "duration_hours": hours, "min_education": f"Class {grade}",
            "min_education_rank": 4 if grade >= 12 else 3 if grade >= 9 else 2 if grade >= 8 else 1,
            "entry_routes": routes, "valid_to": valid_to,
            "skills": [row[0] for row in rows[1][1:] if row and row[0] not in ("OJT", "OJT (Mandatory)")],
            "description": re.search(r"Job Description\s+(.+?)\s+Eligibility Criteria", text)[1],
            "certification_body": re.search(r"Awarding Bodies\s+(.+?)\s+Type of Organisation", text)[1],
            "source_url": url}


if __name__ == "__main__":
    with httpx.Client(timeout=40, follow_redirects=True) as client:
        records = [fetch_record(client, record_id) for record_id in RECORDS]
    snapshot = {"checked_at": datetime.now(timezone.utc).date().isoformat(), "records": records}
    target = Path(__file__).resolve().parents[1] / "app" / "data" / "nqr_catalogue.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(records)} official NQR records to {target}")
