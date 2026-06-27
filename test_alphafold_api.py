import requests

def test_alphafold_fetch():
    print("Testing free AlphaFold Database API (EMBL-EBI)...")
    uniprot_id = "P9WGR1"  # Tuberculosis InhA protein
    url = f"https://www.alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                prediction = data[0]
                pdb_url = prediction.get("pdbUrl")
                print("Successfully retrieved AlphaFold prediction metadata!")
                print(f"  UniProt ID: {prediction.get('uniprotId')}")
                print(f"  Protein Name: {prediction.get('uniprotDescription')}")
                print(f"  Organism: {prediction.get('organismScientificName')}")
                print(f"  PDB URL: {pdb_url}")
                
                # Fetch first 10 lines of the actual PDB file to verify
                if pdb_url:
                    pdb_res = requests.get(pdb_url, timeout=10)
                    if pdb_res.status_code == 200:
                        print("\nFirst 10 lines of the downloaded AlphaFold PDB file:")
                        lines = pdb_res.text.splitlines()[:10]
                        for line in lines:
                            print(f"  {line}")
                        print("\nSUCCESS!")
                    else:
                        print(f"Failed to fetch PDB file. Status: {pdb_res.status_code}")
            else:
                print("No prediction found in AlphaFold Database for this UniProt ID.")
        else:
            print(f"Failed to connect to AlphaFold Database API. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == '__main__':
    test_alphafold_fetch()
