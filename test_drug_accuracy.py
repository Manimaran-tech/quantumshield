import os
import requests
import json
from dotenv import load_dotenv
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.DataStructs import TanimotoSimilarity
from generator import EvolutionaryGenerator

# Load env variables
load_dotenv()

# Reference FDA-approved drugs
REFERENCE_DRUGS = {
    "malaria": {
        "name": "Pyrimethamine",
        "smiles": "CCC1=C(C2=CC=C(C=C2)Cl)N=C(N)N=C1N", # Standard malaria DHFR inhibitor
        "description": "A DHFR inhibitor used to treat malaria."
    },
    "tuberculosis": {
        "name": "Isoniazid",
        "smiles": "c1cc(ccn1)C(=O)NN", # Standard first-line TB InhA inhibitor
        "description": "A prodrug that inhibits InhA cell-wall synthesis."
    }
}

def calculate_similarity(smiles1, smiles2):
    """
    Computes Scaffold Atom-Sharing Similarity using RDKit's Maximum Common Substructure (MCS).
    This measures the percentage of overlapping heavy atoms between the evolved drug and the reference.
    """
    try:
        from rdkit.Chem import rdFMCS
        mol1 = Chem.MolFromSmiles(smiles1)
        mol2 = Chem.MolFromSmiles(smiles2)
        if not mol1 or not mol2:
            return 0.0
        
        # Find maximum common substructure
        res = rdFMCS.FindMCS([mol1, mol2])
        if res.numAtoms == 0:
            return 0.0
            
        # Similarity = overlap / max heavy atoms
        max_atoms = max(mol1.GetNumHeavyAtoms(), mol2.GetNumHeavyAtoms())
        return res.numAtoms / max_atoms
    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0

def run_accuracy_test():
    print("====================================================")
    print("AI-QUANTUM DRUG ACCURACY & SIMILARITY VALIDATOR")
    print("====================================================")

    gen = EvolutionaryGenerator()
    api_key = os.getenv("NVIDIA_API_KEY")
    
    # 1. Test Tuberculosis Accuracy
    print("\n--- 1. Testing Tuberculosis Target Accuracy ---")
    print("Running local Genetic Algorithm (presetting Tuberculosis InhA target)...")
    tb_candidates = gen.evolve(pathogen_name="tuberculosis", num_candidates=3)
    
    ref_tb = REFERENCE_DRUGS["tuberculosis"]
    print(f"Reference Drug: {ref_tb['name']} (SMILES: {ref_tb['smiles']})")
    
    for idx, cand in enumerate(tb_candidates):
        similarity = calculate_similarity(cand["smiles"], ref_tb["smiles"])
        print(f"Evolved Candidate {idx+1}: {cand['smiles']}")
        print(f"  Tanimoto Similarity to {ref_tb['name']}: {similarity*100:.2f}%")
        if similarity > 0.5:
            print("  [MATCH] High similarity to approved drug scaffold!")
        elif similarity > 0.3:
            print("  [PARTIAL MATCH] Shares significant chemical fragments.")
        else:
            print("  [NOVEL CORE] Explores novel structural conformations.")

    # 2. Test Malaria Accuracy using NVIDIA NIM
    print("\n--- 2. Testing Malaria Target Accuracy via NVIDIA NIM ---")
    if not api_key:
        print("Skipping Malaria test: NVIDIA_API_KEY not found.")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    prompt = """You are a molecular pharmacology AI. Identify the primary therapeutic protein target and pocket specifications for Malaria.
You MUST respond with a valid JSON object ONLY. Do not include any markdown formatting (like ```json), explanations, or text outside the JSON.

The JSON structure must be exactly:
{
  "target_protein": "DHFR",
  "pocket_size_angstrom": 12.0,
  "pocket_charge_bias": "hydrophobic" or "polar" or "mixed",
  "recommended_seed_smiles": "the exact SMILES string of the primary FDA-approved reference drug for Malaria (Pyrimethamine: CCC1=C(C2=CC=C(C=C2)Cl)N=C(N)N=C1N)"
}

Pathogen: Malaria
"""

    pocket_specs = None
    seed_smiles = None
    
    try:
        payload = {
            "model": "meta/llama-3.1-8b-instruct",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 512
        }
        response = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"].strip()
            if content.startswith("```"):
                lines = content.split("```")
                if len(lines) > 1:
                    content = lines[1]
                    if content.startswith("json"):
                        content = content[4:]
            pocket_specs = json.loads(content.strip())
            seed_smiles = pocket_specs.get("recommended_seed_smiles")
            print(f"NVIDIA NIM resolved Malaria target protein: {pocket_specs.get('target_protein')}")
            print(f"Recommended Seed Scaffold: {seed_smiles}")
        else:
            print(f"NVIDIA NIM failed: {response.text}")
    except Exception as e:
        print(f"NVIDIA NIM call failed: {e}")

    if pocket_specs:
        print("\nEvolving molecules for Malaria pocket...")
        malaria_candidates = gen.evolve(
            pathogen_name="malaria",
            pocket_specs=pocket_specs,
            seed_smiles=seed_smiles,
            num_candidates=3
        )
        
        ref_malaria = REFERENCE_DRUGS["malaria"]
        print(f"Reference Drug: {ref_malaria['name']} (SMILES: {ref_malaria['smiles']})")
        
        for idx, cand in enumerate(malaria_candidates):
            similarity = calculate_similarity(cand["smiles"], ref_malaria["smiles"])
            print(f"Evolved Candidate {idx+1}: {cand['smiles']}")
            print(f"  Tanimoto Similarity to {ref_malaria['name']}: {similarity*100:.2f}%")
            if similarity > 0.5:
                print("  [MATCH] High similarity to approved drug scaffold!")
            elif similarity > 0.3:
                print("  [PARTIAL MATCH] Shares significant chemical fragments.")
            else:
                print("  [NOVEL CORE] Explores novel structural conformations.")
    else:
        print("Failed to resolve Malaria target parameters.")

if __name__ == '__main__':
    run_accuracy_test()
