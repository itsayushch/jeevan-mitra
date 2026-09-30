import pytest
import uuid
import json
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.core.security import create_access_token


@pytest.fixture
def planning_db():
    """Seed clean database with test data for district planning verification."""
    with get_db() as conn:
        now_iso = datetime.now(timezone.utc).isoformat()
        future_iso = (datetime.now(timezone.utc) + timedelta(days=60)).isoformat()

        # Seed Users
        # 1. Super admin
        conn.execute("""
            INSERT OR REPLACE INTO users (id, email, phone, display_name, is_active, preferred_language, created_at, updated_at)
            VALUES ('usr_admin_global', 'super@up.gov.in', '9999990001', 'Global Super Admin', 1, 'en', ?, ?);
        """, (now_iso, now_iso))
        conn.execute("INSERT OR REPLACE INTO user_roles (user_id, role_id, assigned_at) VALUES ('usr_admin_global', 'role_super_admin', ?);", (now_iso,))

        # 2. Moradabad District Admin
        conn.execute("""
            INSERT OR REPLACE INTO users (id, email, phone, display_name, is_active, preferred_language, created_at, updated_at)
            VALUES ('usr_admin_mbd', 'admin.mbd@up.gov.in', '9999990002', 'Moradabad Admin', 1, 'hi', ?, ?);
        """, (now_iso, now_iso))
        conn.execute("INSERT OR REPLACE INTO user_roles (user_id, role_id, assigned_at) VALUES ('usr_admin_mbd', 'role_district_admin', ?);", (now_iso,))
        conn.execute("""
            INSERT OR REPLACE INTO user_scopes (id, user_id, district_id, scope_type, assigned_at)
            VALUES ('scope_admin_mbd', 'usr_admin_mbd', 'Moradabad', 'district', ?);
        """, (now_iso,))

        # 3. Field Worker (unprivileged for planning)
        conn.execute("""
            INSERT OR REPLACE INTO users (id, email, phone, display_name, is_active, preferred_language, created_at, updated_at)
            VALUES ('usr_worker_mbd', 'worker.mbd@up.gov.in', '9999990003', 'Field Worker Moradabad', 1, 'hi', ?, ?);
        """, (now_iso, now_iso))
        conn.execute("INSERT OR REPLACE INTO user_roles (user_id, role_id, assigned_at) VALUES ('usr_worker_mbd', 'role_field_worker', ?);", (now_iso,))

        # 4. Seed Beneficiaries (at least 6 for solar in Moradabad to pass k=5 privacy threshold)
        for i in range(1, 8):
            b_id = f"ben_mbd_{i}"
            conn.execute("""
                INSERT OR REPLACE INTO beneficiaries (
                    id, name, phone, district, block, preferred_language, created_at, updated_at
                ) VALUES (?, ?, ?, 'Moradabad', 'Chhajlet', 'hi', ?, ?);
            """, (b_id, f"Beneficiary {i}", f"980000000{i}", now_iso, now_iso))

            # Recommendation for solar
            conn.execute("""
                INSERT OR REPLACE INTO recommendations (
                    id, beneficiary_id, qualification_id, local_opportunity_id,
                    rank, score, score_breakdown, match_state, explanation_text,
                    audio_explanation_script, tradeoff_summary, skill_gap_summary,
                    data_snapshot, local_opportunity_status, explanation_facts,
                    created_at, updated_at
                ) VALUES (
                    ?, ?, 'qual_solar_01', 'opp_solar_moradabad_01',
                    1, 92.0, '{}', 'VERIFIED_MATCH', 'Solar PV Installer matches your background',
                    'Audio explanation script', 'Local batch available', 'Minimal skill gaps',
                    '{}', 'ACTIVE', '["Confirmed 10th pass", "Local opportunity in Moradabad"]',
                    ?, ?
                );
            """, (f"rec_mbd_{i}", b_id, now_iso, now_iso))

        # 7. Seed Opportunity Submissions (multimodal)
        conn.execute("""
            INSERT OR REPLACE INTO opportunity_submissions (
                id, submitted_by_user_id, input_mode, raw_text, normalized_text,
                locale, status, created_at, updated_at
            ) VALUES (
                'sub_voice_1', 'usr_admin_mbd', 'voice', 'Solar training centre near market',
                'Solar training centre near market', 'hi', 'SUBMITTED', ?, ?
            );
        """, (now_iso, now_iso))
        conn.execute("""
            INSERT OR REPLACE INTO opportunity_submissions (
                id, submitted_by_user_id, input_mode, raw_text, normalized_text,
                locale, status, created_at, updated_at
            ) VALUES (
                'sub_text_1', 'usr_admin_mbd', 'text', 'Electrician workshop training',
                'Electrician workshop training', 'en', 'REVIEWED', ?, ?
            );
        """, (now_iso, now_iso))

        # 8. Seed Explanation Cache
        conn.execute("""
            INSERT OR REPLACE INTO recommendation_explanation_cache (
                id, recommendation_id, locale, renderer, rendered_text, created_at
            ) VALUES (
                'exp_c_1', 'rec_mbd_1', 'hi', 'template', '{"summary": "सिफारिश"}', ?
            );
        """, (now_iso,))


