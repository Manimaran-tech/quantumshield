import sys, os
sys.path.insert(0, os.path.abspath('.'))
from qrl_optimizer import resolve_pathogen_metadata
import json

res = resolve_pathogen_metadata("Pneumonia")
print("RESULT:", json.dumps(res, indent=2))
