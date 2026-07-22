import os
import json
import requests

api_key = "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"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def query_model(model_name, prompt):
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 512
    }
    response = requests.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=25
    )
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        raise Exception(f"Status {response.status_code}: {response.text}")

def clean_json_string(s):
    s = s.strip()
    if s.startswith("```"):
        lines = s.split("```")
        if len(lines) > 1:
            s = lines[1]
            if s.startswith("json"):
                s = s[4:]
    return s.strip()

def run_test(pathogen):
    print(f"\n--- Testing resolution for pathogen: {pathogen} ---")
    model = "meta/llama-3.1-70b-instruct"
    
    previous_attempts = []
    
    for attempt in range(1, 4):
        print(f"Attempt {attempt}...")
        if attempt == 1:
            prompt = f"""You are a molecular pharmacology AI. Given a pathogen or disease name, identify its primary therapeutic protein target and provide the characteristics of its active binding pocket for drug discovery.
You MUST respond with a valid JSON object ONLY. Do not include any markdown formatting (like ```json), explanations, or text outside the JSON.

The JSON structure must be exactly:
{{
  "target_protein": "name of pathogen-specific protein target (do not return host/human proteins)",
  "uniprot_id": "the UniProt Accession ID of this pathogen protein target",
  "pocket_size_angstrom": 12.0,
  "pocket_charge_bias": "hydrophobic" or "polar" or "mixed",
  "fda_drug_name": "the specific common name of the FDA-approved small-molecule chemical drug (e.g. 'Acyclovir' for chicken pox). Do NOT return vaccines, antibodies, or biologicals; return a small-molecule chemical drug, or 'None' if none exists."
}}

Pathogen: {pathogen}
"""
        else:
            prompt = f"""You are a molecular pharmacology AI. Given a pathogen or disease name, identify its primary therapeutic protein target and provide the characteristics of its active binding pocket for drug discovery.
You MUST respond with a valid JSON object ONLY. Do not include any markdown formatting (like ```json), explanations, or text outside the JSON.

CRITICAL: For pathogen '{pathogen}', your previous suggestion(s) {previous_attempts} were verified as incorrect or NOT FDA-approved.
Please select a different, correct FDA-approved small-molecule chemical drug, or return "None" if there is no FDA-approved small-molecule drug for this pathogen.

The JSON structure must be exactly:
{{
  "target_protein": "name of pathogen-specific protein target (do not return host/human proteins)",
  "uniprot_id": "the UniProt Accession ID of this pathogen protein target",
  "pocket_size_angstrom": 12.0,
  "pocket_charge_bias": "hydrophobic" or "polar" or "mixed",
  "fda_drug_name": "the specific common name of the FDA-approved small-molecule chemical drug, or 'None' if none exists."
}}

Pathogen: {pathogen}
"""
        try:
            content = query_model(model, prompt)
            cleaned = clean_json_string(content)
            print(f"Model Response: {cleaned}")
            specs = json.loads(cleaned)
            drug = specs.get("fda_drug_name", "None")
            
            if drug.lower().strip() in ["none", "n/a", "fda reference", "unidentified", "no fda approved drug", "null", ""]:
                print("No drug returned, resolution completed.")
                return specs
                
            # Verification Step
            verification_prompt = f"""You are a strict medical validator.
Is the drug '{drug}' FDA-approved for treating the pathogen/disease '{pathogen}'?
Respond with a valid JSON object ONLY:
{{
  "is_approved": true or false,
  "reason": "explanation of why it is approved or not approved"
}}
Answer true only if '{drug}' is specifically FDA-approved for treating '{pathogen}'. Answer false if '{drug}' is not FDA-approved for '{pathogen}', is only experimental/off-label, or if there is no known FDA-approved drug for '{pathogen}'.
"""
            verify_content = query_model(model, verification_prompt)
            verify_cleaned = clean_json_string(verify_content)
            print(f"Verification response: {verify_cleaned}")
            verify_data = json.loads(verify_cleaned)
            
            if verify_data.get("is_approved") is True:
                print(f"Verification SUCCESS: {drug} is approved for {pathogen}")
                return specs
            else:
                print(f"Verification FAILED: {drug} is NOT approved for {pathogen}. Reason: {verify_data.get('reason')}. Retrying...")
                previous_attempts.append(drug)
        except Exception as e:
            print(f"Error in attempt {attempt}: {e}")
            break
            
    print("All attempts failed to verify. Setting drug to None.")
    return None

run_test("nipah virus")
run_test("tuberculosis")
