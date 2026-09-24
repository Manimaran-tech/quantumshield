# fix.md — Prioritized Issues & Recommended Fixes

**Project:** QuantumShield — "Quantum-Powered Antibiotic Discovery"
**Audit date:** 2026-07-19
**Scope:** In-silico / simulation-only computational research (defensive, educational).
**Method:** Static source review of `app.py`, `generator.py`, `simulation.py`, `qrl_optimizer.py`, `utils.py`, `real_benchmark.py`, tests, config. No runtime execution was performed; items that require running the code to confirm are explicitly marked **UNVERIFIED**.

Severity legend: **CRITICAL** (invalidates scientific claims or is a security hole) · **HIGH** · **MEDIUM** · **LOW**.

---

## A. Scientific integrity / hallucinated results (most important)

### A1. CRITICAL — The "VQE" runs on a hand-fabricated Hamiltonian, not a molecular electronic Hamiltonian
- **Files:** `simulation.py` `get_molecular_hamiltonian()` (L199–242), `calculate_coordinate_energy()` (L139–197)
- **What it does:** The `SparsePauliOp` is built by hand: the identity coefficient is a **classical Lennard-Jones + Coulomb toy energy** (`calculate_coordinate_energy`), plus fixed ad-hoc `Z`, `ZZ`, `XX` coefficients (`-0.2/n`, `-0.05/n`, `0.08/n`). There is no electronic-structure calculation — no one/two-electron integrals, no fermionic operator, no Jordan-Wigner/parity qubit mapping of real integrals (no PySCF / Qiskit Nature).
- **Why it matters:** The result is presented throughout the UI and returned as `fci_energy` / VQE ground state "in Hartrees." It is **not** quantum chemistry. `calculate_coordinate_energy` is labeled "Hartrees" but is a Lennard-Jones potential in arbitrary units. Any energy, HOMO/LUMO, or "binding" number derived as a quantum-chemistry quantity is unsupported.
- **Root cause:** Physics was mocked to produce plausible-looking numbers without a chemistry backend.
- **Fix:** Either (a) integrate **Qiskit Nature + PySCF** to build a genuine `ElectronicStructureProblem` → `FermionicOp` → mapped qubit Hamiltonian for small actives spaces (H₂, LiH are already in scope and feasible), and validate VQE vs FCI; or (b) if a real Hamiltonian is out of scope, **remove all "VQE / Hartree / electronic ground state" language** and relabel these as a classical force-field heuristic. Do not present a toy operator as VQE.
- **Impact:** Restores the central scientific claim of the project or makes the honest scope explicit.

### A2. CRITICAL — The reported drug "binding energy" does not come from the quantum computation at all
- **Files:** `simulation.py` `run_vqe_simulation()` (L1235–1317)
- **What it does:** After VQE runs, `binding_energy` is computed **separately** from the classical toy docking (`EvolutionaryGenerator.calculate_docking_energy`) and a fixed rescaling `-14.0 + 0.8*(raw-2.0)` clamped to `[-22,-6]`. The VQE `final_energy` is returned but **never feeds the binding energy**. `if error_mitigation: binding_energy -= 0.3` adjusts a physical result by a UI toggle.
- **Why it matters:** The "quantum" pipeline is decorative — turning quantum on/off cannot change the headline drug metric. This is the definition of quantum-theater.
- **Fix:** Make the reported quantity actually depend on the quantum result, or clearly separate and relabel "classical docking heuristic" vs "quantum electronic energy" and stop implying the former is quantum-derived. Remove the `error_mitigation → -0.3` hack.

### A3. CRITICAL — Fabricated NISQ noise and fabricated convergence history
- **Files:** `simulation.py` L1158–1233
- **What it does:** "NISQ noise" is synthesized as `bias + jitter*sin(step*1.8)*sin(step*0.612+0.5)`. If VQE throws, the convergence curve is fabricated as `fci_energy + 1.62*0.88**i`. Both are returned as `history`/`measured`/`error`.
- **Why it matters:** Presented as measured quantum device behavior; it is a sine-wave decoration. Given A6 (likely VQE API incompatibility) the fabricated fallback may be the **only** path that ever runs — **UNVERIFIED**, must be checked at runtime.
- **Fix:** Use Qiskit Aer with a real `NoiseModel` (or IBM runtime) for noisy estimation, or label the plot explicitly "illustrative schematic, not simulated device output."

