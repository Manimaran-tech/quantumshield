import subprocess
import time
import requests
import json
import os

def test_pipeline():
    print("====================================================")
    print("STARTING INTEGRATION TEST FOR DRUG DISCOVERY DASHBOARD")
    print("====================================================")

    # 1. Start Flask app
    print("Starting app.py server...")
    # Get python path
    python_exe = os.path.join(".", "venv", "Scripts", "python.exe")
    server_process = subprocess.Popen(
        [python_exe, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to bind to port 5000
    time.sleep(3)

    base_url = "http://127.0.0.1:5000"
    
    try:
        # 2. Test preset pathogen generation (Tuberculosis)
        print("\n--- 1. Testing Preset Pathogen Generation (Tuberculosis) ---")
        payload = {"pathogen_name": "Tuberculosis"}
        response = requests.post(f"{base_url}/generate", json=payload, timeout=120)
        
        if response.status_code == 200:
            res_data = response.json()
            print("Successfully connected to /generate endpoint.")
            print(f"Pathogen: {res_data['pathogen']}")
            print(f"Target Protein: {res_data['target_protein']}")
            print(f"Number of generated candidates: {len(res_data['candidates'])}")
            
            # Print first candidate details
            first_cand = res_data['candidates'][0]
            print(f"  Top Candidate Name: {first_cand['name']}")
            print(f"  Formula: {first_cand['formula']}")
            print(f"  SMILES: {first_cand['smiles']}")
            print(f"  Binding score: {first_cand['wtBinding']} kcal/mol")
        else:
            print(f"Preset generation failed. Code: {response.status_code}, Body: {response.text}")
            raise Exception("Preset generation failed.")

        # 3. Test custom pathogen generation using NVIDIA NIM (Influenza)
        print("\n--- 2. Testing Custom Pathogen Generation (Influenza) ---")
        payload = {"pathogen_name": "Influenza"}
        response = requests.post(f"{base_url}/generate", json=payload, timeout=120)
        
        if response.status_code == 200:
            res_data = response.json()
            print("Successfully resolved custom pathogen via NVIDIA NIM.")
            print(f"Pathogen: {res_data['pathogen']}")
            print(f"Target Protein: {res_data['target_protein']}")
            print(f"AlphaFold UniProt ID: {res_data.get('uniprot_id')}")
            print(f"Number of generated candidates: {len(res_data['candidates'])}")
            
            # Print first candidate details
            first_cand = res_data['candidates'][0]
            print(f"  Top Candidate Name: {first_cand['name']}")
            print(f"  Formula: {first_cand['formula']}")
            print(f"  SMILES: {first_cand['smiles']}")
            print(f"  Binding score: {first_cand['wtBinding']} kcal/mol")
            print(f"  MW: {first_cand['admet']['mw']} g/mol, LogP: {first_cand['admet']['logp']}")
            
            # We will use this custom candidate for VQE simulation testing
            target_candidate = first_cand
        else:
            print(f"Custom generation failed. Code: {response.status_code}, Body: {response.text}")
            raise Exception("Custom generation failed.")

        # 4. Test VQE Simulation with Custom Coordinates of Evolved Molecule
        print("\n--- 3. Testing VQE Simulation with Evolved custom coordinates ---")
        simulate_payload = {
            "molecule_id": target_candidate["id"],
            "active_orbitals": 4,
            "ansatz_type": "custom",
            "noise_level": 5.0,
            "error_mitigation": True,
            "mapper": "parity",
            "custom_coords": target_candidate["atoms"]
        }
        
        response = requests.post(f"{base_url}/simulate", json=simulate_payload, timeout=20)
        
        if response.status_code == 200:
            res_data = response.json()
            print("VQE Simulation successful!")
            print(f"  Qubits used: {res_data['qubits']}")
            print(f"  Final VQE Energy: {res_data['final_energy']:.6f} Hartree")
            print(f"  FCI Exact Energy: {res_data['fci_energy']:.6f} Hartree")
            print(f"  VQE-confirmed Binding Energy: {res_data['binding_energy']:.2f} kcal/mol")
            print(f"  Bioavailability: {res_data['admet']['bioavailability']}")
            print(f"  Toxicity Risk: {res_data['admet']['toxicity']}")
            print(f"  Docking score: {res_data['docking']['score']} kcal/mol")
        else:
            print(f"Simulation failed. Code: {response.status_code}, Body: {response.text}")
            raise Exception("Simulation failed.")

        # 5. Test DNA-Drug Docking Interaction Endpoint
        print("\n--- 4. Testing DNA Docking Interaction endpoint ---")
        dna_payload = {
            "molecule_id": target_candidate["id"],
            "custom_coords": target_candidate["atoms"]
        }
        response = requests.post(f"{base_url}/dna-interaction", json=dna_payload, timeout=20)
        
        if response.status_code == 200:
            res_data = response.json()
            print("DNA interaction endpoint successful!")
            print(f"  Compatibility Score: {res_data['compatibility_score']}")
            print(f"  Binding Mode: {res_data['binding_mode']}")
            print(f"  Ames Prediction: {res_data['ames_prediction']}")
            print(f"  Helix Unwinding: {res_data['helix_unwinding']} deg")
        else:
            print(f"DNA interaction failed. Code: {response.status_code}, Body: {response.text}")
            raise Exception("DNA interaction failed.")

        print("\n====================================================")
        print("ALL PIPELINE INTEGRATION TESTS SUCCEEDED!")
        print("====================================================")

    finally:
        # Terminate server
        print("\nShutting down server...")
        server_process.terminate()
        server_process.wait()
        print("Server shutdown completed.")

if __name__ == '__main__':
    test_pipeline()