def _get_auth_headers(user_id: str, role: str) -> dict:
    token = create_access_token(
        subject=user_id,
        session_id=f"sess_{uuid.uuid4().hex[:8]}",
        expires_delta=timedelta(hours=2)
    )
    return {"Authorization": f"Bearer {token}"}


class TestDistrictPlanningAccessControl:
    """Verify role and geographic access boundaries."""

    def test_unauthenticated_request_rejected(self, planning_db):
        client = TestClient(app)
        res = client.get("/api/v1/planning/overview?district_id=Moradabad")
        assert res.status_code == 401

    def test_unauthorized_role_rejected(self, planning_db):
        client = TestClient(app)
        headers = _get_auth_headers("usr_worker_mbd", "field_worker")
        res = client.get("/api/v1/planning/overview?district_id=Moradabad", headers=headers)
        assert res.status_code == 403
        assert "Forbidden" in res.json()["detail"]

    def test_district_admin_own_district_allowed(self, planning_db):
        client = TestClient(app)
        headers = _get_auth_headers("usr_admin_mbd", "district_admin")
        res = client.get("/api/v1/planning/overview?district_id=Moradabad", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["metadata"]["district_id"] == "Moradabad"

    def test_district_admin_other_district_forbidden(self, planning_db):
        client = TestClient(app)
        headers = _get_auth_headers("usr_admin_mbd", "district_admin")
        res = client.get("/api/v1/planning/overview?district_id=Varanasi", headers=headers)
        assert res.status_code == 403
        assert "Access denied" in res.json()["detail"]

    def test_super_admin_any_district_allowed(self, planning_db):
        client = TestClient(app)
        headers = _get_auth_headers("usr_admin_global", "super_admin")
        res = client.get("/api/v1/planning/overview?district_id=Varanasi", headers=headers)
        assert res.status_code == 200
        assert res.json()["metadata"]["district_id"] == "Varanasi"


class TestDistrictPlanningAggregations:
    """Verify authoritative demand, supply, gaps, and data quality metrics."""

    def test_demand_report_aggregation(self, planning_db):
        client = TestClient(app)
        headers = _get_auth_headers("usr_admin_mbd", "district_admin")
        res = client.get("/api/v1/planning/demand?district_id=Moradabad", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data["demand"]) >= 1
        solar_item = next((d for d in data["demand"] if d["qualification_id"] == "qual_solar_01"), None)
        assert solar_item is not None
        assert solar_item["verified_match_count"] >= 5
        assert solar_item["is_suppressed"] is False

    def test_supply_report_aggregation(self, planning_db):
        client = TestClient(app)
        headers = _get_auth_headers("usr_admin_mbd", "district_admin")
        res = client.get("/api/v1/planning/supply?district_id=Moradabad", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data["supply"]) >= 1
        solar_supply = next((s for s in data["supply"] if s["qualification_id"] == "qual_solar_01"), None)
        assert solar_supply is not None
        assert solar_supply["available_capacity"] == 14

    def test_gap_report_aggregation(self, planning_db):
        client = TestClient(app)
        headers = _get_auth_headers("usr_admin_mbd", "district_admin")
        res = client.get("/api/v1/planning/gaps?district_id=Moradabad", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data["gaps"]) >= 1
        solar_gap = next((g for g in data["gaps"] if g["qualification_id"] == "qual_solar_01"), None)
        assert solar_gap is not None
        assert solar_gap["available_verified_capacity"] == 14

    def test_data_quality_and_accessibility_dimensions(self, planning_db):
        client = TestClient(app)
        headers = _get_auth_headers("usr_admin_mbd", "district_admin")
        res = client.get("/api/v1/planning/data-quality?district_id=Moradabad", headers=headers)
        assert res.status_code == 200
        data = res.json()
        dq = data["data_quality"]

        # 1. Core hygiene counts
        assert "stale_or_expired_opportunities_count" in dq
        assert "opportunities_due_reverification_count" in dq

        # 2. Language distribution (k-threshold applied)
        assert "language_distribution" in dq
        assert "hi" in dq["language_distribution"]
        # Beneficiaries in Moradabad seeded with hi: count 7 >= 5, so not suppressed
        assert dq["language_distribution"]["hi"] >= 5

        # 3. Multimodal opportunity submissions
        assert "opportunity_submissions_by_mode" in dq
        assert "opportunity_submissions_by_status" in dq

        # 4. Explainability quality (strictly no raw text)
        assert "explainability_quality" in dq
        eq = dq["explainability_quality"]
        assert "total_cached_explanations" in eq
        assert "template_count" in eq
        assert "recommendations_with_confirmed_facts" in eq
        assert eq["recommendations_with_confirmed_facts"] >= 7


class TestPlanningSnapshotsLifecycle:
    """Verify immutable snapshot generation, review, approval, and metrics ingestion."""

    def test_full_snapshot_lifecycle(self, planning_db):
        client = TestClient(app)
        admin_headers = _get_auth_headers("usr_admin_mbd", "district_admin")

        # 1. Create snapshot
        create_payload = {
            "district_id": "Moradabad",
            "period_start": "2026-01-01",
            "period_end": "2026-12-31",
            "notes": "Q1 District Planning Review"
        }
        res_create = client.post("/api/v1/planning/snapshots", json=create_payload, headers=admin_headers)
        assert res_create.status_code == 201
        snap = res_create.json()
        snap_id = snap["id"]
        assert snap["status"] == "GENERATED"
        assert snap["district_id"] == "Moradabad"

        # Verify normalized metrics inserted into database
        with get_db() as conn:
            metric_rows = conn.execute("""
                SELECT metric_group, metric_key, metric_value 
                FROM planning_snapshot_metrics 
                WHERE snapshot_id = ?;
            """, (snap_id,)).fetchall()
            assert len(metric_rows) >= 5

        # 2. Review snapshot
        res_rev = client.post(
            f"/api/v1/planning/snapshots/{snap_id}/review",
            json={"notes": "Reviewed with NEDA coordinator"},
            headers=admin_headers
        )
        assert res_rev.status_code == 200
        assert res_rev.json()["status"] == "REVIEWED"
        assert res_rev.json()["reviewed_by_user_id"] == "usr_admin_mbd"

        # 3. Approve snapshot
        res_app = client.post(
            f"/api/v1/planning/snapshots/{snap_id}/approve",
            json={"notes": "Approved for district skilling committee"},
            headers=admin_headers
        )
        assert res_app.status_code == 200
        assert res_app.json()["status"] == "APPROVED"
        assert res_app.json()["approved_by_user_id"] == "usr_admin_mbd"

        # 4. List snapshots
        res_list = client.get("/api/v1/planning/snapshots?district_id=Moradabad", headers=admin_headers)
        assert res_list.status_code == 200
        snaps = res_list.json()
        assert any(s["id"] == snap_id for s in snaps)


class TestControlledExports:
    """Verify reproducible, tamper-evident CSV and PDF exports from immutable snapshots."""

    def test_csv_and_pdf_export_generation_and_download(self, planning_db):
        client = TestClient(app)
        admin_headers = _get_auth_headers("usr_admin_mbd", "district_admin")

        # 1. Create a snapshot first
        snap_res = client.post("/api/v1/planning/snapshots", json={
            "district_id": "Moradabad",
            "period_start": "2026-01-01",
            "period_end": "2026-12-31",
            "notes": "Export testing"
        }, headers=admin_headers)
        snap_id = snap_res.json()["id"]

        # 2. Generate CSV export
        csv_res = client.post(f"/api/v1/planning/snapshots/{snap_id}/exports/csv", headers=admin_headers)
        assert csv_res.status_code == 201
        csv_export = csv_res.json()
        assert csv_export["export_type"] == "CSV"
        assert csv_export["status"] == "GENERATED"
        assert csv_export["checksum"] is not None
        csv_id = csv_export["id"]

        # 3. Download CSV export
        dl_csv = client.get(f"/api/v1/planning/exports/{csv_id}/download", headers=admin_headers)
        assert dl_csv.status_code == 200
        assert dl_csv.headers["content-type"].startswith("text/csv")
        csv_text = dl_csv.text

        # Verify CSV contents: Checksum, Disclaimer, Privacy note, Sections
        actual_hash = hashlib.sha256(csv_text.encode("utf-8")).hexdigest()
        assert actual_hash == csv_export["checksum"]
        assert "JeevanMitra 2.0 District Planning Export" in csv_text
        assert "SECTION 1: DEMAND VS VERIFIED CAPACITY GAPS" in csv_text
        assert "SECTION 4: DATA QUALITY & ACCESSIBILITY METRICS" in csv_text
        assert "minimum cell-size privacy threshold of k = 5" in csv_text

        # Verify download count incremented
        meta_res = client.get(f"/api/v1/planning/exports/{csv_id}", headers=admin_headers)
        assert meta_res.status_code == 200
        assert meta_res.json()["download_count"] == 1

        # 4. Generate PDF export
        pdf_res = client.post(f"/api/v1/planning/snapshots/{snap_id}/exports/pdf", headers=admin_headers)
        assert pdf_res.status_code == 201
        pdf_export = pdf_res.json()
        assert pdf_export["export_type"] == "PDF"
        pdf_id = pdf_export["id"]

        # 5. Download PDF export
        dl_pdf = client.get(f"/api/v1/planning/exports/{pdf_id}/download", headers=admin_headers)
        assert dl_pdf.status_code == 200
        assert "PDF" in dl_pdf.text
        assert "DATA QUALITY & ACCESSIBILITY METRICS" in dl_pdf.text

    def test_unauthorized_user_cannot_download_export(self, planning_db):
        client = TestClient(app)
        admin_headers = _get_auth_headers("usr_admin_mbd", "district_admin")

        # Snapshot and export for Moradabad
        snap_res = client.post("/api/v1/planning/snapshots", json={
            "district_id": "Moradabad",
            "period_start": "2026-01-01",
            "period_end": "2026-12-31"
        }, headers=admin_headers)
        snap_id = snap_res.json()["id"]

        csv_res = client.post(f"/api/v1/planning/snapshots/{snap_id}/exports/csv", headers=admin_headers)
        export_id = csv_res.json()["id"]

        # Field worker attempt to download export should fail with 403
        worker_headers = _get_auth_headers("usr_worker_mbd", "field_worker")
        res_dl = client.get(f"/api/v1/planning/exports/{export_id}/download", headers=worker_headers)
        assert res_dl.status_code == 403