### A4. HIGH — Hardcoded, fabricated scientific outputs presented as computed
- **Files:** `generator.py` (pocket_detection L631–660; mutation_resistance energies L668–700; MD trajectory L703–711), `simulation.py` (per-molecule HOMO/LUMO L1329–1352; H₂/LiH ADMET blocks L578–636; DNA/MD `np.random` fields), `app.py` (`run_validation` L478–592: `pose_rms=0.15`, `rmsd_trajectory=[…]`, `pocket_detection` `{0.85,500,12}`, fallback `ref_details` MW 350/docking −8.0).
- **Examples of fabrication:**
  - Mutation-resistance energies are the wild-type value plus **constant offsets** (`+0.25`, `+0.45`, …) attached to **real variant names** (Delta L452R, Omicron BA.5, JN.1, InhA S315T). The labels are real; the numbers are invented.
  - `pocket_detection` druggability/volume/residue counts and names ("Cys145-His41 Catalytic Dyad", "P2Rank Identified") are hardcoded — **P2Rank is never run**.
  - Water HOMO-LUMO `gap_ev = 23.15` (L1330) is non-physical (experimental optical gap ≈ 7 eV).
  - Pipeline `steps[]` text (`app.py` L651–694) claims "AutoDock Vina", "100 ns GROMACS/OpenMM", "pre-trained SMILES LSTM 1000 candidates" — none of Vina/GROMACS/OpenMM exist in the code, and generation uses batches, not 1000.
- **Why it matters:** These are the numbers a reader/reviewer would trust. They are not computed.
- **Fix:** Delete hardcoded scientific values or compute them for real; remove tool names (Vina/GROMACS/P2Rank) that are not actually invoked; relabel anything illustrative.

### A5. HIGH — Docstrings claim methods the code does not implement
- **Files:** `simulation.py` `solve_huckel_gap()` (L244–406), `get_dynamic_molecular_properties()` (L408), `analyze_dna_interaction()` (L1420)
- **What it does:** Docstrings say "diagonalizing a Tight-Binding / Hückel Hamiltonian." No matrix is built or diagonalized; the gap is `base_gap + 1.2*Δχ − 0.05*n_heavy − stretch` with **hardcoded overrides** (cyanide→4.20, isocyanate→5.20). `analyze_dna_interaction` claims "ICH M7 guidelines" and "QSAR" but implements ad-hoc element-count heuristics; `simulate_wet_lab_validation` attributes its ΔG formula to "Wang et al." with no citation and invented coefficients.
- **Fix:** Rewrite docstrings to describe what the code actually does, or implement the named method. Remove citations that do not correspond to an implemented method (see A9).

### A6. HIGH / UNVERIFIED — Qiskit primitive/algorithm version mismatch may mean VQE never actually runs
- **Files:** `simulation.py` L1146/1165, `qrl_optimizer.py` `run_actual_vqe` L61–85; `requirements.txt` (`qiskit==2.4.2`, `qiskit-algorithms==0.4.0`)
- **Concern:** `qiskit_algorithms.VQE` is built around the **V1** `BaseEstimator`, while `StatevectorEstimator` is the **V2** primitive (used elsewhere in `qrl_optimizer` via the `estimator.run([pub])` PUB API). Passing a V2 estimator into V1 `VQE` is very likely to raise, sending execution into the fabricated fallback (A3).
- **Fix:** Pin compatible versions and choose one primitive generation. Add a unit test asserting VQE returns within chemical accuracy of `NumPyMinimumEigensolver` on a **real** small Hamiltonian. **Must be confirmed by running.**

### A7. MEDIUM — "Docking" is a 6-DoF toy against a fake pocket
- **Files:** `generator.py` `calculate_docking_energy()` (L272–379), `PRESET_POCKETS` (L27–54), `parse_pdb_to_pocket()` (L90–168)
- **Concern:** Pockets are either 6 hand-placed atoms or, when AlphaFold succeeds, the **10 heavy atoms closest to the whole-protein centroid** — which is the buried core, **not** the binding site. LJ params `r_e=1.6, D_e=0.15` are single global constants; energies are clamped then linearly rescaled "to look like standard kcal/mol" (explicit comment L547).
- **Fix:** Use a real pocket detector (fpocket/P2Rank) or documented literature pocket residues; use a validated scoring function (AutoDock Vina/smina) if docking is a genuine goal; otherwise label as a coarse electrostatic/steric heuristic and stop calling the output kcal/mol.

### A8. MEDIUM — Unseeded RNG makes "results" non-reproducible
- **Files:** `simulation.py` MD (`np.random.normal` L1731/1793), DNA structural impact (`np.random.uniform` L1594–1604), trajectory noise (L703); `generator.py` trajectory noise (L707); `qrl_optimizer.py` agent init `self.theta = np.random.uniform(...)` (L133), `np.random.choice` action sampling (L265); `simulation.py` `np.random.seed(100+i)` **inside** a loop (L935) which also mutates global RNG state for everything after it.
- **Fix:** Thread a single configurable seed (`numpy.random.default_rng(seed)`) through all stochastic paths; never call `np.random.seed()` inside a loop. Record the seed in every result payload.

