import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.ai_layers.layer3_matching.state_machine import MatchStateMachine, UnauthorizedStateTransitionError

class TestPythonBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'operational')
        self.assertEqual(data['verifiedMatchProtocol'], 'enforced')
        self.assertIn('sixLayersStatus', data)

    def test_catalogue_qualifications(self):
        res = self.client.get('/api/catalogue/qualifications')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data['qualifications'], list)
        self.assertGreater(len(data['qualifications']), 0)

    def test_planning_matrix(self):
        res = self.client.get('/api/planning/supply-gap-matrix?district=Moradabad')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('matrix', data)
        self.assertIn('metrics', data)
        self.assertGreater(data['metrics']['beneficiaries_interviewed'], 0)

    def test_chat_endpoint(self):
        res = self.client.post('/api/chat', json={'message': 'hello sahayak', 'language': 'en'})
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
