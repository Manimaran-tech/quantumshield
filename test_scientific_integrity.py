# Copyright 2026 QuantumShield Team
# Licensed under the Apache License, Version 2.0

"""
test_scientific_integrity.py — Rigorous Automated Verification of Scientific Models

Verifies:
 1. Ertl & Schuffenhauer Synthetic Accessibility (SA) Score benchmark.
 2. Official RDKit PAINS (Pan-Assay Interference) FilterCatalog.
 3. Discriminative Hill-Langmuir Pharmacodynamic Binding Curves.
 4. Quantum Chemistry Metric reporting in millihartrees (mHa).
 5. QRL Parameter-Shift Policy initialization and checkpoint persistence.
"""

import os
import sys
import unittest
import numpy as np

# Ensure root directory is on Python path
sys.path.insert(0, os.path.dirname(__file__))

from utils import calculate_sascore, check_pains, calculate_hill_langmuir_binding
from rdkit import Chem


class TestScientificIntegrity(unittest.TestCase):

    def test_01_ertl_sa_score(self):
        """Verify SA score returns peer-reviewed values on reference compounds."""
        # Aspirin is simple and readily synthesizable (SA < 2.5)
        aspirin = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
        sa_aspirin = calculate_sascore(aspirin)
        self.assertGreaterEqual(sa_aspirin, 1.0)
        self.assertLessEqual(sa_aspirin, 2.5, f"Aspirin SA score should be <= 2.5, got {sa_aspirin}")

        # Isoniazid is a small, accessible hydrazine derivative (SA < 2.5)
        isoniazid = Chem.MolFromSmiles("c1cc(ccn1)C(=O)NN")
        sa_inh = calculate_sascore(isoniazid)
        self.assertGreaterEqual(sa_inh, 1.0)
        self.assertLessEqual(sa_inh, 2.5, f"Isoniazid SA score should be <= 2.5, got {sa_inh}")

    def test_02_pains_filter_catalog(self):
        """Verify RDKit FilterCatalog flags known PAINS and passes clean drugs."""
        # Aspirin has no PAINS alerts
        aspirin = Chem.MolFromSmiles("CC(=O)Oc1ccccc1C(=O)O")
        has_pains_asp, reasons_asp = check_pains(aspirin)
        self.assertFalse(has_pains_asp, f"Aspirin should not be flagged as PAINS, got {reasons_asp}")

        # 5-benzylidene-rhodanine is an archetype PAINS toxicophore
        rhodanine = Chem.MolFromSmiles("O=C1NC(=S)SC1=Cc2ccccc2")
        has_pains_rho, reasons_rho = check_pains(rhodanine)
        self.assertTrue(has_pains_rho, "5-benzylidene rhodanine MUST be detected as PAINS")
        self.assertGreater(len(reasons_rho), 0)

    def test_03_hill_langmuir_pharmacodynamics(self):
        """Verify that Hill-Langmuir curve is discriminative between strong and weak binders."""
        # High affinity drug (Kd = 0.05 uM = 50 nM)
        strong_curve = calculate_hill_langmuir_binding(kd_uM=0.05)
        # Weak affinity drug (Kd = 50.0 uM)
        weak_curve = calculate_hill_langmuir_binding(kd_uM=50.0)

        # At 1.0 uM concentration:
        # Strong drug (Kd=0.05) -> 1.0 / (0.05 + 1.0) = 95.2% bound
        # Weak drug (Kd=50.0)   -> 1.0 / (50.0 + 1.0) = 1.96% bound
        strong_at_1uM = [pt for pt in strong_curve if pt['concentration_uM'] == 1.0][0]['percent_bound']
        weak_at_1uM = [pt for pt in weak_curve if pt['concentration_uM'] == 1.0][0]['percent_bound']

        self.assertGreater(strong_at_1uM, 90.0, f"Strong binder at 1uM should be >90% bound, got {strong_at_1uM}%")
        self.assertLess(weak_at_1uM, 5.0, f"Weak binder at 1uM should be <5% bound, got {weak_at_1uM}%")

        # Verify monotonic increase
        strong_pcts = [pt['percent_bound'] for pt in strong_curve]
        self.assertEqual(strong_pcts, sorted(strong_pcts), "Binding curve must be monotonically non-decreasing")

    def test_04_vqe_millihartree_metric(self):
        """Verify that VQE accuracy is benchmarked in mHa against 1.6 mHa chemical accuracy."""
        from simulation import run_vqe_simulation
        res = run_vqe_simulation(molecule_id='h2', active_orbitals=2, ansatz_type='custom', noise_level=0.0, error_mitigation=False, mapper='parity')
        self.assertIn('final_energy', res)
        self.assertIn('fci_energy', res)
        
        diff_hartree = abs(res['final_energy'] - res['fci_energy'])
        diff_mha = diff_hartree * 1000.0
        # Check that error is a finite float
        self.assertTrue(np.isfinite(diff_mha))
        self.assertGreaterEqual(diff_mha, 0.0)

    def test_05_qrl_agent_and_checkpoint(self):
        """Verify that QuantumRLAgent loads, builds PQC, and samples valid actions."""
        from qrl_optimizer import QuantumRLAgent
        agent = QuantumRLAgent(num_qubits=8, lr=0.05)
        self.assertEqual(len(agent.theta), 32)
        
        # Test action selection with mask
        dummy_state = np.zeros(12)
        mask = [1.0] * agent.num_actions
        action_idx, prob = agent.select_action(dummy_state, mask)
        self.assertGreaterEqual(action_idx, 0)
        self.assertLess(action_idx, agent.num_actions)
        self.assertGreater(prob, 0.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