### A9. MEDIUM — Unsupported citation / benchmark labels
- **Files:** `simulation.py` L1882 ("Wang et al. inspired"), `real_benchmark.py` final table L174 (`"100.0% chemically valid"` hardcoded regardless of actual results)
- **Fix:** Add real references or remove the attribution; compute the validity number rather than printing a constant.

---

## B. Bugs / correctness

### B1. HIGH — `NameError` when a disease resolves via metadata but not to `'custom'`
- **File:** `app.py` `run_validation()` (L396–503)
- **Bug:** `disease_info` is only assigned inside `if disease == 'custom':` (L415–492). If the initial `disease` is not `'custom'` **and** `resolve_pathogen_metadata` returns `status != 'success'`, `disease` stays its original value, the block is skipped, and L496 `if disease_info and …` raises `NameError` → 500.
- **Fix:** Initialize `disease_info = None` before the branch and handle the non-custom path explicitly.

### B2. MEDIUM — Unreachable code after `return`
- **Files:** `generator.py` L911–912 (after `return None`); multiple leftover `pass` no-ops in `app.py` (L365, L391, L438, L456, L510).
- **Fix:** Delete dead code.

### B3. MEDIUM — Duplicated logic
- **Files:** `app.py` `normalize_name` defined twice (L224, L430); `fda = disease_info.get('fda_drug_details')` computed twice (L611, L616); the pathogen→key normalization block is copy-pasted in ≥5 places across `app.py`, `generator.py`, `simulation.py`, `qrl_optimizer.py`; `get_dynamic_molecular_properties` re-derives the entire toxicophore analysis already computed in `solve_huckel_gap`.
- **Fix:** Extract one `normalize_pathogen(name) -> key` helper and one toxicophore analyzer into a shared module; import everywhere.

### B4. MEDIUM — Inconsistent / likely-wrong UniProt ID for acetylcholinesterase
- **Files:** `app.py` L463–464 uses `P22340`; `qrl_optimizer.py` L1499 uses `P22303`. Human AChE is **P22303**; `P22340` does not correspond to it.
- **Fix:** Use one constant (`P22303`) from a single source of truth.

### B5. LOW — `mutantBinding = docking + 0.5`, `exactBaseEnergy = -75.0 - mw*0.5`
- **Files:** `generator.py` L718–719, `app.py` L542–543
- **Bug/why:** A constant +0.5 kcal/mol "mutant" shift and a molecular-weight-linear "exact base energy (Hartrees)" are physically meaningless placeholders presented as computed quantities.
- **Fix:** Remove or replace with a real per-variant recomputation (a `simulate_mutant_pocket` path already exists in `score_molecule` and could be reused consistently).

---

## C. Security

### C1. CRITICAL — Flask debug server bound to all interfaces
- **File:** `app.py` L942 `app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)`
- **Why:** `debug=True` enables the Werkzeug interactive debugger, which allows **arbitrary code execution** via the browser console PIN if reachable; `0.0.0.0` exposes it on the network.
- **Fix:** `debug=False` in any non-local context; gate via env var; never expose the debugger. Serve behind a WSGI server (gunicorn/waitress) for anything beyond a laptop demo.

### C2. HIGH — `torch.load(..., weights_only=False)` on a pickled model
- **File:** `utils.py` L20 (loads `pretrained.rnn.pth`)
- **Why:** `weights_only=False` unpickles arbitrary Python objects — code execution if the `.pth` is ever swapped/untrusted. The class is re-declared for pickle compatibility, so the file carries a full object graph.
- **Fix:** Re-export the model as a `state_dict` and load with `weights_only=True` into a freshly constructed `MiniSMILESLSTM`.

### C3. MEDIUM — CORS fully open
- **File:** `app.py` L13 `CORS(app)` (all origins, all routes)
- **Fix:** Restrict to known frontend origins for any deployment.

### C4. LOW — Secrets handling (no leak found)
- **Findings:** `.env` is **not** git-tracked (`.gitignore` L7 excludes `.env*`, keeps `.env.example`); `git log` shows no `.env` history. `.env` exists locally (~526 B) and presumably holds real `GEMINI_API_KEY`, `NVIDIA_API_KEY`, `MYUPCHAR_API_KEY`. The IBM Quantum `api_token` arrives via request body (`app.py` L159) and is passed to `QiskitRuntimeService` — acceptable but unvalidated and logged nowhere (good).
- **Recommendation:** Keep secrets in `.env`/secret manager only (already done); document required vars in README; add server-side validation/rate-limiting on the `api_token` field. Do not print tokens. **No credential is exposed in the repo — no rotation required from this audit.**

---

## D. Software engineering / dependencies

