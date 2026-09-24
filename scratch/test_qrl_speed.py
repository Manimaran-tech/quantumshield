import sys, os, time
sys.path.insert(0, os.path.abspath('.'))
from qrl_optimizer import run_qrl_optimization

start = time.time()
print("Starting optimization for c1cccc1CC[NH2+]CCNC1CCCCC1...")
res = run_qrl_optimization("c1cccc1CC[NH2+]CCNC1CCCCC1", "Tuberculosis", epochs=3)
elapsed = time.time() - start
print(f"Finished in {elapsed:.2f} seconds! Status: {res.get('status')}, Optimized: {res.get('optimized_smiles')}")
