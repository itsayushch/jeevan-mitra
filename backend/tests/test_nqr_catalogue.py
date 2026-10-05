import json
from datetime import date

from app.db.session import get_db
from app.services.catalogue_service import CatalogueService
from app.services.nqr_catalogue import import_catalogue, is_current
from app.services.nqr_rag_service import NQRRagService
from tests.test_live_interview import live_interview, complete


def test_official_catalogue_import_is_idempotent_and_has_no_invented_batches(client):
    with get_db() as conn:
        import_catalogue(conn)
        import_catalogue(conn)
        rows = CatalogueService.list_qualifications(conn)
        assert len(rows) == 7
        sewing = next(row for row in rows if row['id'] == 'nqr_10422')
        assert sewing['duration_hours'] == 300
        assert sewing['nsqf_level'] == 2.5
        assert sewing['min_education_rank'] == 3
        assert sewing['official_source_url'] == 'https://www.nqr.gov.in/qualifications/10422'
        assert json.loads(sewing['entry_requirements_json'])['valid_to'] == '2026-11-01'
        assert all(row['source_name'] == 'National Qualification Register (NCVET)' for row in rows)
        assert conn.execute('SELECT COUNT(*) AS n FROM local_opportunities').fetchone()['n'] == 0
    response = client.get('/api/v1/qualifications')
    assert response.status_code == 200
    assert next(row for row in response.json() if row['id'] == 'nqr_10422')['nsqf_level'] == 2.5


def test_expiry_uses_validity_date_and_never_assumes_malformed_dates_are_valid():
    qual = {'verification_status': 'VERIFIED', 'entry_requirements_json': '{"valid_to":"2026-11-01"}'}
    assert is_current(qual, date(2026, 11, 1))
    assert not is_current(qual, date(2026, 11, 2))
    qual['entry_requirements_json'] = '{"valid_to":"unknown"}'
    assert not is_current(qual)


def test_retiring_demo_records_keeps_history(client):
    with get_db() as conn:
        # Use an existing official row as a template for the known legacy seed ID.
        conn.execute("UPDATE qualifications SET id = 'qual_sewing_02' WHERE id = 'nqr_10422'")
        conn.execute("UPDATE qualifications SET nqr_code = 'legacy-demo', external_reference = 'legacy-demo' WHERE id = 'qual_sewing_02'")
        import_catalogue(conn)
        old = conn.execute("SELECT * FROM qualifications WHERE id = 'qual_sewing_02'").fetchone()
        assert old is not None
        assert not is_current(dict(old))
        assert len(CatalogueService.list_qualifications(conn)) == 7


def test_rag_uses_official_snapshot_instead_of_mock_curricula():
    docs = NQRRagService().documents
    sewing = next(doc for doc in docs if doc['course'] == 'Sewing Machine Operator')
    facts = json.loads(sewing['content'])
    assert facts['duration_hours'] == 300
    assert facts['source_url'].endswith('/10422')
    assert facts['local_batch'].startswith('Not verified')
    assert all(doc['id'].isdigit() for doc in docs)


def test_matching_and_saved_dashboard_use_current_official_courses(client, live_interview):
    profile = complete(client, live_interview)
    interview_id, headers = live_interview
    client.post(f'/api/v1/interviews/{interview_id}/confirm-profile', headers=headers,
                json={'confirmed_fields': profile})
    result = client.post('/api/v1/recommendations/generate', headers=headers,
                         json={'interview_id': interview_id})
    assert result.status_code == 200
    courses = result.json()['recommendations']
    assert courses
    sewing = next(item for item in courses if item['qualification']['title'] == 'Sewing Machine Operator')
    assert sewing['qualification']['duration_hours'] == 300
    assert sewing['qualification']['nsqf_level'] == 2.5
    assert all(item['local_availability']['status'] == 'unknown' for item in courses)
    assert all(item['local_availability']['centre_name'] is None for item in courses)
    assert all(item['qualification']['official_url'].startswith('https://www.nqr.gov.in/qualifications/') for item in courses)
    assert all(fact['factor'] not in ('TRAVEL_FEASIBILITY', 'LOCATION_RELEVANCE', 'VERIFIED_LOCAL_AVAILABILITY')
               for item in courses for fact in item['explanationFacts'])
    with get_db() as conn:
        conn.execute("UPDATE qualifications SET entry_requirements_json = ? WHERE id = 'nqr_10422'",
                     ('{"valid_to":"2020-01-01"}',))
    saved = client.get(f'/api/v1/interviews/{interview_id}/recommendations', headers=headers).json()
    assert all(item['qualification']['title'] != 'Sewing Machine Operator' for item in saved['recommendations'])