### D1. HIGH — README does not describe the actual project
- **Files:** `README.md` (AI-Studio Node/Gemini boilerplate), `metadata.json`
- **Concern:** README documents `npm install && npm run dev` for a React app and a `GEMINI_API_KEY`. The actual research system is a large **Python Flask** backend (`app.py` + 3 big modules). No instructions exist to install Python deps, obtain the model, or start the API. A second researcher cannot reproduce anything from the README.
- **Fix:** Rewrite README: architecture diagram, `pip install -r requirements.txt`, how to launch `app.py`, required env vars, the meaning/limits of each output, and an explicit "simulation-only, not for real-world use" statement.

### D2. HIGH / UNVERIFIED — Suspicious dependency pins
- **File:** `requirements.txt`
- **Concern:** Some pins may not exist on PyPI: `requests==2.34.2` (latest known is 2.32.x), `torch==2.12.1`. Others are plausible for 2026 but unconfirmed here (`qiskit==2.4.2`, `rdkit==2026.3.3`, `numpy==2.2.6`). `real_benchmark.py` imports `transformers` and downloads `deepchem/ChemBERTa-77M-MTR`, but `transformers` is **not** listed in requirements.
- **Fix:** Verify every pin resolves on the target index; add missing deps (`transformers`); generate a locked environment (`pip freeze` / `uv.lock`) that is known to install cleanly.

### D3. MEDIUM — In-memory global mutable state under a threaded server
- **File:** `app.py` `history_records = []` (L134), mutated in `/simulate` and `/history/clear` with `app.run(threaded=True)`.
- **Why:** Concurrent requests mutate a shared list without a lock (data race); state is lost on restart.
- **Fix:** Use a thread-safe store or a small database; guard with a lock if kept in memory.

### D4. MEDIUM — No real tests
- **Files:** `test_*.py` (root) and `scratch/*`
- **Concern:** `test_drug_accuracy.py`, `real_benchmark.py`, etc. are **print-only scripts with no assertions**. `test_drug_accuracy.py` "tests" LLM target identification while **embedding the correct answer (Pyrimethamine SMILES) in the prompt** (L97) — it cannot fail and validates nothing. No CI config exists.
- **Fix:** Convert to `pytest` with assertions on invariants that are actually true (e.g., generated SMILES parse in RDKit; VQE ≈ FCI on a real toy Hamiltonian; reward monotonic in a controlled input). Remove answer-leaking prompts. Add a CI workflow.

### D5. LOW — Heavy per-call recomputation / performance
- **Files:** `qrl_optimizer.py` `compute_parameter_shift_gradients` (L268) runs `2 × 32` PQC evaluations per step (parameter-shift over 32 params), each a fresh statevector build; `generator.calculate_docking_energy` re-runs L-BFGS-B with an O(atoms×residues) Python objective per candidate; `EvolutionaryGenerator()` is re-instantiated repeatedly (reloads nothing but allocates).
- **Fix:** Batch estimator PUBs, cache the reference fingerprint, vectorize the docking objective with NumPy, and reuse a single generator/agent instance.

---

## E. What is actually sound (do not "fix")

- **`qrl_optimizer.py` `QuantumRLAgent`** — a genuine parameterized quantum circuit policy: dense-angle encoding with data re-uploading, entangling CNOT rings, **correct parameter-shift-rule gradients**, softmax policy with action masking, REINFORCE with discounted normalized returns. This is the scientifically strongest component. Keep it; just fix the seed (A8) and feed it a defensible reward.
- **`resolve_pathogen_metadata` and helpers** (`query_open_targets`, `resolve_uniprot_id`, `verify_fda_approval`, `verify_ema_approval`, `fetch_pubchem_smiles`) — real, key-free, authoritative EMBL-EBI / OpenFDA / EMA / PubChem / NCBI integrations with reasonable fallbacks and RDKit validation of returned SMILES. Legitimate.
- **RDKit descriptor usage** (MW, LogP, HBD/HBA, TPSA, QED, Lipinski, PAINS SMARTS, Tanimoto, MCS) — standard and correct.
- **`calculate_qpu_codesign`** — uses correct transmon relations (`E_J = I_cΦ₀/2π`, `E_C = e²/2C`, `f_q = √(8E_JE_C) − E_C`) with real constants; the coupling/coherence fudge factors are illustrative but the physics skeleton is sound. Label the empirical factors as such.
- **AlphaFold structure retrieval + PDB parsing** — real API, sensible secondary-accession and parallel-candidate fallback. The weakness is pocket *selection* (A7), not the retrieval.

---

## Fix priority order
1. C1 (debug server) — one-line security fix.
2. A1/A2/A6 — decide: build real VQE (Qiskit Nature/PySCF) **or** relabel honestly. Everything downstream depends on this.
3. A3/A4/A5/A9 — remove or relabel fabricated numbers, tool names, and citations.
4. B1 — the `NameError` crash path.
5. D1/D2/D4 — README, dependencies, real tests (reproducibility gate).
6. A7/A8 — pocket realism + seeding.
7. Remaining B/C/D items.
