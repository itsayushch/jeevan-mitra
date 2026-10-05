"""Offline NQR snapshot, with source provenance and validity checks."""
import json
from datetime import date
from pathlib import Path

SNAPSHOT = Path(__file__).resolve().parents[1] / "data" / "nqr_catalogue.json"
DEMO_IDS = ["qual_solar_01", "qual_sewing_02", "qual_elec_03", "qual_food_04",
            "qual_tractor_05", "qual_retail_06", "qual_mushroom_07", "qual_plumber_08",
            "qual_gda_09", "qual_dataentry_10", "qual_beauty_11", "qual_welder_12"]


def load_snapshot():
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def is_current(qualification, today=None):
    if str(qualification.get("verification_status", "")).upper() != "VERIFIED":
        return False
    try:
        requirements = json.loads(qualification.get("entry_requirements_json") or "{}")
        valid_to = requirements.get("valid_to")
        return not valid_to or date.fromisoformat(valid_to) >= (today or date.today())
    except (ValueError, TypeError):
        return False


def import_catalogue(conn):
    """Idempotent import; retain historical IDs/references, retire only known seed records."""
    snapshot = load_snapshot()
    checked = snapshot["checked_at"]
    for demo_id in DEMO_IDS:
        conn.execute("UPDATE qualifications SET verification_status = 'deprecated' WHERE id = ?", (demo_id,))
        conn.execute("UPDATE local_opportunities SET status = 'ARCHIVED', is_archived = 1 WHERE qualification_id = ? AND source = 'pm_ajay_portal'", (demo_id,))
    for item in snapshot["records"]:
        skills = json.dumps(item["skills"], ensure_ascii=False)
        criteria = "; OR ".join(" / ".join(route.values()) for route in item["entry_routes"])
        requirements = json.dumps({"routes": item["entry_routes"], "valid_to": item["valid_to"],
                                   "matching_note": "School-entry route only; alternative experience routes require review."})
        values = {"nqr_code": item["nqr_code"], "title": item["title"], "sector": item["sector"],
                  "nsqf_level": item["nsqf_level"], "duration_hours": item["duration_hours"],
                  "min_education": item["min_education"], "min_education_rank": item["min_education_rank"],
                  # Internal matching defaults, not promises of work or accessibility from NQR.
                  "work_type": "both", "physical_intensity": "medium",
                  "skills_acquired": skills, "skills_json": skills, "entry_requirements_json": requirements,
                  "curriculum_summary": item["description"], "description": item["description"],
                  "entry_criteria": criteria, "certification_body": item["certification_body"],
                  "nqr_link": item["source_url"],
                  "source_name": "National Qualification Register (NCVET)", "source_url": item["source_url"],
                  "external_reference": str(item["record_id"]), "source_version": item["nqr_code"],
                  "source_verified_at": checked + "T00:00:00Z", "verification_date": checked,
                  "verification_status": "VERIFIED" if item["valid_to"] >= date.today().isoformat() else "deprecated",
                  "updated_at": checked}
        record_id = f"nqr_{item['record_id']}"
        existing = conn.execute("SELECT id FROM qualifications WHERE id = ?", (record_id,)).fetchone()
        if existing:
            conn.execute("UPDATE qualifications SET " + ", ".join(f"{key} = ?" for key in values) + " WHERE id = ?",
                         (*values.values(), record_id))
        else:
            values = {"id": record_id, "created_at": checked, **values}
            conn.execute("INSERT INTO qualifications (" + ", ".join(values) + ") VALUES (" + ", ".join("?" for _ in values) + ")",
                         tuple(values.values()))
    return len(snapshot["records"])
