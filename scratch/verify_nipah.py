import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qrl_optimizer import resolve_pathogen_metadata

print("--- Testing Pathogen Resolution for Nipah Virus ---")
result = resolve_pathogen_metadata("nipah virus")
print("Result:")
print(result)

if result and result.get("status") == "success" and result.get("fda_drug_name") == "None":
    print("\nSUCCESS: Nipah Virus resolved to None (no FDA-approved drug) as expected!")
else:
    print("\nFAILURE: Nipah Virus resolved incorrectly.")
