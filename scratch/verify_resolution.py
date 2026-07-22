import sys
import os

# Add parent directory to sys.path so we can import qrl_optimizer
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qrl_optimizer import resolve_pathogen_metadata

print("--- Testing Pathogen Resolution with Gemini Fallback ---")
# Influenza is standard, let's test a custom/variant name so that it hits the API fallback
result = resolve_pathogen_metadata("Influenza A virus")
print("Result:")
print(result)

if result and result.get("status") == "success" and result.get("target_protein") == "Neuraminidase":
    print("\nSUCCESS: Pathogen successfully resolved using fallback model!")
else:
    print("\nFAILURE: Pathogen target resolution failed or returned unexpected data.")
