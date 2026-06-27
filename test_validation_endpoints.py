import requests
import json

def run_tests():
    base_url = "http://127.0.0.1:5000"
    print("====================================================")
    print("STARTING ENDPOINT VERIFICATION FOR QUANTUMSHIELD BACKEND")
    print("====================================================")
    
    # 1. Test preset pathogen generation (Tuberculosis)
    print("\n[TEST 1] /generate endpoint (Tuberculosis)...")
    payload = {"pathogen_name": "Tuberculosis"}
    try:
        response = requests.post(f"{base_url}/generate", json=payload, timeout=60)
        if response.status_code == 200:
            res_data = response.json()
            print("SUCCESS: /generate returned 200 OK.")
            print(f"Pathogen: {res_data['pathogen']}")
            print(f"Target Protein: {res_data['target_protein']}")
            print(f"Number of generated candidates: {len(res_data['candidates'])}")
            
            # Print advanced properties
            first_cand = res_data['candidates'][0]
            print(f"Advanced properties in generated candidate:")
            print(f"  Name: {first_cand['name']}")
            print(f"  Binding Free Energy (dG): {first_cand['free_energy']} kcal/mol")
            print(f"  Kd text: {first_cand['kd_text']}")
            print(f"  Multi-Objective Fitness Score: {first_cand['fitnessScore']}%")
            print(f"  Synthesizability steps: {first_cand['retrosynthesis']['steps']} (SA: {first_cand['retrosynthesis']['sa_score']})")
            print(f"  Pocket detected volume: {first_cand['pocket_detection']['volume']} A^3")
            print(f"  MD stability score: {first_cand['md']['stability_score']}%")
            print(f"  Variant mutation count: {len(first_cand['mutation_resistance']['variants'])}")
        else:
            print(f"FAILED: /generate returned {response.status_code}. Body: {response.text}")
    except Exception as e:
        print(f"ERROR: failed to connect to /generate: {e}")

    # 2. Test VQE Simulation with advanced thermodynamic corrections
    print("\n[TEST 2] /simulate endpoint...")
    simulate_payload = {
        "molecule_id": "evolved-0",
        "active_orbitals": 4,
        "ansatz_type": "custom",
        "noise_level": 5.0,
        "error_mitigation": True,
        "mapper": "parity",
        "pathogen_name": "Tuberculosis"
    }
    try:
        response = requests.post(f"{base_url}/simulate", json=simulate_payload, timeout=30)
        if response.status_code == 200:
            res_data = response.json()
            print("SUCCESS: /simulate returned 200 OK.")
            print(f"  VQE Active Space Ground Energy: {res_data['final_energy']:.5f} Ha")
            print(f"  Exact FCI Energy: {res_data['fci_energy']:.5f} Ha")
            print(f"  VQE Electronic Descriptor (E_vqe): {res_data['vqe_interaction_energy']} kcal/mol")
            print(f"  Implicit Solvation (dG_solv): {res_data['solvation_energy']} kcal/mol")
            print(f"  Entropy Penalty (-T*dS): {res_data['entropy_penalty']} kcal/mol")
            print(f"  Total Binding Free Energy (dG): {res_data['free_energy']} kcal/mol")
            print(f"  Dissociation Constant (Kd): {res_data['kd_text']}")
            print(f"  Pocket detected volume: {res_data['pocket_detection']['volume']} A^3")
        else:
            print(f"FAILED: /simulate returned {response.status_code}. Body: {response.text}")
    except Exception as e:
        print(f"ERROR: failed to connect to /simulate: {e}")

    # 3. Test Validation Experiment API route
    print("\n[TEST 3] /api/validation/run endpoint (COVID-19)...")
    payload = {"disease": "covid-19"}
    try:
        response = requests.post(f"{base_url}/api/validation/run", json=payload, timeout=60)
        if response.status_code == 200:
            res_data = response.json()
            print("SUCCESS: /api/validation/run returned 200 OK.")
            print(f"  Disease: {res_data['disease']}")
            print(f"  Target Protein: {res_data['target']}")
            print(f"  FDA Control Drug: {res_data['fda_drug_name']}")
            print(f"  FDA Drug Kd: {res_data['fda_drug_details']['kd_text']}")
            print(f"  Number of steps in pipeline logs: {len(res_data['steps'])}")
            print(f"  Number of generated candidates: {len(res_data['candidates'])}")
        else:
            print(f"FAILED: /api/validation/run returned {response.status_code}. Body: {response.text}")
    except Exception as e:
        print(f"ERROR: failed to connect to /api/validation/run: {e}")

    # 4. Test Validation Compare API route (RDKit Morgan Fingerprint + MCS Scaffold Match)
    print("\n[TEST 4] /api/validation/compare endpoint...")
    compare_payload = {
        "candidate_smiles": "CC1=CC=C(C=C1)C(=O)NN",
        "reference_smiles": "c1cc(ccn1)C(=O)NN"
    }
    try:
        response = requests.post(f"{base_url}/api/validation/compare", json=compare_payload, timeout=30)
        if response.status_code == 200:
            res_data = response.json()
            print("SUCCESS: /api/validation/compare returned 200 OK.")
            print(f"  Tanimoto Fingerprint Similarity: {res_data['tanimoto_similarity']}%")
            print(f"  Shared Scaffold Core: {res_data['shared_scaffold']}")
        else:
            print(f"FAILED: /api/validation/compare returned {response.status_code}. Body: {response.text}")
    except Exception as e:
        print(f"ERROR: failed to connect to /api/validation/compare: {e}")

    # 5. Test History route
    print("\n[TEST 5] /history endpoint...")
    try:
        response = requests.get(f"{base_url}/history", timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            print("SUCCESS: /history returned 200 OK.")
            print(f"  Number of runs in history: {len(res_data)}")
            if len(res_data) > 0:
                print(f"  Last Run: {res_data[-1]['molecule_id']} (dG: {res_data[-1]['free_energy']} kcal/mol, Kd: {res_data[-1]['kd_text']})")
        else:
            print(f"FAILED: /history returned {response.status_code}. Body: {response.text}")
    except Exception as e:
        print(f"ERROR: failed to connect to /history: {e}")

if __name__ == '__main__':
    run_tests()
