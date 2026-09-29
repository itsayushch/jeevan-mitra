import os
import tempfile
import unittest
import pytest
from fastapi.testclient import TestClient
from app.config import settings
from app.database import get_db
from app.main import app
from app.dependencies.auth import get_current_actor
from app.services.session_service import SessionService
from app.ai_layers.layer3_matching.state_machine import MatchStateMachine, UnauthorizedStateTransitionError

class TestPythonBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_database_path = settings.DATABASE_PATH
        cls.original_ai_provider = settings.AI_PROVIDER
        cls.original_worker_api_key = settings.WORKER_API_KEY
        cls.original_worker_id = settings.WORKER_ID
        cls.original_worker_name = settings.WORKER_NAME
        cls.original_officer_api_key = settings.OFFICER_API_KEY
        cls.original_officer_district = settings.OFFICER_DISTRICT
        cls.database_directory = tempfile.TemporaryDirectory()
        settings.DATABASE_PATH = os.path.join(cls.database_directory.name, 'test.db')
        settings.AI_PROVIDER = 'mock'
        settings.WORKER_API_KEY = 'test-worker-api-key'
        settings.WORKER_ID = 'test-worker-01'
        settings.WORKER_NAME = 'Test Field Worker'
        settings.OFFICER_API_KEY = 'test-officer-api-key'
        settings.OFFICER_DISTRICT = 'Moradabad'
        cls.client = TestClient(app, headers={'X-Worker-API-Key': settings.WORKER_API_KEY})
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.client.__exit__(None, None, None)
        finally:
            settings.DATABASE_PATH = cls.original_database_path
            settings.AI_PROVIDER = cls.original_ai_provider
            settings.WORKER_API_KEY = cls.original_worker_api_key
            settings.WORKER_ID = cls.original_worker_id
            settings.WORKER_NAME = cls.original_worker_name
            settings.OFFICER_API_KEY = cls.original_officer_api_key
            settings.OFFICER_DISTRICT = cls.original_officer_district
            cls.database_directory.cleanup()

    @pytest.mark.security
    def test_untrusted_headers_do_not_create_privileged_or_beneficiary_actors(self):
        for forged_key in ("admin-attacker", "counselor-attacker"):
            with self.subTest(api_key=forged_key):
                actor = get_current_actor(
                    x_session_id=None,
                    x_session_token=None,
                    x_worker_api_key=forged_key,
                    x_beneficiary_id=None,
                    authorization=None
                )
                self.assertEqual(actor.actor_role, "anonymous")

        actor = get_current_actor(
            x_session_id=None,
            x_session_token=None,
            x_worker_api_key=None,
            x_beneficiary_id="ben_rajesh_kumar",
            authorization=None
        )
        self.assertEqual(actor.actor_role, "anonymous")

    @pytest.mark.security
    def test_session_id_is_not_a_session_credential(self):
        with get_db() as conn:
            session = SessionService.create_session(conn)

        actor_from_id = get_current_actor(
            x_session_id=session["session_id"],
            x_session_token=None,
            x_worker_api_key=None,
            x_beneficiary_id=None,
            authorization=None
        )
        self.assertEqual(actor_from_id.actor_role, "anonymous")
        self.assertNotEqual(actor_from_id.actor_id, session["session_id"])

        actor_from_token = get_current_actor(
            x_session_id=None,
            x_session_token=session["session_token"],
            x_worker_api_key=None,
            x_beneficiary_id=None,
            authorization=None
        )
        self.assertEqual(actor_from_token.actor_id, session["session_id"])

    def test_health_check(self):
        res = self.client.get('/api/v1/health')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'operational')
        
        res = self.client.get('/api/v1/ready')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'ready')
        self.assertEqual(data['verifiedMatchProtocol'], 'enforced')
        self.assertIn('sixLayersStatus', data)

    def test_catalogue_qualifications(self):
        res = self.client.get('/api/v1/catalogue/qualifications')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data['qualifications'], list)
        self.assertGreater(len(data['qualifications']), 0)

    def test_seeded_referral_references_recommendation(self):
        with get_db() as conn:
            count = conn.execute("""
                SELECT COUNT(*)
                FROM referrals r
                JOIN recommendations rec ON rec.id = r.recommendation_id
                WHERE r.id = 'ref_rajesh_01';
            """).fetchone()[0]

        self.assertEqual(count, 1)

    def test_interview_start_requires_affirmative_consent(self):
        beneficiary = self.client.post('/api/v1/beneficiaries', json={
            'name': 'Consent Test',
            'district': 'Moradabad',
            'block': 'Chhajlet'
        })
        self.assertEqual(beneficiary.status_code, 201)

        response = self.client.post('/api/v1/interview/start', json={
            'beneficiary_id': beneficiary.json()['id']
        })

        self.assertEqual(response.status_code, 403)

    def test_withdrawn_consent_blocks_interview_operations(self):
        beneficiary_id = 'ben_rajesh_kumar'
        started = self.client.post('/api/v1/interview/start', json={
            'beneficiary_id': beneficiary_id
        })
        self.assertEqual(started.status_code, 201)
        session_id = started.json()['session_id']

        withdrawal = self.client.post('/api/v1/consents', json={
            'beneficiary_id': beneficiary_id,
            'purpose': 'PM-AJAY livelihood guidance',
            'dpdp_affirmative_consent': False
        })
        self.assertEqual(withdrawal.status_code, 201)

        self.assertEqual(self.client.post('/api/v1/interview/start', json={
            'beneficiary_id': beneficiary_id
        }).status_code, 403)
        self.assertEqual(self.client.post('/api/v1/interview/turn', json={
            'session_id': session_id,
            'text_input': 'I completed class ten'
        }).status_code, 403)
        self.assertEqual(self.client.get(f'/api/v1/interview/extract/{session_id}').status_code, 403)
        self.assertEqual(self.client.post('/api/v1/interview/confirm', json={
            'session_id': session_id,
            'beneficiary_id': beneficiary_id,
            'confirmed_fields': {'education_level': 'Class 10'}
        }).status_code, 403)
        self.assertEqual(self.client.get(f'/api/v1/interview/session/{session_id}').status_code, 403)

    def test_interview_start_returns_not_found_for_unknown_beneficiary(self):
        response = self.client.post('/api/v1/interview/start', json={
            'beneficiary_id': 'ben_does_not_exist'
        })

        self.assertEqual(response.status_code, 404)

    @pytest.mark.security
    def test_worker_verification_is_required_before_referral(self):
        consent = self.client.post('/api/v1/consents', json={
            'beneficiary_id': 'ben_rajesh_kumar',
            'purpose': 'PM-AJAY livelihood guidance',
            'dpdp_affirmative_consent': True
        })
        self.assertEqual(consent.status_code, 201)

        with get_db() as conn:
            conn.execute("DELETE FROM referrals WHERE recommendation_id = 'rec_seed_01';")
            conn.execute("UPDATE recommendations SET match_state = 'Interest Match' WHERE id = 'rec_seed_01';")
            conn.execute("UPDATE local_opportunities SET verified_by_worker_id = NULL WHERE id = 'opp_mushroom_chhajlet_07';")

        referral_payload = {
            'recommendation_id': 'rec_seed_01',
            'local_opportunity_id': 'opp_mushroom_chhajlet_07',
            'caste_document_verified': True,
            'income_criteria_verified': True,
            'residence_proof_verified': True
        }
        denied = self.client.post(
            '/api/v1/worker/cases/ben_rajesh_kumar/referral',
            json=referral_payload,
            headers={'X-Worker-API-Key': 'incorrect-key'}
        )
        self.assertEqual(denied.status_code, 403)

        before_verification = self.client.post(
            '/api/v1/worker/cases/ben_rajesh_kumar/referral', json=referral_payload
        )
        self.assertEqual(before_verification.status_code, 409)

        verification = self.client.post(
            '/api/v1/worker/opportunities/opp_mushroom_chhajlet_07/verify',
            json={'available_seats': 6, 'batch_status': 'upcoming', 'notes': 'Confirmed with centre manager'}
        )
        self.assertEqual(verification.status_code, 200)
        self.assertTrue(verification.json()['verified'])

        with get_db() as conn:
            recommendation = conn.execute(
                "SELECT match_state FROM recommendations WHERE id = 'rec_seed_01';"
            ).fetchone()
            audit_count = conn.execute("""
                SELECT COUNT(*) FROM audit_events
                WHERE entity_type = 'local_opportunities'
                  AND entity_id = 'opp_mushroom_chhajlet_07'
                  AND action = 'opportunity_verification_updated';
            """).fetchone()[0]
        self.assertEqual(recommendation['match_state'], 'Verified Match')
        self.assertEqual(audit_count, 1)

        created = self.client.post(
            '/api/v1/worker/cases/ben_rajesh_kumar/referral', json=referral_payload
        )
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.json()['status'], 'documents_verified')

        revoked = self.client.post(
            '/api/v1/worker/opportunities/opp_mushroom_chhajlet_07/verify',
            json={'available_seats': 0, 'batch_status': 'full', 'notes': 'Centre confirmed batch is full'}
        )
        self.assertEqual(revoked.status_code, 200)
        self.assertFalse(revoked.json()['verified'])
        stale = self.client.post(
            '/api/v1/worker/cases/ben_rajesh_kumar/referral', json=referral_payload
        )
        self.assertEqual(stale.status_code, 409)

    def test_matching_does_not_trust_unverified_opportunities(self):
        with get_db() as conn:
            conn.execute("UPDATE local_opportunities SET verified_by_worker_id = NULL;")

        response = self.client.post('/api/v1/recommendations/match', json={
            'beneficiaryId': 'ben_rajesh_kumar',
            'district': 'Moradabad',
            'block': 'Chhajlet',
            'educationLevel': 'Class 10',
            'interests': ['farming', 'mushroom'],
            'skills': ['farming'],
            'mobilityRadiusKm': 10,
            'workPreference': 'both'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['recommendations'])
        self.assertTrue(all(
            item['match_state'] == 'Interest Match'
            for item in response.json()['recommendations']
        ))

    def test_planning_matrix(self):
        # Seed anonymised demand records so the matrix has real query data
        with get_db() as conn:
            conn.executemany("""
                INSERT OR REPLACE INTO demand_records
                (id, qualification_id, district, block, mobility_radius_km,
                 work_preference, had_verified_match, period, created_at)
                VALUES (?, 'qual_mushroom_07', 'Moradabad', 'Chhajlet', 10.0, 'both', 1, 'FY 2026-27', ?);
            """, [(f"it_dem_{i}", "2026-09-01T00:00:00+00:00") for i in range(6)])

        res = self.client.get('/api/v1/planning/supply-gap-matrix?district=Moradabad',
                              headers={'X-Officer-API-Key': 'test-officer-api-key'})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('matrix', data)
        self.assertIn('metrics', data)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['metrics']['total_demand_records'], 6)
        self.assertTrue(data['gap_scoring']['formula'])

        # Unauthenticated call is rejected
        anon = self.client.get('/api/v1/planning/supply-gap-matrix?district=Moradabad')
        self.assertEqual(anon.status_code, 403)

    def test_chat_endpoint(self):
        res = self.client.post('/api/v1/chat', json={'message': 'hello sahayak', 'language': 'en'})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('reply', data)

    def test_claim1_state_machine_guard(self):
        # AI / system actor cannot self-promote to Verified Match
        with self.assertRaises(UnauthorizedStateTransitionError):
            MatchStateMachine.validate_transition(
                current_state='Interest Match',
                target_state='Verified Match',
                actor_role='system',
                has_confirmed_opportunity=True
            )

        # Beneficiary cannot self-promote to Verified Match
        with self.assertRaises(UnauthorizedStateTransitionError):
            MatchStateMachine.validate_transition(
                current_state='Interest Match',
                target_state='Verified Match',
                actor_role='beneficiary',
                has_confirmed_opportunity=True
            )

        # Authorized field worker succeeds when confirmed opportunity exists
        MatchStateMachine.validate_transition(
            current_state='Interest Match',
            target_state='Verified Match',
            actor_role='field_worker',
            has_confirmed_opportunity=True
        )

if __name__ == '__main__':
    unittest.main()
