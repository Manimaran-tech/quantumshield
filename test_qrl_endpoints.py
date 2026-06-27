import unittest
import json
from app import app

class QRLApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_qrl_circuit(self):
        response = self.app.post('/api/qrl/circuit', json={
            'smiles': 'c1cc(ccn1)C(=O)NN',
            'pathogen_name': 'Tuberculosis'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('circuit_ascii', data)
        self.assertIn('circuit_svg', data)
        self.assertIsInstance(data['circuit_ascii'], str)
        self.assertIsInstance(data['circuit_svg'], str)
        self.assertTrue(data['circuit_svg'].startswith('<svg') or '<svg' in data['circuit_svg'])
        print("QRL Circuit draw test passed!")

    def test_qrl_optimize(self):
        response = self.app.post('/api/qrl/optimize', json={
            'smiles': 'c1cc(ccn1)C(=O)NN',
            'pathogen_name': 'Tuberculosis',
            'epochs': 1
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('circuit_ascii', data)
        self.assertIn('circuit_svg', data)
        self.assertIsInstance(data['circuit_svg'], str)
        self.assertTrue(data['circuit_svg'].startswith('<svg') or '<svg' in data['circuit_svg'])
        print("QRL Optimize test passed!")

if __name__ == '__main__':
    unittest.main()
