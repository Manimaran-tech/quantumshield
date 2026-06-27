import unittest
import json
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app

class TestWetLabQRLEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_qrl_optimize_endpoint(self):
        print("Testing /api/qrl/optimize endpoint...")
        payload = {
            "seed_smiles": "c1cc(ccn1)C(=O)NN",
            "episodes": 2
        }
        response = self.app.post('/api/qrl/optimize', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("optimized_smiles", data)
        self.assertIn("history", data)
        self.assertIn("recommended_candidate", data)
        self.assertTrue(len(data["history"]) > 0)
        print("  [OK] /api/qrl/optimize")
    
    def test_md_trajectory_endpoint(self):
        print("Testing /api/md/trajectory endpoint...")
        payload = {
            "molecule_id": "hydrazine",
            "custom_coords": None
        }
        response = self.app.post('/api/md/trajectory', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("trajectory", data)
        self.assertIn("stability_score", data)
        self.assertIn("h_bonds", data)
        self.assertIn("rmsd_trajectory", data)
        print("  [OK] /api/md/trajectory")
        
    def test_validation_wetlab_endpoint(self):
        print("Testing /api/validation/wetlab endpoint...")
        payload = {
            "smiles": "c1cc(ccn1)C(=O)NN",
            "pathogen_name": "Tuberculosis"
        }
        response = self.app.post('/api/validation/wetlab', 
                                 data=json.dumps(payload),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("predicted_kd_text", data)
        self.assertIn("predicted_kd_value", data)
        self.assertIn("concs_uM", data)
        self.assertIn("measured_binding", data)
        self.assertIn("sa_score", data)
        self.assertIn("admet_twin", data)
        print("  [OK] /api/validation/wetlab")
        
if __name__ == '__main__':
    unittest.main()
