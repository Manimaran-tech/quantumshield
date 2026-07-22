# fix.md — Prioritized Issues & Recommended Fixes

**Project:** QuantumShield — "Quantum-Powered Antibiotic Discovery against Drug-Resistant Tuberculosis"
**Audit date:** 2026-07-22
**Supersedes:** `fix.2026-07-19.bak.md` (static-only review). This revision **executes** the code and **calls the live APIs**; items previously marked UNVERIFIED are now resolved either way.
**Scope:** In-silico / simulation-only computational research (defensive, educational). No recommendation here concerns synthesis, laboratory work, or clinical use.

**Environment used for verification:** the project's own `venv` — Python 3.10.11, `qiskit 2.4.2`, `qiskit-algorithms 0.4.0`, `qiskit-ibm-runtime 0.47.0`, `torch 2.12.1+cpu`, `rdkit 2026.3.3`, `numpy 2.2.6`, `Flask 3.1.3`.

**Evidence tags**
- **[EXECUTED]** — confirmed by running the code in this environment.
- **[LIVE-API]** — confirmed by issuing the actual HTTP request.
- **[STATIC]** — confirmed by reading the source; not executed.
- **[UNVERIFIED]** — could not be confirmed; stated as such.

**Severity legend:** **CRITICAL** (invalidates a central scientific claim, or is a security hole) · **HIGH** · **MEDIUM** · **LOW**.

---

## 0. Executive triage — the ten items that block publication

| # | Item | Severity | Evidence |
|---|---|---|---|
| A1 | The qubit Hamiltonian contains **zero molecular information** — every molecule yields identical non-identity Pauli coefficients | CRITICAL | [EXECUTED] |
| A2 | Reported binding energies do **not** depend on the quantum result | CRITICAL | [STATIC] |
| A3 | The QRL agent **never learns** — fresh random weights per request, one update, discarded | CRITICAL | [STATIC] |
| A4 | Actions are chosen by greedy reward lookahead, **not** by the policy → the REINFORCE gradient estimates nothing | CRITICAL | [STATIC] |
| A5 | "Lead polishing" hand-edits the output **only when it loses to the baseline** | CRITICAL | [STATIC] |
| A6 | `solve_huckel_gap` performs no Hückel calculation — no matrix, no diagonalization | CRITICAL | [STATIC] |
| A7 | Docking score is non-discriminative: ethanol scores better than isoniazid against InhA; Kd = 5.8 pM | CRITICAL | [EXECUTED] |
| A8 | Accuracy scripts print `PASSED` / `[PROVED]` / `[SUCCESS]` as unconditional string literals over a metric pinned at ~100 % | CRITICAL | [STATIC] |
| B1 | Live API keys on disk; one marked "compromised" in a comment | CRITICAL | [STATIC] |
| B2 | `debug=True` on `0.0.0.0` — remote code execution via the Werkzeug console | CRITICAL | [STATIC] |

---

# Part A — Scientific integrity and fabricated content

This is the largest category and the one that determines whether the project is publishable. Findings are classified as:
**fabricated** (asserted, never computed) · **unsupported** (computed, but by an invented method with no basis) · **questionable** (structurally real, uncalibrated) · **valid**.

---

### A1. CRITICAL — The qubit Hamiltonian carries no molecular information. Every molecule produces the same operator up to a constant.

- **Files:** `simulation.py:199-242` (`get_molecular_hamiltonian`), consumed by `simulation.py:1164`, `qrl_optimizer.py:509-521, 739-750, 1999-2003`
- **What it does:** the identity coefficient is set from a classical energy; every other Pauli coefficient is a function of `num_qubits` alone.

```python
simulation.py:207   target_energy = calculate_coordinate_energy(coords) - (active_orbitals * 0.05)
simulation.py:219   pauli_list.append(("I" * num_qubits, target_energy + 0.5))
simulation.py:225   pauli_list.append(("".join(pauli_label), -0.2  / num_qubits))   # Z
simulation.py:233   pauli_list.append(("".join(pauli_label), -0.05 / num_qubits))   # ZZ
simulation.py:239   pauli_list.append(("".join(pauli_label),  0.08 / num_qubits))   # XX
```

- **[EXECUTED] — direct measurement.** Building the operator for five different molecules at `active_orbitals=4`:

| molecule | identity coefficient | non-identity terms |
|---|---|---|
| `inh-q1` | −40.3276 | 16 |
| `water` | −3.3681 | 16 |
| `h2` | −0.8628 | 16 |
| `pyridine` | −18.2199 | 16 |
| `triclo-qv4` | −48.4211 | 16 |

  `ALL NON-IDENTITY COEFFS IDENTICAL ACROSS MOLECULES: True` — every molecule gets `ZIIIII: -0.033333`, `IZIIII: -0.033333`, …

- **Why it matters:** the identity term is a **global energy offset that commutes with everything**. It cannot change the eigenvector, the variational landscape, or the optimizer trajectory. Therefore the VQE solves **one fixed 6-qubit toy Ising-like problem for every molecule the product will ever process**. There are no one-/two-electron integrals, no basis set, no Hartree–Fock reference, no fermionic operator, and no Jordan–Wigner/parity transform — `mapper_type` only subtracts 2 from the qubit count (`simulation.py:212-214`). `qiskit_nature` is not a dependency. `num_qubits` is fixed at 6 regardless of molecule size, so there is no problem-size scaling and no basis for any quantum-advantage claim.
- **Root cause:** the electronic-structure layer was never implemented; a plausible-looking `SparsePauliOp` was assembled by hand.
- **Fix:** either (a) integrate **Qiskit Nature + PySCF**, build a genuine `ElectronicStructureProblem` → `FermionicOp` → mapped qubit Hamiltonian for a small active space, and report VQE error vs FCI and vs CCSD(T); or (b) delete every "VQE / Hartree / electronic ground state / FCI" label from code, UI, and docs and describe the module honestly as a classical force-field heuristic. Do not ship (c) — the current state.
- **Classification: fabricated.** **Impact:** restores or honestly retracts the project's central claim.

---

### A2. CRITICAL — The headline drug metric does not depend on the quantum computation.

- **Files:** `simulation.py:1306-1310`, `generator.py:549-550`
```python
simulation.py:1306   binding_energy = -14.0 + 0.8 * (raw_docking_score - 2.0)
simulation.py:1307   binding_energy = max(-22.0, min(-6.0, binding_energy))
simulation.py:1309   if error_mitigation:
simulation.py:1310       binding_energy -= 0.3
```
- **Why it matters:** `raw_docking_score` is a dimensionless sum of clipped LJ terms from `generator.py:346-349`. `-14.0`, `0.8`, `2.0` have no derivation. The clamp guarantees every candidate reports −6 to −22 kcal/mol, i.e. "nanomolar-to-picomolar binder", for any input. The VQE `final_energy` is returned but never enters this computation. Turning the quantum path on or off cannot move the headline number.
- **The `error_mitigation` term is physically impossible:** a quantum error-mitigation toggle cannot improve a classical Lennard-Jones docking score by 0.3 kcal/mol. It is a UI switch adjusting a "physical" result.
- **Fix:** delete lines 1309-1310 unconditionally. Then either make the reported quantity genuinely depend on the quantum result, or split the UI into two clearly separated panels — "classical docking heuristic" and "quantum electronic energy" — and stop implying the former is quantum-derived.
- **Classification: unsupported (formula) + fabricated (mitigation term).**

---

### A3. CRITICAL — The reinforcement-learning agent never learns.

- **Files:** `qrl_optimizer.py:133, 1920, 2048, 2116`; entrypoint `app.py:817-818`
```python
qrl_optimizer.py:133    self.theta = np.random.uniform(0, 2*np.pi, 32)
qrl_optimizer.py:1920   agent = QuantumRLAgent(num_qubits=8, lr=0.05)
qrl_optimizer.py:2048   agent.update_policy(states_batch, actions_batch, action_masks_batch, rewards_batch)
```
- **What it does:** the agent is constructed **inside** the per-HTTP-request function. Weights are freshly random every request, never loaded, never saved — there is no checkpoint path in the file. `update_policy` is called **exactly once**, *after* the rollout loop has ended. The updated `theta` is then used for exactly one thing: drawing the circuit picture at `:2116`. It never selects an action and is destroyed when the function returns.
- **Why it matters:** there is no training loop, no episodes, no convergence, and nothing persists between requests. The `epochs` parameter (`:1882, 1918, 1939`) is the step budget of a *single* rollout, not epochs. Every use of the words "training", "learning", "convergence", or "optimization curve" in the paper, UI, or docs is unsupportable.
- **Fix:** move the agent out of the request handler into a process-level (or persisted) object; add checkpoint save/load; run many episodes; log and plot the reward curve across episodes with seeds and error bars over ≥5 repeats.
- **Classification: unsupported — the method described is not the method implemented.**

---

### A4. CRITICAL — Actions are not sampled from the policy, so the REINFORCE gradient estimates nothing.

- **File:** `qrl_optimizer.py:1946-1968`
```python
1955   top_candidates = valid_indices[:3]
1958   cand_smiles = apply_chemical_action(current_smiles, act_name)
1961   r = calculate_chemical_reward(cand_smiles, pocket_residues, ref_smiles, pathogen_name)
1964   if r > best_candidate_reward:
1966       best_candidate_idx = idx
1968   action_idx = best_candidate_idx
```
- **Why it matters:** the action is chosen by **exhaustive greedy reward lookahead** — `a_t = argmax_a R(s,a)`. REINFORCE (`update_policy`, `:301-333`) requires `a_t ~ π_θ(·|s_t)`. Without importance weighting, the computed gradient is not an estimator of `∇J(θ)` for any objective. The quantum policy only ranks candidates for the top-3 shortlist; **when ≤3 actions are valid it has literally zero influence.** `select_action` (`:260-266`), the file's only on-policy sampler, is dead code — never called.
- **Fix:** sample the action from `probs`; or, if greedy lookahead is intentional, drop the RL framing entirely and describe the method as **greedy one-step search with a learned ranker**, then benchmark it against random search and a genetic algorithm.
- **Classification: unsupported — invalid estimator.**

---

### A5. CRITICAL — "Lead polishing" edits the result until it beats the baseline.

- **File:** `qrl_optimizer.py:2050-2084`
```python
2050   # Lead Polishing: ensure the QRL candidate beats the reference drug's free energy
2058   if cand_free_energy > ref_free_energy:
2060       polishing_actions = ["add_trifluoromethyl", "bioisostere_h_to_f", ...]
2081       if polished_free_energy < cand_free_energy:
2082           best_smiles = polished_smiles
```
- **Why it matters:** this runs **after** the RL loop, fires **only when the agent loses to the reference drug**, applies a hardcoded list of chemist-chosen edits, and the output is returned as `"optimized_smiles"` (`:2154`) and `"recommended_candidate"` (`:2165`). Hand-coded post-processing is attributed to the RL agent, and the exact failure mode it corrects is "we did not beat the baseline". If discovered after publication this would be treated as result fabrication.
- **Fix:** delete it. If a chemistry-rule refinement stage is genuinely wanted, make it unconditional, name it in the pipeline diagram, and report agent-only and agent+refinement results side by side.
- **Classification: fabricated (result engineering). Highest research-integrity risk in the repository.**

---

### A6. CRITICAL — `solve_huckel_gap` performs no Hückel calculation.

- **File:** `simulation.py:244-406`; docstring at `:246-249` claims "combines a Hückel tight-binding solver with a stable organic chemistry baseline"; `:409-412` repeats "by diagonalizing a Tight-Binding / Hückel Hamiltonian of the 3D coordinates".
- **What it actually does:** there is no matrix and no eigensolver. `np.linalg` appears in this file only as `np.linalg.norm` in unrelated MD code. The body is a constant `base_gap = 13.5` (`:347`), an affine formula (`:376`), a clamp (`:379`), then a lookup table (`:382-399`):
```python
if is_cyanide:           gap_ev = 4.20
elif is_sulfide:         gap_ev = 4.80
elif is_carbon_monoxide: gap_ev = 5.10
elif is_isocyanate:      gap_ev = 5.20
```
- The only genuine Hückel diagonalization in the repo is `solve_huckel_gap_custom` in `scratch_huckel_test.py:36-37` — a scratch file imported by nothing.
- **Fix:** delete the false docstrings; either wire up the real solver or remove the module.
- **Classification: fabricated.**

---

### A7. CRITICAL — The docking score cannot discriminate between molecules.

- **Files:** `generator.py:272-379` (`calculate_docking_energy`), rescale at `:549-550`
- **[EXECUTED] — measured against the project's own `PRESET_POCKETS['tuberculosis']`:**

| SMILES | heavy atoms | raw score | reported kcal/mol |
|---|---|---|---|
| `CCO` — ethanol, MW 46 | 9 | −2.757 | **−17.81** |
| `c1cc(ccn1)C(=O)NN` — isoniazid | 17 | −2.201 | **−17.36** |
| aspirin | 21 | −2.416 | −17.53 |
| nirmatrelvir, MW 499 | 67 | −3.374 | −18.30 |

- **Why it matters:** **ethanol scores better than isoniazid against the InhA pocket.** The entire dynamic range across a 10× mass span is 0.9 kcal/mol. Propagating ethanol through `generator.py:601-611` gives ΔG = −15.33 kcal/mol and **Kd = 5.8 pM** — the pipeline reports ethanol as a picomolar InhA binder. The clamp floor of −22.0 kcal/mol sits below the strongest affinity known in biology (biotin–streptavidin, ≈ −18 kcal/mol).
- **Root cause — a unit error (`generator.py:343-352`):**
```python
v_lj  = D_e * ((r_e / dist)**12 - 2 * (r_e / dist)**6)   # D_e = 0.15, implicitly kcal/mol
v_coul = (achg * rchg) / (dist * 1.88973)                 # Å→Bohr ⇒ this term is in Hartree
energy += v_lj + v_coul                                   # Hartree added to kcal/mol
```
  Hartree and kcal/mol are summed directly — a factor of 627 apart — so the electrostatic term is numerically ≈0 and the score is pure sterics, i.e. essentially an atom count. Missing: the 332 kcal·Å·mol⁻¹·e⁻² constant, any dielectric model, any desolvation term. `r_e = 1.6`, `D_e = 0.15` (`:317-318`) are single global constants for **all** element pairs. `if achg and rchg` (`:349`) also short-circuits on `0.0`, silently zeroing electrostatics for any neutral atom — a truthiness bug, not a modelling choice.
- **Fix:** replace with a real scoring function (**smina** / **AutoDock Vina** / **gnina** via subprocess), or fix units and **benchmark against a labelled set** (PDBbind core, DUD-E) reporting RMSE / enrichment / AUC. A score that cannot separate ethanol from nirmatrelvir supports no conclusion.
- **Classification: unsupported (unit-inconsistent, non-discriminative).**

---

### A8. CRITICAL — The accuracy benchmark is guaranteed to pass.

- **Files:** `test_accuracy_validation.py:48, 82, 104, 144, 148`
```python
144   print(f"  Quantum Chemistry Solver Accuracy (vs FCI): {quantum_accuracy:.4f}% (PASSED >95% goal)")
148   print("[SUCCESS] Platform successfully validated as genuine, accurate, and scalable.")
 82   print(f"\n[PROVED] Best candidate ... shares {best_overlap * 100:.1f}% structural scaffold overlap...")
```
- **Why it matters, three compounding defects:**
  1. `PASSED`, `[SUCCESS]`, and `[PROVED]` are **string literals inside f-strings**. No assertion, no threshold comparison. They print whatever the number is, including 0.0.
  2. The metric is structurally pinned: `simulation.py:1170` sets `final_energy = fci_energy` on the VQE exception path, so `relative_error` at `:104` is exactly 0 → accuracy exactly 100.0000 %.
  3. Even on the success path, `fci_energy` (`simulation.py:1119`) is `NumPyMinimumEigensolver` applied to **the same `qubit_op` the VQE minimizes**. That is self-consistency, not an independent FCI reference — and per **A1** the operator is not a molecular Hamiltonian at all.
- The banner at `:48` advertises "Achieves > 95 % numerical chemistry accuracy (VQE simulation vs exact FCI)".
- **Fix:** retract the claim. Replace with `pytest` assertions against **published reference energies** for a molecule with a real Hamiltonian (H₂/LiH via Qiskit Nature + PySCF), and report the error in millihartree against chemical accuracy (1.6 mHa).
- **Classification: fabricated benchmark.**

---

### A9. CRITICAL — VQE runs, but ~50× outside chemical accuracy and non-deterministically.

- **[EXECUTED] — this resolves an item the 2026-07-19 audit could not.** `qiskit-algorithms 0.4.0` **does** accept the V2 `StatevectorEstimator`; no silent fallback to `NumPyMinimumEigensolver` occurs. Two identical calls to `run_actual_vqe` on the `inh-q1` operator:

```
exact  = -40.574850
vqe #1 = -40.506562   error 0.0683 Ha  =  42.9 kcal/mol
vqe #2 = -40.428505   error 0.1463 Ha  =  91.8 kcal/mol
```

- Chemical accuracy is 1.6 mHa. These errors are **43× and 91×** larger, and the run-to-run spread alone is 0.078 Ha ≈ 49 kcal/mol.
- **Root cause:** `simulation.py:1126` builds `TwoLocal(num_qubits, ['ry','rz'], ['cx'], 'linear', reps=3)` — **64 parameters** at 8 qubits — and `:1161` sets `COBYLA(maxiter=40)`. COBYLA needs ≥ n+1 = 65 evaluations merely to build its initial simplex. With 40 it returns essentially the random initial point. `qrl_optimizer.py:68-70` is worse: 12 parameters, `maxiter=15`. No `initial_point`, no `tol`, no seed; `result` is never inspected for convergence.
- Yet `simulation.py:822` emits the string *"VQE active space electronic ground state converged."*
- **Fix:** set `maxiter ≥ 20·n_params`, pass a fixed `initial_point` and seed, check `result.optimizer_result`, and report the FCI gap. Delete the unconditional "converged" string.

---

### A10. CRITICAL — Fabricated binding pockets presented as structural biology.

Three separate fabrication sites:

**(a) Hardcoded "binding sites" annotated with real residue names — `generator.py:27-54`**
```python
'sars-cov-2': [
    {"element": "S", "x": 0.0, "y": 0.0, "z": 1.0, "charge": -0.4},  # Cys145
    {"element": "N", "x": 1.5, "y": 1.0, "z": 0.0, "charge":  0.3},  # His41
```
Five to six hand-typed atoms on a lattice of round numbers. Comments assert these are the InhA hydrophobic cleft, the Mpro catalytic dyad, and the GyrB ATP pocket. They are derived from no structure. **All docking numbers for preset targets rest on these six invented atoms.**

**(b) Hash-of-string pockets, in three places — `generator.py:420-438`, `qrl_optimizer.py:869-886`, `simulation.py:1285-1302`**
```python
seed = sum(ord(c) for c in pathogen_name)
rng  = random.Random(seed)
pocket.append({"res_name": rng.choice(res_names), "res_num": rng.randint(20, 300),
               "x": rng.uniform(-4.0, 4.0), ..., "charge": rng.choice([-0.4, 0.0, 0.4, ...])})
```
Ten uniformly random points in an 8 Å box with random residue names and numbers. Downstream consumers cannot distinguish these from PDB-parsed residues — `generator.py:870-874` reads `res_name`/`res_num` to build labels like `"CYS145 to … mutant"`. The log line says "Dynamically simulating", which reads as a feature rather than a failure.

**(c) The real AlphaFold path is permanently dead — `simulation.py:1281`**
`gen` is used at `:1281` but not assigned until `:1304`. Because `gen` is function-local, `:1281` raises `UnboundLocalError` **on every call**, swallowed by `except Exception` at `:1282`. Execution therefore *always* falls through to (b). The result is labelled in the UI as `'Primary Druggable Hydrophobic Cleft (P2Rank Identified)'` (`simulation.py:770`, `generator.py:659`). **P2Rank is never invoked anywhere in the repository.**

**(d) Druggability metrics from character arithmetic — `generator.py:653-658`**
```python
seed   = sum(ord(c) for c in smiles)
p_vol  = float(round(350.0 + (seed % 300), 1))
p_drag = float(round(0.72 + (seed % 20) / 100.0, 2))
p_res  = int(8 + (seed % 10))
```
Emitted under the header `--- POCKET DETECTION ENGINE DATA ---`. `generator.py:631-648` and `simulation.py:739-759` add per-target hardcoded tables of the same quantities.

- **Fix:** fix the `UnboundLocalError`; on structural-resolution failure **return an error**, never fabricate a pocket. Remove the "P2Rank"/"Vina" strings unless those tools are actually executed. If synthetic pockets are kept for demo purposes, add `"is_synthetic": true` to the payload and render a visible warning banner.
- **Classification: fabricated.**

---

### A11. CRITICAL — Silent substitution of the wrong target.

- **File:** `generator.py:813-814`
```python
if not pocket_residues:
    pocket_residues = PRESET_POCKETS['tuberculosis']
```
- **Why it matters:** if AlphaFold resolution fails for, say, a *Salmonella* query, every affinity, Kd, and ΔG returned is computed against the invented InhA pocket while being **labelled with the user's pathogen**. No warning is logged, and nothing in the response indicates it. This is the most easily-missed fabrication in the codebase because the output looks completely normal.
- **Fix:** raise; or return `{"status": "unresolved_target"}`.

---

### A12. CRITICAL — Garbage pathogen input returns `status: "success"`.

- **[EXECUTED]** `resolve_pathogen_metadata("Zorblax fictional pathogen")` →
```json
{"status": "success", "pathogen": "Zorblax fictional pathogen",
 "target_protein": "Target Protein", "uniprot_id": "P12345",
 "fda_drug_name": "None", "data_sources": []}
```
- `P12345` is the canonical placeholder accession (`qrl_optimizer.py:1858`, `app.py:371`). `data_sources` is empty — the code *knows* nothing resolved — yet still reports success. The full pipeline will then design "drug candidates" for a non-existent organism and report binding affinities for them.
- **Also verified:** for `Tuberculosis` the resolver returns UniProt **F2GEM2** (an unreviewed TrEMBL entry), **not** InhA (P9WGR1) as every document in the repo claims. `Nipah virus` → Q9IH62 (Glycoprotein G), which is plausible.
- **Fix:** return `status: "unresolved"` when `data_sources` is empty; assert a non-placeholder accession; add a curated, cited target table for the pathogens actually claimed in the paper, and make the resolver a fallback rather than the primary path.

---

### A13. HIGH — The convergence plot shown to the user is synthetic.

- **File:** `simulation.py:1200-1220`. The real callback energies (`history`, `:1151-1156`) are **overwritten**:
```python
1212   jitter = jitter_amp * np.sin(step * 1.8) * np.sin(step * 0.612 + 0.5)
1213   measured_energy = ideal_energy + bias + jitter
```
Bias magnitudes (`n_coeff * 1.55 / 0.18 / 0.42 / 0.032`, `:1192-1198`) are tuned so `error_mitigation=True` always looks ≈8.6× better. This is a hand-drawn curve presented as NISQ hardware behaviour.
- **Fix:** plot the actual callback trace, or run a real `qiskit_aer` noise model.
- **Classification: fabricated.**

---

### A14. HIGH — Failure paths synthesize a *perfect* result and return it unflagged.

- **File:** `simulation.py:1168-1178` (duplicated at `:1223-1233`)
```python
except Exception as e:
    print(f"VQE execution fallback triggered: {e}")
    final_energy = fci_energy
    history = []
    for i in range(41):
        ideal_val = fci_energy + 1.62 * (0.88 ** i)
```
- On **any** VQE failure the UI receives a textbook-perfect exponential convergence curve and `final_energy == fci_energy` — exact agreement, the best possible result — with **no flag in the returned dict**. A user cannot distinguish a successful run from a total failure. Combined with **A8**, this is why the accuracy benchmark reports 100 %.
- **Fix:** add `"status": "vqe_failed"` to the payload and surface it; never synthesize a curve.

---

### A15. HIGH — Hardcoded electronic-structure table; two entries are ionization potentials.

- **File:** `simulation.py:1329-1355`
```python
if   mol_id_lower == 'water':            gap_ev = 23.15; homo_ev = -12.60
elif mol_id_lower == 'carbon-monoxide':  gap_ev = 14.01; homo_ev = -14.01
elif mol_id_lower == 'nitric-oxide':     gap_ev =  9.26; homo_ev =  -9.26
elif mol_id_lower in ['inh-q1','triclo-qv4','ethio-qx9']:
                                         gap_ev = 17.54; homo_ev = -13.41
```
- CO (14.01 eV) and NO (9.26 eV) are the **experimental ionization potentials** of those molecules, copy-pasted into the gap field — `gap_ev == -homo_ev` exactly. A gap is not an IP.
- The three lead antibiotic candidates — chemically distinct molecules — are assigned **identical** electronic structure.
- 17.54 eV and 23.15 eV are physically absurd HOMO–LUMO gaps for water and drug-like organics (real range ≈3–8 eV). The related claim in `completeworkflow.md` that gaps `< 8 eV` indicate toxicity would flag essentially every drug molecule ever made.
- `dyn_props` is computed at `:1326` and then **discarded** for every listed molecule.
- **Classification: fabricated.**

---

### A16. HIGH — Fabricated resistance mutations for clinically named variants.

**(a) `generator.py:669-700`**
```python
{'name': 'Omicron (BA.5)',     'energy': float(round(free_energy + 0.45, 2))},
{'name': 'JN.1 (L455S/R357K)', 'energy': float(round(free_energy + 0.65, 2))},
{'name': 'KP.3 (F456L/Q493R)', 'energy': float(round(free_energy + 0.72, 2))}
```
Constant offsets on the wild-type number. No mutant structure is built. Worse, the modelled SARS-CoV-2 target is **Mpro** (Cys145/His41, `generator.py:37-44`) while every listed variant is a **spike RBD** mutation — spike mutations have no bearing on Mpro inhibitor binding. The panel is chemically meaningless for the modelled target.

**(b) `generator.py:680`** — `'InhA S315T mutant'`. S315T is the canonical ***katG*** mutation (isoniazid activation), not an *InhA* mutation. The adjacent `InhA I21V` entry is correct, which makes this a fabricated pairing rather than shorthand.

**(c) `qrl_optimizer.py:604-660, 2135-2147`** — `simulate_adversarial_mutant_pocket` claims to "physically simulate an adversarial point mutation" but shifts one atom 1.2 Å, negates its charge, and renames it via a fixed chain (`:658`). Residue identity and numbering are invented when absent: `res_map = {"S":"CYS","O":"ASP","N":"HIS","C":"ALA"}` and `res["res_num"] = closest_idx + 108` (`:637-639`). Output strings like `"HIS110 to VAL mutant"` look like real resistance annotations but are derived from an array index plus 108.

- **Fix:** delete all three. If resistance modelling is a goal, use a real mutation set (e.g. the WHO catalogue of *M. tuberculosis* resistance-associated variants), build actual mutant structures, and cite the source.
- **Classification: fabricated biology in the user-facing payload.**

---

### A17. HIGH — "Molecular dynamics" that never integrates equations of motion.

- **Files:** `generator.py:702-710`, `simulation.py:700-709`
```python
# --- MOLECULAR DYNAMICS SIMULATION ---
noise = np.random.uniform(-0.01, 0.02)
val   = limit * (1.0 - 0.7 ** i) + noise
```
- No integrator, no force field, no time step. `rmsf_average = 0.12 + (100 - stability) * 0.005` and `h_bonds = int(3 + (hba // 2))` are invented formulas. Emitted as `"md": {"rmsd_trajectory": ...}` with no synthetic label.
- A **genuine Langevin integrator does exist** at `simulation.py:1694-1856` — and is **never called** from `run_vqe_simulation`. The user-facing MD data is the closed-form curve above.
- The UI narrates *"Ran 100ns GROMACS/OpenMM trajectory on top 20 leads"* (`app.py:679`). Neither package is a dependency. `qrl_optimizer.py:462-463` carries the comment `# Production uses 100ns molecular dynamics simulations.` — there is no such path anywhere.
- **Fix:** call the real integrator, or delete the MD block and the narration.

---

### A18. HIGH — "Wet-lab validation" returns `np.random.normal` draws under the key `measured_binding`.

- **File:** `simulation.py:1899-1910`, endpoint `app.py:917`
```python
concs_uM = [float(round(c * kd_uM, 3)) for c in [0.1, 0.3, 1.0, 3.0, 10.0]]
for c in concs_uM:
    ideal_binding = c / (c + kd_uM)
    measured = ideal_binding + np.random.normal(0, std_dev)
```
- Because the concentrations are **defined as multiples of Kd**, `ideal_binding` is **9.1 / 23.1 / 50.0 / 75.0 / 90.9 %** for *every molecule ever submitted*. The "5-point dose–response curve" carries zero molecule-specific information; only the x-axis moves. **[EXECUTED]** — a run returned `measured_binding: [6.2, 23.4, 47.5, 80.1, 90.7]`, and a second identical call returned different values.
- The word "measured" is applied to a Gaussian draw. "Simulate" appears in the internal function name but **not** in the API route, the response keys, or the UI.
- `starting_materials` is a canned generic list returned as retrosynthesis output.
- **Fix:** rename the route to `/api/simulation/dose_response_synthetic`, rename the key to `synthetic_binding`, and render a persistent "SYNTHETIC — NOT EXPERIMENTAL DATA" banner. Given the biomedical framing, this is the single highest-risk mislabel for a lay reader.

---

### A19. HIGH — Invented energy scales presented as quantum chemistry.

| Location | Code | Problem |
|---|---|---|
| `generator.py:570` | `base_energy = -75.0 - (mw * 0.5)` with comment `# Physical base energy baseline for VQE (Hartrees)` | A linear function of MW is not an electronic energy. A 400 Da molecule → −275 Ha. Emitted as `"exactBaseEnergy"` (`:719`) |
| `simulation.py:172` | `energy += -0.5 if el1 == 'H' else -2.5` | One "core valence energy" for C, N, O, F, Cl **and S** alike. True atomic energies: C −37.8, N −54.6, O −75.1, S −398 Ha |
| `simulation.py:147-154` | `D_e` 0.09–0.22 "Ha" | = 56–138 kcal/mol as LJ well depths; real vdW wells are 0.05–0.5 kcal/mol — off by ~300×. `r_e` values are covalent bond lengths used where vdW radii belong |
| `simulation.py:159, 209`; `qrl_optimizer.py:84-85` | `return -75.0` | Magic fallback, duplicated in three files |
| `app.py:543` | `-75.0 - (scored_cand["mw"] * 0.5)` | Fourth copy |

**[EXECUTED]:** water → −3.67 Ha (true −76.4); pyridine → −18.52 Ha (true ≈ −248); methyl isocyanate (4 atoms) → **−0.348 Ha**. Values are 1–2 orders of magnitude off and labelled "Hartrees". Note the `-75.0` fallback is *more* physical than the "computation" it replaces.

---

### A20. HIGH — Sign error inverts the fitness function.

- **File:** `generator.py:622`
```python
docking_fit = max(0, min(100, 100 - (scaled_docking - (-12.0)) * -10.0))  # -12.0 is 100, -6.0 is 40
```
- **Computed:** −6 → **100**, −12 → 100, −18 → 40, −22 → **0**. The comment claims −6 → 40. The double negative means **weaker binding scores higher and the tightest binders score zero.** Since `fitness_score = 0.4*docking_fit + …` (`:627`), the headline "Multi-objective optimization fitness score" (`:758`) ranks candidates **backwards** on its largest-weighted term.
- The same file scores the same quantity in the opposite direction at `:703` (`stability` rewards `abs(scaled_docking)`).
- **Fix:** `docking_fit = max(0, min(100, (abs(scaled_docking) - 6.0) / 16.0 * 100))`, then add a unit test pinning the endpoints.

---

### A21. HIGH — The reward function is nine magic numbers with no ground truth.

- **File:** `qrl_optimizer.py:666-828`; weights at `:776-784`
- **Five of nine default weights are unreachable** — `w_docking`, `w_vqe`, `w_lipinski` are unconditionally overwritten at `:800-807`; `w_entropy`, `w_mw` at `:789-795`.
- **Magic thresholds flip weights by 2–3×:** `if spatial_spread < 2.2` (`:788`), `if polar_ratio > 0.35` (`:798`). **The objective is not the same function between two pathogens**, so cross-target comparisons are meaningless.
- **Substring pathogen override (`:810-815`):** `if 'isocyan' in norm or 'cyan' in norm …` — `'cyan'` matches *cyanobacteria*, *cyanosis*, *cyanocobalamin*. The objective silently rewrites itself on a substring match. The identical fragile normalizer appears at `app.py:226` and `app.py:432`.
- **Terms are strongly collinear:** `mw` enters via `sa_score` *and* `norm_mw_penalty`; `rotb` via `sa_score` *and* `norm_entropy`. The "multi-objective" framing is misleading.
- **`w_toxicity` is near-dead:** per **A22**, `is_toxic` is always False for drug-like molecules, so only `pains_alerts * 30.0` survives.
- **Penalty magnitudes sit inside the normal reward range** (`-25.0` at `:376/673`, `-20.0` at `:718`, `-10.0` at `:380`; typical valid rewards ≈ [−50, +78]) — so "invalid molecule" can outscore a merely mediocre valid one.
- **Fix:** rebuild from defensible, cited components only (QED, Ertl SA_Score, Lipinski/Veber, PAINS via `FilterCatalog`, Tanimoto novelty, and a real docking score). Publish a weight table with an ablation.

---

### A22. HIGH — Toxicity prediction is unreachable for every drug-like molecule.

- **File:** `simulation.py:454-456` (duplicated at `:300-302`), consumed by `generator.py:555-557, 837-839` and the QRL reward
```python
is_cyanide         = 'C' in el_set and 'N' in el_set and n_heavy <= 3
is_sulfide         = 'S' in el_set and n_heavy <= 2
is_carbon_monoxide = 'C' in el_set and 'O' in el_set and n_heavy <= 2 and 'N' not in el_set
```
- Every branch is gated on ≤3 heavy atoms. Every LSTM-generated candidate has 15–40. **Every branch is unreachable**, `toxicity` is always `"Low Risk"`, and `tox_penalty = 0` (`generator.py:624`) makes that fitness term a permanent no-op — while the docstring calls it a "dynamic toxicophore engine" performing "Real-Time Functional Group Analysis".
- Where the rules *do* fire they are wrong: methylamine → "Extreme Risk (Cyanide Poisoning)"; formaldehyde → "Extreme Risk (Carbon Monoxide)"; `is_hydrocarbon_solvent` (`:492`) flags any pure hydrocarbon ≥5 heavy atoms as "Carcinogenic", which is false for cyclohexane, decalin, and most terpenes; `is_flat_aromatic_toxicophore` (`:495`) flags **any** planar 5–12-atom ring system — including pyridine, the isoniazid pharmacophore this project is built on (**[EXECUTED]**: pyridine → gap forced to 7.30).
- `fsp3` is recomputed from interatomic distances with a 1.6 Å cutoff counting hydrogens (`:437-452`) instead of `Lipinski.FractionCSP3`. RDKit's `FilterCatalog` (PAINS/Brenk/NIH) is available and unused. No Tox21, no AMES, no hERG model.
- **Fix:** replace with `FilterCatalog` structural alerts plus a published QSAR model, or delete the toxicity claim.

---

### A23. HIGH — No ADMET model exists; every field is a hand-fitted guess.

| Location | Formula | Problem |
|---|---|---|
| `generator.py:601` | `solvation = -1.8 - 0.22*hba + 0.12*logp` | Labelled "Implicit solvation ΔG". No PB/GB/SASA. Sign on logP is backwards |
| `generator.py:605` | `entropy_penalty = 4.5 + 0.35*n_rot` | Commented `T*dS`. A +4.5 kcal/mol floor on every molecule, rigid ones included |
| `generator.py:742` | two-branch string on `violations == 0 and tpsa < 140` | Presented as a bioavailability *prediction* |
| `simulation.py:1932` | `papp = 15.0 + 3.5*logp - 0.01*mw - 0.08*tpsa` | "Virtual Human ADMET Twin" Caco-2 permeability |
| `simulation.py:1936` | `half_life = 45.0 - 5.0*logp + 0.05*mw` | Human half-life from two descriptors |
| `simulation.py:670` | `logp = (n_nonpolar - n_polar)*0.4 + 0.5` | Water → +0.9 (true −1.38). The same file uses correct Crippen `MolLogP` at `:1873` |

**Uncheckable citation:** `simulation.py:1882` — `# Improved empirical ΔG estimator (Wang et al. inspired scoring function)`. "Wang et al." with no year, title, or venue, attached to seven hand-picked coefficients (`:1887-1894`), then clamped to `[-13, -4]`. The coefficients do not match X-Score or Vina's published forms. **Treat as an invented citation until a reference is produced.**

---

### A24. HIGH — Three mutually contradictory synthetic-accessibility scores, none of them SA_Score.

```python
generator.py:663      sa_score = round(1.8 + (violations * 1.6) + (mw * 0.005), 2)
generator.py:721      "saScore": f"{int(98 - (violations * 15) - (mw * 0.05))}% (Accessible)"
simulation.py:1916    sa_score = 1.5 + 0.005*mw + 0.3*rotb + 0.5*n_chiral + 0.4*n_rings
qrl_optimizer.py:683  sa_score = 1.5 + 0.005*mw + 0.3*rotb + 0.5*n_chiral + 0.4*n_rings
app.py:545            f"{int(98 - (scored_cand['sa_score'] * 5))}% (Accessible)"
```
- The first two are emitted **in the same result dict** on scales that disagree (1–10 vs percentage), and both key off **Lipinski violations**, which have no relationship to synthetic accessibility. The real Ertl–Schuffenhauer SA_Score ships with RDKit (`Contrib/SA_Score/sascorer.py`) and is not used.
- `retro_steps = int(2 + sa_score // 1.5)` (`:665`) converts the invented score into a "number of synthetic steps", surfaced as "Accessibility path: N synthetic steps". **No retrosynthesis is performed.**
- `generator.py:721` can render `"-2% (Accessible)"`.

---

### A25. MEDIUM — Lipinski applied more strictly than Lipinski.

- `generator.py:552` — Ro5 permits **one** violation ("no more than one"); this reports one violation as `"Fail"`, then penalizes it 25 points in `admet_fit` and 20 in `sa_fit`. Thresholds themselves (`:492-495`) are correct. `Descriptors.ExactMolWt` (monoisotopic) is used where Ro5 specifies average MW (`Descriptors.MolWt`).

---

### A26. MEDIUM — Fabricated cost, timing, and "confidence" metrics.

| Location | Code | Problem |
|---|---|---|
| `app.py:627-631` | `compute_duration = 0.25 + steps*0.05`; `qpu_cost_usd = 0.12 if is_qrl_optimized else 0.0`; `* 83.5` | Invented cost model; hardcoded FX rate; "Simulated access fee" reported as a real figure |
| `app.py:103` | `us_price * 95.0 * 0.15` | Comment claims "NPPA-regulated ratios"; **[EXECUTED]** `get_indian_price("isoniazid", 1.5)` → `21.38`, purely from this formula |
| `simulation.py:1080, 1318` | `elapsed_time_multiplier = 4.2 ** diff` | For `diff=10` the reported wall-clock is inflated 1.7 × 10⁶×. `elapsed_time` is not a measurement |
| `qrl_optimizer.py:2005-2019` | `f_dock % 8.0`; `vqe_std = 0.05`; `confidence = 100 - (docking_std*12 + vqe_std*50)` | Modulo of a physical energy, constructed so the result is always −14…−6 kcal/mol; `vqe_std` is a constant standing in for an unmeasured uncertainty |
| `simulation.py:1378-1379` | `cnot_base = active_orbitals**2 * 12` | Invented formula presented as a gate count; no transpilation performed |
| `test_accuracy_validation.py:124-136` | `quantum_scaling = f"{sim_qubits} Qubits (Polynomial O(N^4))"` | Nothing executed or timed; exponential-vs-polynomial advantage asserted by string literal |

---

### A27. MEDIUM — Pipeline narration describes software that never runs.

- `app.py:661` "Detected binding cavity via **P2Rank**"
- `app.py:667` "Generated **1000 candidate structures** from pre-trained SMILES LSTM" — the call is `evolve(num_candidates=5)`
- `app.py:673` "Completed **AutoDock Vina** binding pose optimization"
- `app.py:679` "Ran **100ns GROMACS/OpenMM** trajectory on top 20 leads"
- `app.py:685` "Refined local active space **CAS(4,4)**" — no active-space selection exists
- `generator.py:756` `f"Vina binding pose conformation energy: {scaled_docking:.2f} kcal/mol"`
- `test_drug_accuracy.py:61` "Running local **Genetic Algorithm**" — `evolve()` is pure LSTM sampling; there is no population, no selection, no crossover. `mutate_molecule` (`generator.py:170-216`) is **never called from any file**. The class name `EvolutionaryGenerator` and the method name `evolve` are equally unsupported.
- The `steps[].duration` values (400/600/1000/800/1200/1500/600 ms) are hardcoded.
- **Fix:** delete every tool name that is not executed. This is the cheapest high-impact remediation in the audit and should be done first.

---

### A28. MEDIUM — Fabricated defaults substituted silently on failure.

| Location | Value | Problem |
|---|---|---|
| `qrl_optimizer.py:1983-1986` | `mw = 137.1`, `logp = -0.7` | **Isoniazid's** MW and logP, substituted for any unparseable molecule, then emitted into `step_record` as if computed |
| `qrl_optimizer.py:2161`, `app.py:489` | `"CC1=CC=C(C=C1)C(=O)NN"` | Fake "FDA reference drug" (4-methylbenzohydrazide), paired with the fake name `"FDA Reference"` (`:2160`) |
| `app.py:477-482` | full `ref_details` dict — `mw 350.0, docking -8.0, kd '35.0 uM'`, … | Fabricated reference-drug profile returned when scoring fails |
| `app.py:556` | `druggability 0.85, volume 500.0, residues 12` | Hardcoded per-candidate "pocket detection" |
| `app.py:578, 582` | `pose_rms: 0.15`, `rmsd_trajectory: [0.05 … 0.16]` | Hardcoded ten-point MD trajectory |
| `app.py:718-719` | `similarity = 0.25`, `"Organic Aromatic Fragment"` | Returned when RDKit comparison fails, indistinguishable from a real result |
| `app.py:542` | `mutantBinding = docking + 0.5` | Constant mutation penalty |
| `qrl_optimizer.py:547, 709` | `except: novelty = 0.5` | Exception masquerading as a measurement |
| `qrl_optimizer.py:1962` | `except: r = -20.0` | Exception value enters the argmax as if it were a reward |
| `simulation.py:578-636` | H2/LiH: fully hardcoded 30-field dict incl. 15-point trajectory | Presented identically to computed results; no `is_reference` flag. `kd_value 0.84` vs `kd_text "841.4 mM"` are internally inconsistent (also `:626-627`) |
| `src/App.tsx:1078-1080` | `-10.4` kcal/mol, `-111.6366` / `-111.6772` Ha | UI seeded with fabricated "results" that render before any computation — a screenshot taken at load shows numbers that were never computed |

---

### A29. MEDIUM — Contradictory chemical identity for the flagship candidate.

- `simulation.py:60-79` gives `inh-q1` 18 atoms **including F, Cl, S**, with C–C separations of 3.6–4.3 Å — an unbonded point cloud, not a molecule.
- `simulation.py:91` gives `'inh-q1': 'CC1=CC=C(C=C1)C(=O)NNC(=O)C'` — C/N/O only, 13 heavy atoms, no halogens or sulfur.
- `get_preset_molecule_coords` prefers the coordinates (`:98-99`); `get_admet_and_docking_data:716-720` uses the SMILES. **The lead TB candidate has two mutually contradictory chemical identities feeding different parts of the same result object.**

---

### A30. MEDIUM — Reaction SMARTS are mislabelled and destructive.

- `qrl_optimizer.py:45` — `"ring_expansion_cyclopentyl_to_cyclohexyl"` produces a **seven**-membered ring (C1–C5 plus two unmapped C). It is cyclopentyl → cyclo**heptyl**. The wrong name propagates into the `"action"` telemetry string (`:2023`) and any figure derived from it.
- `:46` `ring_contraction_cyclohexyl_to_cyclopentyl` and `:44` `scaffold_hop_phenyl_to_thiophene` drop mapped atom `[C:6]`/`[c:6]`, **silently deleting that atom and every substituent on it**.
- `:47` `"linker_elongation": "[C:1][C:2] >> [C:1]CC[C:2]"` matches *any* C–C bond — maximally promiscuous.
- All transformations take `products[0][0]` (`:419`), so the reaction site is decided by RDKit's internal match ordering — arbitrary and undocumented.

---

### A31. MEDIUM — Docstrings contradict the code they document.

| Location | Claim | Contradicted by |
|---|---|---|
| `qrl_optimizer.py:433` | "No hardcoded pathogen name logic" | `:810-815` substring override |
| `qrl_optimizer.py:572` | "Zero hardcoded templates" | 48-entry `DISEASE_ALIASES` (`:924-972`); `from generator import PRESET_POCKETS` (`:16`) |
| `qrl_optimizer.py:1462` | "Uses ONLY authoritative, free public data sources" | `:1494-1505` hardcoded branch returning `'data_sources': ['hardcoded-toxicant']` |
| `simulation.py:246, 409` | "Hückel tight-binding solver", "diagonalizing" | **A6** — no matrix exists |
| `simulation.py:822` | "ground state converged" | **A9** — 43–92 kcal/mol error, printed unconditionally |
| `generator.py:11-22` | `# Re-declare LSTM class for pickle loading compatibility` | The checkpoint unpickles as `SmilesLSTM` (512 units / 3 layers); `MiniSMILESLSTM` (64/128/2) is not the architecture and is not needed. Dead code with a false explanation. Duplicated at `test_hybrid.py:14` |

---

### A32. LOW–MEDIUM — Data encoding is algebraically absorbed; four state features are destroyed.

- `qrl_optimizer.py:181-191` — nothing separates the encoding `RY(π·sᵢ)` from the variational `RY(θᵢ)` on the same wire. Since `RY(a)·RY(b) = RY(a+b)`, the circuit is **identical to a plain hardware-efficient ansatz** with `θ'ᵢ = θᵢ + π·sᵢ`. The docstring claim of "data re-uploading to enhance expressiveness" (`:174`) and "inject non-linearity" (`:202`) is false — no non-linearity is injected because the re-upload is not interleaved with non-commuting trainable operations.
- `:184-186` — features 8–11 (toxicity, QED, novelty, MW) are added as extra `RY` on qubits 0–3, which already carry features 0–3. Only the **sums** are observable: the policy provably cannot distinguish a high-docking/low-QED molecule from a low-docking/high-QED one.
- **Fix:** interleave encoding and variational layers, or use `ZZFeatureMap` + `RealAmplitudes`; map 12 features to ≥12 qubits or use a proper compression.

---

### A33. Scientifically **valid** components — credit where due

Not everything is fabricated. These are correct and should be preserved and foregrounded:

- **RDKit descriptor usage** — `Descriptors.MolLogP` (Wildman–Crippen), `Descriptors.TPSA`, `Lipinski.NumHDonors/NumHAcceptors/NumRotatableBonds`, `QED.qed` (Bickerton), `CalcMolFormula`, `AllChem.EmbedMolecule`/`MMFFOptimizeMolecule` (ETKDG + MMFF94), `rdFMCS.FindMCS` — `generator.py:482-488, 604, 227-230, 80`.
- **Morgan/Tanimoto similarity** — `app.py:730-733` uses the current `rdFingerprintGenerator.GetMorganGenerator` API correctly (not the deprecated `GetMorganFingerprintAsBitVect`).
- **Kd relation** — `generator.py:611` `Kd = 10**(ΔG/1.364)` is the correct 298 K form.
- **The LSTM checkpoint is genuine** — verified by loading: `smiles_lstm.model.smiles_lstm.SmilesLSTM`, vocabulary 57 tokens matching `_linear.out_features=57` and `_embedding.num_embeddings=57`, `max_sequence_length=256`, `{dropout: 0.2, layer_size: 512, num_layers: 3, cell_type: lstm, embedding_layer_size: 512}`, `training=False`. Vocabulary and checkpoint are self-consistent.
- **QPU co-design physics** — `simulation.py:858-1031` uses correct constants (Φ₀ = 2.067833848e-15 Wb, h, e, ε_r,Si = 11.7) and correct transmon relations `E_J = I_c Φ₀/2π`, `E_C = e²/2C`, `f_q = √(8E_J E_C) − E_C`, `α ≈ −E_C`, half-wave CPW `f_r = v/2L`. **This is the most defensible block in the repository.** Caveats: `g_mhz = 95.0·√(…)` (`:904`), `pocket_t1_factor` (`:916`), `e_1q ×1.45` (`:923`), `e_2q ×2.2` (`:928`) are uncalibrated fudge factors, and `eps_eff = (ε_r+1)/2` (`:897`) is the ideal-microstrip approximation rather than the CPW value. **Classification: questionable — structurally real, empirically uncalibrated.** Note `app.py:763` credits "Qiskit Metal", which is **not installed and never called**.
- **Public-database integration is real and current** — see **C1**.
- **`P08668`** (`test_hybrid.py:37`) is genuinely *Hantaan virus (strain 76-118)*, reviewed Swiss-Prot. **[LIVE-API]** — this hardcoded ID is correct.

---

# Part B — Security

### B1. CRITICAL — Live API keys on disk; one annotated as compromised.

- **`.env`** (correctly excluded by `.gitignore:7` and **absent from git history** — verified with `git log --all -- .env`) contains `GEMINI_API_KEY`, `APP_URL`, `NVIDIA_API_KEY`, **plus a comment containing a full Google API key in plaintext** with the text *"Rotate/revoke the compromised key (…) immediately!"*. A key written into a comment is still a live key.
- **`scratch/` — 5 files with a hardcoded NVIDIA key:** `list_nvidia_models.py:4`, `test_llama33.py:4`, `test_palmyra.py:5`, `test_llama31_verification.py`, `test_models_connection.py`. Untracked by git, but plaintext on disk and one `git add -A` away from publication.
- **Also:** `app.py:159` accepts an IBM Quantum `api_token` in the POST body and forwards it to `simulation.py`, where failures are `print()`ed (`:1145`) — tokens can reach stdout/logs.
- **Fix, in order:** (1) **revoke and rotate all three keys now** — the Gemini key must be treated as public; (2) delete the key text from the `.env` comment; (3) replace the `scratch/` literals with `os.getenv("NVIDIA_API_KEY")` and add `scratch/` to `.gitignore`; (4) run `gitleaks detect` / `trufflehog` over the full history before any public release; (5) never log exception bodies from authenticated calls.

### B2. CRITICAL — `debug=True` bound to all interfaces.

- `app.py:942` — `app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)`. The Werkzeug interactive debugger allows **arbitrary code execution** from any host that can reach port 5000. On a lab or campus network this is a full compromise of the machine.
- **Fix:** `debug=os.getenv("FLASK_DEBUG") == "1"`, default `host="127.0.0.1"`, and serve behind `gunicorn`/`waitress` for anything shared.

### B3. HIGH — Arbitrary code execution on model load.

- `utils.py:20` and `smiles_lstm/model/smiles_lstm.py:158` — `torch.load(file_path, weights_only=False)`. The checkpoint is a **full pickled object** (`torch.save(self, path)` at `smiles_lstm.py:172`), not a `state_dict`, so loading executes arbitrary pickle opcodes. torch 2.12 defaults to `weights_only=True`; both call sites explicitly opt out. Combined with **D1** (no checksum, undocumented origin), a reviewer who clones this repo executes unaudited code from a 25 MB binary.
- **Fix:** re-save as `state_dict`, load with `weights_only=True`, publish a SHA-256, and document provenance.

### B4. HIGH — Wide-open CORS on unauthenticated, network-calling endpoints.

- `app.py:13` — `CORS(app)` allows every origin. Every route is unauthenticated and unrate-limited; several trigger dozens of outbound HTTP requests (**C4**) and unbounded compute. Any web page the user visits can drive this server, and `/simulate` will forward a supplied IBM token.
- **Fix:** restrict `origins` to the dev host; add `flask-limiter`; require an API key for compute-heavy routes.

### B5. MEDIUM — Unbounded global state mutated from a threaded server.

- `app.py:134, 213, 757-758` — `history_records` is a module-level list appended on every `/simulate` and reassigned by `/history/clear`, under `threaded=True`. Unbounded growth (memory) plus a read/reassign race. Compounded by `simulation.py:935` `np.random.seed(100 + i)`, which reseeds the **process-global** NumPy RNG inside `calculate_qpu_codesign` — coupling every later `np.random` consumer (RMSD trajectories, DNA unwinding, MD velocities, dose-response noise) to `qpu_qubits`, across concurrent requests.
- **Fix:** bounded `collections.deque` with a lock, or SQLite; replace all global seeding with `np.random.default_rng(seed)` instances.

### B6. MEDIUM — Unvalidated numeric input crashes outside the handler.

- `app.py:154-171` — `int(...)`/`float(...)` on request fields run **before** the `try` at `:173`. A non-numeric `active_orbitals` raises `ValueError` → 500 → with **B2** active, an interactive debugger page. `active_orbitals` is also unbounded: `num_qubits = active_orbitals*2` feeds `NumPyMinimumEigensolver` on a dense 2ⁿ×2ⁿ matrix (`simulation.py:1117`), so `active_orbitals=12` → 24 qubits → OOM, caught at `:1120` and reported as `fci_energy = target_energy` — **the fake classical estimate returned as "exact FCI energy"**.
- **Fix:** validate with `pydantic` (already a dependency, currently unused); clamp `active_orbitals` to ≤6 with an explicit error.

### B7. LOW — `matplotlib.pyplot` in a threaded request handler.

- `app.py:834-849` and `qrl_optimizer.py:2107-2122` — `matplotlib.use('Agg')` is a global side effect executed per request; the pyplot figure manager is process-global and not thread-safe. `buf` is never closed. **Fix:** use the object-oriented `Figure` API.

---

# Part C — External API integrations

### C1. Verified working — **[LIVE-API]**, 2026-07-22

| Service | Endpoint | Status |
|---|---|---|
| AlphaFold DB | `alphafold.ebi.ac.uk/api/prediction/{acc}` | **200** |
| UniProt KB | `rest.uniprot.org/uniprotkb/{acc}.json`, `/search` | **200** |
| Open Targets | `api.platform.opentargets.org/api/v4/graphql` | **200**, apiVersion 26.6.3 |
| openFDA | `api.fda.gov/drug/drugsfda.json` | **200** |
| ChEMBL | `www.ebi.ac.uk/chembl/api/data/{molecule,mechanism,target}` | **200** |
| CMS NADAC | `data.medicaid.gov/api/1/datastore/query/fbb83258…/0` | **200**, real rows returned |
| PubChem PUG REST | `pubchem.ncbi.nlm.nih.gov/rest/pug/…` | **200** — but see **C2** |

Verified end to end: `fetch_nadac_price("ISONIAZID")` → `(1.61163, 'EA')`.

### C2. CRITICAL — `app.py`'s PubChem resolver is dead. Verified two ways.

- **File:** `app.py:116-123`
```python
116   url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{drug_name}/property/CanonicalSMILES/JSON"
122   if properties and "CanonicalSMILES" in properties[0]:
123       canonical_smiles = properties[0]["CanonicalSMILES"]
```
- **[LIVE-API]** PubChem has renamed the property. Requesting `CanonicalSMILES` returns:
```json
{"PropertyTable":{"Properties":[{"CID":3767,"ConnectivitySMILES":"C1=CN=CC=C1C(=O)NN"}]}}
```
  The key `CanonicalSMILES` is **never present**, so the guard at `:122` is always False. (Requesting `/property/SMILES/JSON` returns key `SMILES`.)
- **[EXECUTED]** `app.fetch_pubchem_smiles("isoniazid")` → `None`; `("aspirin")` → `None`. The function can never succeed.
- **Divergent duplicate:** `qrl_optimizer.py:891-916` is the **fixed** version — `:907` sniffs `next(k for k in properties[0] if "SMILES" in k)` — and works. Only one of the two copies was patched.
- **Downstream impact:** `app.py:424-428` silently fails to resolve reference-drug SMILES, so `/api/validation/run` falls through to the fabricated `ref_details` block (**A28**) and the fake SMILES default at `:489`.
- **Fix:** delete `app.py:108-130` and import the working function from `qrl_optimizer`. Request `/property/SMILES/JSON` explicitly and keep the key-sniffing fallback. Add a contract test that fails loudly when the resolver returns `None` for `isoniazid`.

### C3. CRITICAL — The IBM Quantum hardware path cannot execute. Three independent breakages.

- **File:** `simulation.py:1132-1146`, verified against the installed `qiskit-ibm-runtime 0.47.0`:

| Line | Code | Reality in 0.47.0 |
|---|---|---|
| 1135 | `QiskitRuntimeService(channel="ibm_quantum", …)` | `ChannelType = Literal['ibm_quantum_platform', 'ibm_cloud', 'local']`. `"ibm_quantum"` is **not valid** |
| 1141 | `Session(service=service, backend=backend)` | `Session.__init__(self, backend, max_time=None, *, create_new=True)` — **no `service` kwarg** → TypeError |
| 1142 | `Estimator(session=session)` | `Estimator` **is** `EstimatorV2`; signature `(mode, options)` — **no `session` kwarg** → TypeError |

- All three are swallowed by `except Exception` at `:1144`, which silently substitutes `StatevectorEstimator()`. `run_on_qpu` therefore stays `False` and **no hardware run has ever occurred**. Even if construction succeeded, `qiskit_algorithms.VQE` targets the V1 primitive interface and no ISA transpilation step precedes submission, which 0.47 requires.
- **Fix:** migrate to `QiskitRuntimeService(channel="ibm_quantum_platform")`, `Session(backend=backend)`, `EstimatorV2(mode=session)`, `transpile(ansatz, backend=backend)` before submission, and a V2-compatible optimizer loop (`scipy.optimize.minimize` over an `estimator.run([(isa_circuit, isa_observable, params)])` closure). **Until then, remove all "runs on real IBM quantum hardware" claims.**

### C4. HIGH — Unbounded blocking network fan-out inside request handlers.

- `qrl_optimizer.py:1908` (`resolve_pocket_and_reference`) internally calls `resolve_pathogen_metadata`, and `run_qrl_optimization` calls it **again** at `:2131`. Each call issues up to ~10 HTTP requests (Open Targets ×2, ChEMBL ×3, UniProt, openFDA, EMA, PubChem, AlphaFold ×2) with 10–15 s timeouts — worst case ≈2–5 minutes of blocking I/O per request. Because the two calls are independent, an API hiccup between them yields a reported `target_protein`/`uniprot_id` that **does not correspond to the pocket the optimization actually used**.
- No caching, no retry/backoff, no `User-Agent` (NCBI and EBI both request identification and rate-limit anonymous traffic).
- **Fix:** call once and thread the result through; add `requests_cache` + `urllib3.Retry` with exponential backoff; set a descriptive `User-Agent`; respect PubChem's 5 req/s limit.

### C5. HIGH — Nonexistent EMA endpoint; `False` returned for every drug.

- `qrl_optimizer.py:1420` — `https://www.ema.europa.eu/api/v1/medicines` → **[LIVE-API] HTTP 404**. There is no such public JSON API.
- `:1408` and `:1414` assign two further URLs that are never used. The comment at `:1418` concedes the endpoint is speculative. Any non-200 returns `False`, so `is_ema_approved` is **always False** — silently reporting every drug as not EU-approved.
- **Fix:** remove the field, or source EU approvals from the EMA's published EPAR spreadsheet with a dated snapshot committed to the repo.

### C6. MEDIUM — Fragile NADAC and myUpchar handling.

- `app.py:27` — dataset ID hardcoded and commented "the 2026 dataset"; **[LIVE-API]** returns rows with `effective_date: 2025-12-17`. CMS reissues dataset IDs; a rotation silently degrades to the invented Indian-price formula (**A26**). Pin the ID in config and log a warning on empty results.
- `app.py:58-89` — the myUpchar endpoint is `beta.`, undocumented publicly, and requires `MYUPCHAR_API_KEY`, which appears in **no** `.env.example`, README, or docs. Unverifiable by a third party. **Fix:** document it or remove the integration.

---

# Part D — Reproducibility

### D1. CRITICAL — The generative model has no documented provenance.

- `git log` shows the 25 MB `pretrained.rnn.pth` arriving in `1792a97 Initial commit`. There is no training script, no data-prep script, no config, and no checksum.
- The only provenance statements are two comments: `generator.py:383` "pre-trained ZINC LSTM model" and `:440` "Lazy load the ZINC LSTM model"; `real_benchmark.py:102` says outputs are "ZINC-like SMILES". **The string "ZINC" appears in no dataset file, download script, citation, or README.** Which ZINC release, which tranche, what filtering, how many epochs, what hyperparameters — all unrecorded.
- `README.md` is the **unmodified Google AI Studio scaffold** — it describes `npm install` and a `GEMINI_API_KEY` and mentions neither the science nor the model.
- **Licensing:** `smiles_lstm.py:2`, `smiles_vocabulary.py:2`, `smiles_trainer.py:2` all state "based on the REINVENT implementation" (AstraZeneca, Apache-2.0), yet the repository has **no LICENSE file anywhere** and `smiles_lstm/` has no NOTICE. Vendoring Apache-2.0-derived source without the license text is a defect that will block publication and any code release.
- **Fix:** document the corpus with a citation and a download script; publish a SHA-256; add the REINVENT `LICENSE` + `NOTICE`; add a top-level `LICENSE`; write a real README.

### D2. CRITICAL — Nothing is reproducible. Measured.

- **[EXECUTED]** two identical `run_vqe_simulation(molecule_id='inh-q1', active_orbitals=4, …, pathogen_name='Tuberculosis')` calls:

| | run 1 | run 2 |
|---|---|---|
| `final_energy` | −40.548814 | −40.567398 |
| `binding_energy` | −17.04 | −16.92 |
| `kd_text` | `0.00 nM` | `0.01 nM` |

  Two identical `simulate_wet_lab_validation` calls also differ.
- **Root cause:** a repo-wide grep finds exactly **one** seeding call — `simulation.py:935 np.random.seed(100 + i)` — and it is a *global* reseed inside an unrelated function (**B5**). There is no `torch.manual_seed`, no `random.seed` in `generator.py`, no seed on `VQE` (`:1165` omits `initial_point`, so the start point is drawn from the global RNG), no seed on COBYLA/SPSA, and no seed before the MD noise at `generator.py:707`. `AllChem.EmbedMolecule(randomSeed=42)` is the only deterministic step.
- **Consequence:** `test_drug_accuracy.py:62` and `test_accuracy_validation.py:58` both call `evolve()` directly, so **no number printed by either script is reproducible.**
- Separate display bug: `kd_text` renders `0.00 nM` — the formatting loses all precision for sub-nanomolar values.
- **Fix:** add `set_global_seed(seed)` called at app start and at every entry point; replace global `np.random` with per-call `default_rng(seed)`; pass `initial_point` to `VQE`; seed the optimizers; echo the seed in every response payload.

### D3. HIGH — The dependency manifest is not in version control, and one import is missing from it.

- **`requirements.txt` is untracked** (`git status` → `?? requirements.txt`). A fresh clone has no dependency list at all.
- `real_benchmark.py:6` imports `transformers` (`AutoTokenizer`, `AutoModel`) — **not in `requirements.txt`** and not installed. That benchmark cannot run.
- `pytest==8.2.2` is listed but **not installed**: `python -m pytest` → `No module named pytest`. The suite cannot be executed as shipped.
- `dist/` is gitignored (`.gitignore:3`) but `app.py:12` serves from it — a fresh clone cannot serve the frontend without an undocumented `npm run build`.
- **Also:** four core science files (`app.py`, `generator.py`, `qrl_optimizer.py`, `simulation.py`) currently have **uncommitted modifications**, so no result can be tied to a commit.
- **Fix:** `git add requirements.txt`; add `transformers`; pin with `pip-compile`; commit a `pyproject.toml` and an `environment.yml`; record the exact Python and OS; commit the working tree before generating any result for the paper.

### D4. HIGH — Undocumented hyperparameters on the critical path.

- `generator.py:462` — sequence length hardcoded to **128** while the checkpoint's `max_sequence_length` is **256** (verified). Every sequence is truncated at half the trained length; truncated SMILES are almost always invalid, silently biasing output toward short molecules and depressing the validity rate.
- `generator.py:466` — `probabilities = (logits / 0.8).softmax(dim=1)` — temperature **0.8 hardcoded and not a parameter of `evolve()`**, with the comment "to focus on high-probability tokens and increase validity". Any reported validity rate is a function of an undisclosed temperature. Meanwhile `SmilesLSTM._sample` (`smiles_lstm.py:317`) uses temperature 1.0, and `real_benchmark.py` uses a third path — three samplers, three behaviours.
- Also undocumented: `COBYLA(maxiter=40)` / `(maxiter=15)`, `TwoLocal(reps=3)`, `lr=0.05`, all nine reward weights, `num_qubits=8`, `num_residues=10`, `steps=15`, `temp=310.15` (note: inconsistent with the 298 K constant 1.364 used in the Kd conversion).
- **Fix:** move every one into a versioned `config.yaml`, echo the resolved config in each response, and log it alongside results.

### D5. MEDIUM — Sampling runs with autograd enabled.

- `generator.py:462-473` has no `torch.no_grad()` / `inference_mode()`. `smiles_lstm.py:285` shows the decorator was deliberately commented out (`# @torch.no_grad()`). Up to 150 attempts × 20 batch × 127 steps retains a graph across the whole generation — large memory growth and a substantial slowdown on the critical path.

### D6. MEDIUM — Eval mode is never set explicitly.

- `utils.py:4-23` is the loader actually used (`generator.py:443`) and never calls `.eval()`. Its docstring documents a `sampling_mode` parameter that **is not in the signature**. The parallel implementation that *does* handle eval mode (`smiles_lstm.py:144-162`) is dead. Today the checkpoint happens to be pickled with `training=False` (verified), so `dropout=0.2` is inactive — but **any re-save from a training script silently re-enables dropout at sampling time**, changing all published results with no error.

---

# Part E — Correctness bugs

### E1. CRITICAL — Empty SMILES become drug candidates. Verified.

- **File:** `generator.py:479-480`
```python
mol = Chem.MolFromSmiles(smiles)
if mol and smiles not in [c['smiles'] for c in valid_candidates]:
```
- **[EXECUTED]** `Chem.MolFromSmiles("")` returns a **truthy `Mol` with 0 atoms**, not `None`. Token `$` = 0 is the EOS token, so a model emitting `$` first yields `smiles == ""`, which passes `if mol` and is appended with `mw = 0.0`, `QED = 0.339`, `formula = ""`, `violations = 0` → `lipinski = "Pass (0 violations)"`. `generate_3d_coordinates` returns `[]`, so `calculate_docking_energy` early-returns `0.0` (`:281`) → `scaled_docking = -15.6 kcal/mol`.
- **An empty string is reported as a Lipinski-compliant, −15.6 kcal/mol drug candidate.**
- **Fix:** `if mol is not None and mol.GetNumAtoms() > 0:`

### E2. CRITICAL — `/simulate` 500s on its own default. Verified.

- **[EXECUTED]** `run_vqe_simulation(molecule_id='inh-q1', …)` with the default `pathogen_name=None` →
  `TypeError: 'NoneType' object is not iterable` at `simulation.py:1288` (`sum(ord(c) for c in pathogen_name)`).
- `app.py:161` sets `pathogen_name = data.get('pathogen_name', None)` and forwards it at `:192`. **Any `POST /simulate` omitting `pathogen_name` fails.**
- **Fix:** default to `"unknown"` and guard `if not pathogen_name`.

### E3. CRITICAL — `UnboundLocalError` in three exception handlers.

- `qrl_optimizer.py:512-514, 742-743, 2002-2003`
```python
510   qubit_op, target_energy = get_molecular_hamiltonian(...)
512   except Exception as e:
514       vqe_energy = target_energy      # ← never bound if line 510 raised
```
- `target_energy` is bound only by the tuple unpacking on the line that just failed, and is not a module global. **Any** failure in `get_molecular_hamiltonian` therefore raises `UnboundLocalError` *out of the handler meant to absorb it* — at `:2002` this propagates to `app.py:820` as HTTP 500. The intended fallback has never been exercised, i.e. never tested.

### E4. HIGH — `disease_info` can be referenced before assignment.

- `app.py:402-496` — if `disease != 'custom'` and `resolve_pathogen_metadata` does **not** return `status == "success"`, `disease` is never set to `'custom'`, the `if disease == 'custom':` block at `:415` is skipped, and `disease_info` is never assigned. Line 496 then reads it — **outside** the `try` that begins at `:504` — producing an unhandled `NameError` → 500, with the Werkzeug debugger exposed (**B2**).

### E5. HIGH — Silent in-place mutation of the caller's coordinates.

- `generator.py:374-376` writes back into `mol_coords[idx]`. `simulation.py:1305` passes `coords`, which at `:1240` is the **user's `custom_coords` list object**. After `:1305` the caller's molecule has been translated/rotated. `:1319` then computes ADMET on the mutated geometry, and `:1322` re-reads `coords`. Fsp3, planarity (`z_range`, `:1445-1446`), and the DNA-intercalation verdict are all geometry-dependent — **results depend on call order.**
- **Fix:** `copy.deepcopy` at the boundary, or return new coordinates.

### E6. HIGH — Device is taken from global CUDA availability, not from the tensors.

- `smiles_lstm.py:80-87` — `_device = get_device()` returns `"cuda"` whenever `torch.cuda.is_available()`, so the initial hidden state is allocated on GPU while `embedded_data` is on CPU → `RuntimeError: Expected all tensors to be on the same device` at `:90`. `generator.py:443` explicitly loads with `device="cpu"`; that argument is **unhonoured**. `SmilesLSTM.likelihood` (`:223`) has the mirror-image problem.
- **[UNVERIFIED at runtime]** — this box has `torch 2.12.1+cpu`, so the path was confirmed by reading only. It will fire on the first GPU machine, i.e. on most reviewers' hardware.
- **Fix:** derive the device from `input_vector.device`.

### E7. HIGH — Invalid gradient when the exploration mask contradicts the chosen action.

- `qrl_optimizer.py:1943-1944, 1952, 297` — if zeroing `mask[11]` empties the mask, `action_idx = 11` is chosen **while `mask[11] == 0`**. That mask is stored (`:2038`) and used in the update, where `probs[11] == 0` ⇒ `log π(a) = −∞`; `:297` computes a finite but meaningless number.
- Related: `get_valid_action_mask` returns all-zeros without applying its own `mask[-1] = 1.0` repair when the molecule is unparseable (`:93-95` returns early, bypassing `:121-122`); `:253-255` then silently substitutes a uniform distribution over **all** actions including invalid ones. And `:115-118` sets `mask = [1.0] * len(actions)` on error — "allow everything" — converting a masking failure into permission to attempt every invalid reaction.

### E8. HIGH — `real_benchmark.py`'s LSTM benchmark: broken stop condition, dead computation, fabricated verdict.

- `:174` prints `"100.0% chemically valid mutated leads"` as a **string literal**; nothing in `:131-154` measures validity.
- The "genetic evolution" at `:137-149` performs the **identical deterministic operation 20 times** (`h_atoms[0].SetAtomicNum(8)` on the same seed molecule). Not evolution, not stochastic, not a search.
- `:82` `if input_vector.sum() == 0: break` tests the **sum over the whole batch** — individual EOS is ignored.
- `:69/:80` `nlls` accumulated and never read.
- `:117` the ChemBERTa "batch of 50" is the same SMILES repeated 50×, so the latency benefits from identical padding — not representative.
- Header at `:13` reads `"RUNNING LIVE CPU BENCHMARKS (REAL MODELS)"`.

### E9. MEDIUM — Discontinuous, sign-broken score coercion.

- `simulation.py:674-675`
```python
if docking_score > -1.0:
    docking_score = -1.0 - abs(docking_score % 4.0)
```
Python's `%` wraps on negatives: `-0.5 % 4.0 == 3.5` → `-4.5`, while `+0.5 % 4.0 == 0.5` → `-1.5`. A tiny change across zero produces a 3 kcal/mol jump. Same modulo-of-an-energy pattern at `qrl_optimizer.py:2011`.

### E10. MEDIUM — Silent molecular-weight corruption.

- `simulation.py:647-660` covers only H, Li, C, N, O, F, Cl, S; `properties.get(el, {'mw': 1.0, …})` assigns **1.0 Da** to Br, I, P, B, Si, or any metal. A bromine-containing candidate is reported ~79 Da light, silently altering Lipinski violations, `drug_likeness`, and `sa_score`. Same defect at `:1440-1442` (defaults to 12.0).

### E11. MEDIUM — Chemically impossible fallback geometry returned unflagged.

- `simulation.py:124-135` and `generator.py:258-268` — on RDKit embedding failure all atoms are placed at `x = i * 1.2, y = 0, z = 0` with charges zeroed. This flows into `calculate_coordinate_energy`, the Fsp3 planarity test (`z_range == 0` → `is_planar = True`), and `analyze_dna_interaction`, which will classify it as an intercalator. No flag is returned. The comment says the purpose is that "the frontend ALWAYS receives coordinates and never crashes" — i.e. UI convenience was chosen over correctness.

### E12. MEDIUM — Single-start local minimization presented as pose optimization.

- `generator.py:356-377` — one `L-BFGS-B` run from `[0,0,0,0,0,0]` over a 6-DOF `r⁻¹²` landscape returns a local minimum. Real docking uses stochastic multi-start/MC/GA precisely because this surface is pathological. No `maxiter`, no convergence check beyond `res.success`, rigid receptor, and only the single ETKDG conformer from `:227` is scored. The `res.success` guard at `:368` means a failed optimization returns `res.fun` from a non-converged state while leaving `mol_coords` un-updated — **the returned energy and the returned coordinates then disagree.**

### E13. MEDIUM — `smiles_trainer.py` defects.

- `:291` — catches `RuntimeError`, but `MolToSmiles(None, …)` raises `Boost.Python.ArgumentError`, whose MRO is `(ArgumentError, TypeError, Exception, BaseException)` — **not** a `RuntimeError`. Training aborts on the first unparseable SMILES when `augment > 0`.
- `:257-259` — `raise IOError(f"…supplied file: {path}")` interpolates the **`os.path` module** imported at `:6`; renders as `<module 'ntpath' from …>`.
- `:176-182` — "best model" tracking never selects a best model: `_best_epoch` stays `None` when epoch 0 is best, `_save_current_model` runs unconditionally, and `_best_epoch` is never read.
- `:261-265` — one `_initialize_dataloader` serves all three splits with `drop_last=True` and `shuffle=True`, so **validation silently discards up to `batch_size-1` (default 250) molecules** and is shuffled. With a validation set < 250 the loader is empty, `torch.mean` gives `nan`, and the checkpoint comparison at `:178` is always False.
- `:360` — the test dataloader is constructed and **never used**; `run()` evaluates train and valid only. **There is no test-set evaluation path in the codebase.**
- `:252` and `smiles_vocabulary.py:157` — `smiles_list += …` mutates the caller's list in place.

### E14. MEDIUM — Three incompatible similarity metrics, one mislabelled as Tanimoto.

```python
generator.py:84-85            return res.numAtoms / mol2.GetNumHeavyAtoms()
test_drug_accuracy.py:45-46   return res.numAtoms / max(mol1.GetNumHeavyAtoms(), mol2.GetNumHeavyAtoms())
test_accuracy_validation.py   return res.numAtoms / mol2.GetNumHeavyAtoms()
```
- The same candidate/reference pair yields **different published percentages** depending on which script produced the table.
- `test_drug_accuracy.py:70` prints the MCS overlap as `"Tanimoto Similarity"`. `TanimotoSimilarity` and `AllChem` are imported at `:6-7` and never used — creating the appearance of fingerprint similarity that is not performed.
- `generator.py:585-595` names the MCS ratio `"{n}% FDA Overlap"` — an official-sounding name for a metric with no literature basis. It also truncates rather than rounds.
- `rdFMCS.FindMCS` is called with all defaults everywhere — no `ringMatchesRingOnly`, no `completeRingsOnly`, so the MCS may be a chemically meaningless chain fragment; the default `timeout` is 3600 s (hang risk).

### E15. LOW–MEDIUM — Other correctness issues.

- `generator.py:907-913` — duplicated `print` + `return None` **after** a `return`; unreachable. Signals a bad merge; check whether anything else was lost.
- `generator.py:768-909` — a 140-line `try` wrapping all of `score_molecule`, returning `None` on any failure. Callers (`app.py:472,498,507`; `qrl_optimizer.py:2052-2073`) cannot distinguish "invalid SMILES" from "SciPy crashed" from "circular import".
- `generator.py:516-530` vs `:774-786` — the pathogen-key mapping duplicated verbatim, substring-based, and mis-firing (`'hiv'`, `'cyan'`, `'tb'` match unrelated organism names).
- `generator.py:718` (`mutantBinding = scaled_docking + 0.5`) vs `:876-879` (re-dock against a perturbed pocket) — the same UI field is populated by a constant in one path and a calculation in the other.
- `generator.py:625` — `admet_fit = 100 - violations*25 - tox_penalty` is **not clamped**, while its siblings `docking_fit` and `sa_fit` both are; it reaches −30 and drags `fitness_score` off a common scale.
- `simulation.py:1471` — `[el for el in elements if el in ('C','N') and el != 'H']`: the second clause is unreachable, and the variable counts *all* C/N whether aromatic or not, then drives the intercalation verdict.
- `simulation.py:1901-1907` — the dose-response curve is Kd-invariant by construction (see **A18**).
- `simulation.py:1109` — `noise_level` silently discards the caller's argument whenever `codesign_active`.
- `simulation.py:1650` — `float(f"{x:.2e}")` used as a rounding primitive.
- `smiles_lstm.py:243-261` — `sample_smiles(num=0)` → `np.concatenate([])` → `ValueError`.
- `smiles_lstm.py:80` — `get_device()` called on **every forward pass** (127× per batch × 150 attempts).
- `misc.py:112` — `csv.writer(output_file, delimiter="\n")` abuses the field delimiter as a line separator; any SMILES containing `,` or `"` gets quoted and corrupted.
- `misc.py:53-56` — `fraction_valid` uses `MolFromSmiles(sanitize=False)` + `UpdatePropertyCache` + `Kekulize`, a **looser** definition than the field standard, so the reported validity is inflated and not comparable to published numbers. The `if mol is not None` check is dead — the preceding line would already have raised.
- `load.py:15-18` — `smi_file.close()` sits outside the `with` and operates on an already-closed handle; `load.smiles` hardcodes `delimiter=" "` and a `"SMILES"` column with no error handling.
- `generator.py:469-473`, `real_benchmark.py:79-85` — `int64` and `float32` mixed in `torch.cat`, then cast back with `.long()`.

---

# Part F — Software engineering

### F1. HIGH — The test suite cannot run, and most of it asserts nothing.

| File | `test_*` functions | assertions |
|---|---|---|
| `test_accuracy_validation.py` | 0 | **0** |
| `test_alphafold_api.py` | 1 | **0** |
| `test_drug_accuracy.py` | 0 | **0** |
| `test_hybrid.py` | 0 | **0** |
| `test_validation_endpoints.py` | 0 | **0** |
| `test_integration.py` | 1 | **0** |
| `test_qrl_endpoints.py` | 2 | 12 |
| `test_simulation.py` | 4 | 28 |
| `test_wet_lab.py` | 3 | 18 |

- `pytest` is **not installed** (**D3**), so nothing runs as shipped.
- Files named `test_*.py` with no `test_*` functions collect as 0 tests while appearing in the suite — a false sense of coverage.
- `test_integration.py` launches a real server via `subprocess.Popen` + `time.sleep(8)` and is collected by pytest — importing the suite **starts a Flask server**.
- Where assertions exist they check key presence, not values: `test_wet_lab.py` is three `assertIn` calls; `test_qrl_endpoints.py` checks HTTP 200 and that `circuit_ascii` is a string, never `status`, never that the molecule changed, never that a number is finite.
- `test_hybrid.py` is a print script: hardcoded inputs mislabelled as retrieved (`:36 # Load from cache` above `:37 uniprot_id = "P08668"`), a silent `return` at `:87` on model-load failure, and a **tautological conclusion** — `:176` clamps every score to ≤ −6.0, then `:205` prints "The candidates show strong predicted binding affinity (< -6.0 kcal/mol)". The clamp guarantees the claim. Candidates are unconditional LSTM samples with **no target awareness**, yet named `"HANTA-LSTM-Lead-{n}"`.
- `test_drug_accuracy.py:71-76` has **no failing branch** — overlap < 0.3 prints `"[NOVEL CORE] Explores novel structural conformations"`, so a completely unrelated molecule is a success.
- Every test hits live third-party APIs with no mocking — non-hermetic, slow, and red whenever any provider is down.
- **Fix:** install `pytest`; convert to real assertions; mock all network with `responses`/`respx`; mark network tests `@pytest.mark.integration` and exclude by default; move `test_integration.py` behind a fixture; add regression tests pinning the numbers in **A7**, **A20**, **E1**, **E2**.

### F2. HIGH — 65 broad exception handlers; failures are invisible.

- `except Exception` / bare `except` counts: `app.py` 20, `generator.py` 8, `simulation.py` 7, `qrl_optimizer.py` 30.
- Bare `except:` (catches `KeyboardInterrupt`/`SystemExit`): `simulation.py:1183, 1880`; `generator.py:242`; `qrl_optimizer.py:547, 709, 1897, 1936, 1962, 1993, 2148`; `misc.py:60, 78`; `smiles_vocabulary.py:154`.
- Several replace a failed computation with an invented value (**A28**), so an exception becomes a scientific result.
- There is **no `logging` anywhere** — every diagnostic is a bare `print()` to stdout, lost when served under a WSGI server.
- **Fix:** replace with `logging` at module level; catch specific exceptions; never substitute a fabricated value — propagate a typed error and surface it in the response.

### F3. HIGH — Duplication at scale.

- `-14.0 + 0.8*(x - 2.0)` appears **four** times with **disagreeing clamps**: `qrl_optimizer.py:458, 727, 732` and `simulation.py:1306` use `[-22, -6]`; `test_hybrid.py:176` uses `[-14, -6]`. **The same quantity is reported on two different scales in the same project.**
- The Fsp3 + toxicity block is duplicated **four** times verbatim (`simulation.py:277-302, 432-456, 1448-1467`, `scratch_huckel_test.py:82-107`); the isocyanate detector twice (`simulation.py:304-334, 458-488`) — and it is **O(n⁴)** (four nested loops with a `sqrt` innermost; ~10⁸ distance evaluations for a 100-atom ligand, called 3× per simulation).
- The VQE-with-fallback block is copy-pasted three times in `qrl_optimizer.py`, all three carrying the **E3** `UnboundLocalError`.
- Morgan/Tanimoto novelty duplicated at `qrl_optimizer.py:538-548` and `:700-710`.
- `simulate_mutant_pocket = simulate_adversarial_mutant_pocket` (`:663`) — two public names for one function.
- `fetch_pubchem_smiles` duplicated across `app.py` and `qrl_optimizer.py`, **only one fixed** (**C2**).
- `normalize_name` duplicated at `app.py:224` and `app.py:430`.
- `MiniSMILESLSTM` duplicated at `generator.py:11` and `test_hybrid.py:14`.

### F4. MEDIUM — Architecture.

- **Circular dependency**, deliberately deferred to function scope: `simulation.py:1281` imports `generator`, `generator.py:555` imports `simulation` — **inside a per-candidate loop**, re-executing import machinery for every candidate. Same pattern at `generator.py:357, 423, 794, 801, 863`; `qrl_optimizer.py:613, 836-838, 871, 901, 911, 990, 1277, 1343, 1399, 1474, 2107-2110`.
- Four monolithic modules: `qrl_optimizer.py` 2172 lines, `simulation.py` 1977, `generator.py` 913, `app.py` 945. No package structure, no `__init__.py` in either `smiles_lstm` subpackage (imports work only via implicit namespace packages and break under `pip install -e`).
- No layering: HTTP handling, business logic, science, and presentation strings are interleaved in `app.py`.
- No packaging: no `pyproject.toml`, `setup.py`, or `setup.cfg`. No CI: no `.github/`, no `.gitlab-ci.yml`. No linter or formatter config; no type checking (`mypy`/`pyright`) despite `pydantic` being a declared dependency.
- `generator.py:8` — a top-level module named `utils` colliding conceptually with `smiles_lstm/utils/`; resolution depends on `sys.path` order.

### F5. MEDIUM — Performance.

- `qrl_optimizer.py:281-290` — `compute_parameter_shift_gradients` runs `1 + 2×32 = 65` statevector simulations **per timestep** (~325 circuit executions per 5-step episode) whose output is then **discarded** (**A3**).
- `qrl_optimizer.py:358-359, 394-395, 1956-1966` — `env.step` calls `get_state()` (full 3D embed + MD + VQE + docking) **and** `calculate_reward` (another embed + MD + VQE + two dockings), plus up to 3 candidate rewards: **~5 full biophysics pipelines per step**.
- `qrl_optimizer.py:694-695` — `PAINS_SMARTS` re-parsed with `Chem.MolFromSmarts` on **every** reward call instead of compiled once.
- `generator.py:480` — O(n²) dedup rebuilding a list per candidate; should be a `set`. The same loop computes 7 RDKit descriptors *before* the dedup could reject.
- `simulation.py:306-334, 460-488` — the O(n⁴) isocyanate detector (**F3**).

### F6. MEDIUM — Documentation.

- `README.md` is the untouched AI Studio scaffold — wrong content entirely.
- No architecture diagram in the repo (only in `ppt.md`), no API reference, no docstring coverage standard, no CHANGELOG, no CONTRIBUTING, no LICENSE.
- `completeworkflow.md:129` attributes the model to REINVENT; `ppt.md:198-205` lists 8 references. **Spot-checked and genuine:** Lovering, Bikker & Humblet (2009) *J. Med. Chem.* 52(21):6752-6756 "Escape from Flatland" — correct citation. **No fabricated bibliography was found** — a genuine positive. The uncheckable "Wang et al." in `simulation.py:1882` (**A23**) is the only citation-shaped claim that cannot be verified.
- `completeworkflow.md:12` states narrow HOMO–LUMO gaps `< 8 eV` raise toxicity alerts — unsupported, and would flag essentially every drug molecule.
- `ppt.md:9` claims "unprecedented accuracy"; `completeworkflow.md:8` claims "reducing traditional timelines from years to hours". Neither is measured anywhere.

### F7. LOW — Dead code inventory.

`generator.py`: `MUTATION_GROUPS` (`:57-64`), `mutate_molecule` (`:170-216`), `MiniSMILESLSTM` (`:11-22`), the `attachments` loop (`:204-208`, all tuples carry `[]`).
`qrl_optimizer.py`: `select_action` (`:260-266`), `PRESET_POCKETS` import (`:16`), `import os`/`import json` (`:2-3`), `expectations` (`:1947`), `prob` (`:1970`), `logp`/`hbd`/`hba`/`tpsa` (`:441-445`), empty numbered comments (`:535, 550`), unused URLs (`:1408, 1414`).
`simulation.py`: `SLSQP` import (`:5`), `json`/`os` (`:1243-1244`), `n_atoms`/`base_factor` (`:1323-1324`), re-imports of `numpy`/`Chem` inside functions (`:1698, 1860, 1862`).
`smiles_lstm.py`: `load_from_file` (`:144-162`), `_sample` (`:285`).
`smiles_trainer.py`: `_test_dataloader` (`:75-77`).
`app.py`: stray `pass` at `:365, 391, 438, 456, 510` (leftovers from removed overrides); `fda = disease_info.get('fda_drug_details')` duplicated at `:611` and `:616`.
Tests: unused imports at `test_drug_accuracy.py:6-7`, `test_accuracy_validation.py:1-4`.
`scratch_huckel_test.py:132`: `size_factor` computed, never used.

---

# Part G — Recommended remediation order

**Phase 0 — do today (hours)**
1. **Revoke and rotate all three API keys** (**B1**). Treat the Gemini key as public.
2. `debug=False`, bind `127.0.0.1` (**B2**).
3. Delete every false tool attribution: "P2Rank", "AutoDock Vina", "GROMACS/OpenMM", "1000 candidates", "CAS(4,4)", "Genetic Algorithm", "Qiskit Metal", "100ns" (**A27**, `app.py:661-693`, `generator.py:756`, `qrl_optimizer.py:462-463`).
4. Delete the `PASSED` / `[SUCCESS]` / `[PROVED]` literals (**A8**).
5. Delete "Lead Polishing" (**A5**).
6. Rename `measured_binding` → `synthetic_binding` and add a SYNTHETIC banner (**A18**).
7. `git add requirements.txt`; commit the working tree (**D3**).

**Phase 1 — one week**
8. Fix **E1**, **E2**, **E3**, **E4** (four crashes / silent-corruption bugs).
9. Fix **C2** (delete the dead PubChem copy, import the working one) and **C3**/**C5** (remove or migrate the IBM and EMA paths).
10. Global seeding + echo the seed in every response (**D2**).
11. Install `pytest`; add regression tests pinning **A7**, **A20**, **E1**, **E2**.
12. Fix **A20** (inverted fitness sign) and **A7**'s unit error.
13. Add `LICENSE` + REINVENT `NOTICE`; write a real `README.md` (**D1**).

**Phase 2 — one month, choose a lane**
- **Lane A — make the science real:** Qiskit Nature + PySCF for a genuine Hamiltonian (**A1**); smina/Vina for docking (**A7**); RDKit `sascorer` + `FilterCatalog` (**A22**, **A24**); a real RL loop with persistence and on-policy sampling (**A3**, **A4**); benchmark against PDBbind/DUD-E and the MOSES/GuacaMol battery.
- **Lane B — relabel honestly:** keep the heuristics, delete every "VQE / Hartree / FCI / ADMET / MD / wet-lab" label, and publish it as *an integrated pipeline and UI for quantum-inspired molecular design, with illustrative scoring*. This is a legitimate systems/education contribution and is achievable in weeks rather than months.

Both lanes are publishable. The current state — Lane B's implementation carrying Lane A's claims — is not.

---

# Part H — Concrete fixes: exact patches

Every fix below is written against the code as audited on 2026-07-22. **Line numbers shift as you apply patches — match on the quoted code, not the line number.** Apply in the order given; each phase is independently commit-able and leaves the system working.

Target after Phase 0 + 1 + 2: **research readiness 7.2 / 10** (see `audit_summary.md` §9 for the score arithmetic; `audit_summary.md` §10 and `research_improvements.md` §10 cost the further route to 9.1).

---

## H.0 — Phase 0 patches (hours, mostly deletions)

### H.0.1 — Secrets (**B1**)

`.env` — delete the key text from the comment. The comment currently contains a live key:
```diff
- # Rotate/revoke the compromised key (AIzaSy...) immediately!
+ # NOTE: the previous value of this key was exposed and has been revoked.
  GEMINI_API_KEY=...
```

`scratch/list_nvidia_models.py`, `scratch/test_llama33.py`, `scratch/test_palmyra.py`, `scratch/test_llama31_verification.py`, `scratch/test_models_connection.py`:
```diff
- api_key = "nvapi-..."
+ import os
+ api_key = os.environ["NVIDIA_API_KEY"]   # raises if unset — fail loud, never fall back
```

`.gitignore`:
```diff
  venv/
  __pycache__/
+ scratch/
+ *.bak.md
```

Then, before any public release:
```bash
pip install gitleaks-py detect-secrets
gitleaks detect --source . --no-git       # working tree
gitleaks detect --source .                 # full history
```

### H.0.2 — Debug server (**B2**)

`app.py:940-942`:
```diff
  if __name__ == '__main__':
-     # Using port 5000 as configured in the architectural plan, enabling threading for concurrent health-checks
-     app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
+     debug = os.getenv("FLASK_DEBUG") == "1"
+     host  = os.getenv("FLASK_HOST", "127.0.0.1")
+     if debug and host != "127.0.0.1":
+         raise SystemExit("Refusing to run the Werkzeug debugger on a non-loopback interface.")
+     app.run(host=host, port=int(os.getenv("PORT", 5000)), debug=debug, threaded=True)
```
For anything shared, serve with `waitress-serve --host 127.0.0.1 --port 5000 app:app`.

### H.0.3 — Delete "Lead Polishing" (**A5**)

`qrl_optimizer.py:2050-2084` — delete the entire block. It begins at the comment `# Lead Polishing: ensure the QRL candidate beats the reference drug's free energy` and ends after the `best_smiles = polished_smiles` assignment. Nothing downstream depends on it beyond `best_smiles`, which is already set by the rollout loop.

If a rule-based refinement stage is genuinely wanted, make it **unconditional** and report both numbers:
```python
# Always applied, never conditioned on the comparison outcome.
agent_smiles = best_smiles
refined_smiles = apply_refinement_rules(best_smiles)   # deterministic, seeded
result["candidate_agent_only"] = score(agent_smiles)
result["candidate_refined"]    = score(refined_smiles)
result["refinement_applied"]   = True
```

### H.0.4 — Remove false tool attributions (**A27**)

`app.py:651-694` — the `steps` list. Replace each fabricated `detail` with what actually ran, and delete the hardcoded `duration` values (or rename the field to `display_duration_ms` so nobody reads them as measurements):

```diff
- "detail": f"Detected binding cavity via P2Rank. Volume: {...}, Druggability Score: {...}",
+ "detail": f"Binding-site atoms resolved from {pocket_source}."
+            # pocket_source ∈ {"AlphaFold PDB", "curated reference set"}; never a hash

- "detail": "Generated 1000 candidate structures from pre-trained SMILES LSTM model & filtered via Lipinski/toxicity constraints.",
+ "detail": f"Sampled {n_sampled} SMILES from the pretrained LSTM; {len(candidates)} passed RDKit validity and Lipinski filtering.",

- "detail": f"Completed AutoDock Vina binding pose optimization. Top candidate score: {...} kcal/mol.",
+ "detail": f"Rigid-ligand pose optimization (L-BFGS-B, 6 DOF) against the pocket atoms. Heuristic score: {...} (arbitrary units — not benchmarked).",

- "detail": f"Ran 100ns GROMACS/OpenMM trajectory on top 20 leads. Measured average RMSF: {...} nm, Stability: {...}%.",
+ "detail": f"Langevin integration, {md_steps} steps at {md_temp} K, on the top candidate. Trajectory is illustrative, not a production MD run.",

- "detail": "Refined local active space CAS(4,4) electronic ground-state interactions on top 5 leads using Qiskit VQE optimizer.",
+ "detail": f"VQE on a {n_qubits}-qubit model Hamiltonian (not an electronic-structure Hamiltonian). See limitations.",
```

`generator.py:756`:
```diff
- f"Vina binding pose conformation energy: {scaled_docking:.2f} kcal/mol",
+ f"Heuristic pose score: {scaled_docking:.2f} (arbitrary units, not benchmarked)",
```

`qrl_optimizer.py:462-463` — delete both comment lines; there is no 100 ns path.
`app.py:763` — remove "from Qiskit Metal specs"; `qiskit-metal` is not installed.
`test_drug_accuracy.py:61` — "Genetic Algorithm" → "pretrained SMILES LSTM sampling".

### H.0.5 — Delete unconditional success strings (**A8**)

`test_accuracy_validation.py`:
```diff
- print(f"  Quantum Chemistry Solver Accuracy (vs FCI): {quantum_accuracy:.4f}% (PASSED >95% goal)")
+ THRESHOLD = 95.0
+ verdict = "PASS" if quantum_accuracy >= THRESHOLD else "FAIL"
+ print(f"  VQE vs exact diagonalization of the same operator: {quantum_accuracy:.4f}%  [{verdict} @ {THRESHOLD}%]")
+ print("  NOTE: this is self-consistency, not an independent FCI reference. See fix.md A8.")

- print("[SUCCESS] Platform successfully validated as genuine, accurate, and scalable.")
+ if verdict == "FAIL":
+     raise SystemExit(1)
```
`:82` — delete `[PROVED]`; replace with `[INFO] Scaffold overlap: {x:.1f}%`.

`simulation.py:822` — the unconditional `"VQE active space electronic ground state converged."` must become conditional on `result.optimizer_result.nfev` and the FCI gap (see **H.1.8**).

### H.0.6 — Relabel synthetic data (**A18**)

`simulation.py:1899-1910`:
```diff
- measured = ideal_binding + np.random.normal(0, std_dev)
- ...
- "measured_binding": measured_binding,
+ simulated = ideal_binding + rng.normal(0, std_dev)
+ ...
+ "synthetic_binding": simulated_binding,
+ "is_synthetic": True,
+ "synthetic_note": ("Values are drawn from a Hill curve at fixed multiples of the predicted Kd "
+                    "plus Gaussian noise. They contain no molecule-specific information and are "
+                    "NOT experimental measurements."),
```
`app.py:917` — rename the route:
```diff
- @app.route('/api/validation/wetlab', methods=['POST'])
+ @app.route('/api/simulation/dose_response_synthetic', methods=['POST'])
```
Frontend: render a persistent banner wherever `is_synthetic` is true. Keep the old route as a 308 redirect for one release if the UI needs it.

### H.0.7 — Version control (**D3**)

```bash
git add requirements.txt
echo "transformers==4.57.1" >> requirements.txt   # imported by real_benchmark.py, currently missing
pip install pytest==8.2.2                          # listed but not installed
git add -A && git commit -m "chore: track requirements, remove secrets, disable debug server"
```

---

## H.1 — Phase 1 patches (one week)

### H.1.1 — Empty SMILES accepted as candidates (**E1**)

`generator.py:479-480`:
```diff
  mol = Chem.MolFromSmiles(smiles)
- if mol and smiles not in [c['smiles'] for c in valid_candidates]:
+ if mol is not None and mol.GetNumAtoms() > 0 and smiles not in seen_smiles:
+     seen_smiles.add(smiles)
```
Add `seen_smiles = set()` before the loop — this also fixes the O(n²) dedup (**F5**).

Regression test:
```python
def test_empty_smiles_rejected():
    from rdkit import Chem
    m = Chem.MolFromSmiles("")
    assert m is not None and m.GetNumAtoms() == 0, "RDKit contract changed"
    gen = EvolutionaryGenerator()
    assert gen.score_molecule("", "Tuberculosis") is None
```

### H.1.2 — `/simulate` crashes on its own default (**E2**)

`app.py:161`:
```diff
- pathogen_name = data.get('pathogen_name', None)
+ pathogen_name = (data.get('pathogen_name') or 'unknown').strip() or 'unknown'
```
`simulation.py:1285-1288` — guard anyway, so the function is safe for every caller:
```diff
- seed = sum(ord(c) for c in pathogen_name)
+ if not pathogen_name:
+     raise ValueError("pathogen_name is required to resolve a binding pocket")
+ seed = sum(ord(c) for c in pathogen_name)
```

### H.1.3 — `UnboundLocalError` in three handlers (**E3**)

`qrl_optimizer.py:509-521`, `739-750`, `1999-2003` — all three have the same shape:
```diff
+ qubit_op, target_energy = None, None
  try:
      qubit_op, target_energy = get_molecular_hamiltonian(...)
      vqe_energy = run_actual_vqe(qubit_op, active_orbitals)
  except Exception as e:
-     vqe_energy = target_energy
+     logger.warning("Hamiltonian/VQE failed for %s: %s", smiles, e)
+     vqe_energy = None          # propagate absence, do not invent a number
```
Then every consumer must handle `None` explicitly rather than treating it as an energy. The three copies should be collapsed into one helper (**F3**).

### H.1.4 — `disease_info` possibly unbound (**E4**)

`app.py:396-496`:
```diff
  def run_validation():
      data = request.json or {}
      disease = data.get('disease', 'covid-19').strip().lower()
+     disease_info = None
      ...
+     if disease_info is None:
+         return jsonify({"status": "unresolved_target",
+                         "error": f"Could not resolve metadata for '{disease}'."}), 422
      if disease_info and disease_info.get('fda_drug_smiles'):
```

### H.1.5 — Dead AlphaFold pocket path (**A10c**)

`simulation.py:1281` uses `gen` before `:1304` assigns it. Move the construction to module scope (it is stateless) and delete the local:
```diff
+ # module level, after imports
+ _GENERATOR = None
+ def _get_generator():
+     global _GENERATOR
+     if _GENERATOR is None:
+         from generator import EvolutionaryGenerator
+         _GENERATOR = EvolutionaryGenerator()
+     return _GENERATOR
```
```diff
- pocket_residues = gen.parse_pdb_to_pocket(pdb_res.text, num_residues=10)
+ pocket_residues = _get_generator().parse_pdb_to_pocket(pdb_res.text, num_residues=10)
```

### H.1.6 — Never fabricate a pocket (**A10b, A11, A12**)

Replace all three hash-seeded pocket generators (`generator.py:420-438`, `qrl_optimizer.py:869-886`, `simulation.py:1285-1302`) and the silent TB substitution (`generator.py:813-814`) with an explicit failure:
```python
class TargetUnresolved(RuntimeError):
    """Raised when no structural data could be obtained for the requested target."""

def resolve_pocket(pathogen_name, uniprot_id=None):
    pocket = _try_alphafold(uniprot_id) or _try_curated_reference(pathogen_name)
    if pocket is None:
        raise TargetUnresolved(
            f"No structure available for '{pathogen_name}'. "
            f"Provide a UniProt accession or select a target from the curated set."
        )
    return pocket   # carries {"source": "alphafold"|"curated", "uniprot_id": ...}
```
`qrl_optimizer.py:1480-1489` — stop reporting success when nothing resolved:
```diff
- return {"status": "success", ...}
+ status = "success" if data_sources else "unresolved"
+ return {"status": status, "data_sources": data_sources, ...}
```
And reject the placeholder accession outright:
```python
if uniprot_id == "P12345":
    raise TargetUnresolved("Placeholder accession P12345 is not a valid target.")
```

### H.1.7 — PubChem resolver (**C2**)

Delete `app.py:108-130` entirely and import the working implementation:
```diff
- def fetch_pubchem_smiles(drug_name):
-     ...
+ from qrl_optimizer import fetch_pubchem_smiles   # single implementation, key-sniffing
```
Then harden the surviving copy — request the current property name explicitly and keep the sniff as a fallback:
```python
url = (f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
       f"{quote(drug_name.strip())}/property/SMILES,ConnectivitySMILES/JSON")
...
props = data.get("PropertyTable", {}).get("Properties", [])
if props:
    key = next((k for k in ("SMILES", "ConnectivitySMILES", "CanonicalSMILES")
                if k in props[0]), None)
```
Contract test that fails loudly if PubChem renames the property again:
```python
@pytest.mark.integration
def test_pubchem_contract():
    smi = fetch_pubchem_smiles("isoniazid")
    assert smi is not None, "PubChem property name changed — see fix.md C2"
    assert Chem.MolFromSmiles(smi).GetNumAtoms() == 10
```

### H.1.8 — IBM Runtime path (**C3**) and optimizer budget (**A9**)

Either delete the QPU branch and every "runs on real quantum hardware" claim, or migrate it. Correct form for `qiskit-ibm-runtime 0.47.0`:
```python
from qiskit_ibm_runtime import QiskitRuntimeService, Session, EstimatorV2
from qiskit import transpile

service = QiskitRuntimeService(channel="ibm_quantum_platform", token=api_token)
backend = service.backend(backend_name) if backend_name else service.least_busy(operational=True, simulator=False)

isa_ansatz = transpile(ansatz, backend=backend, optimization_level=3)
isa_op     = qubit_op.apply_layout(isa_ansatz.layout)

with Session(backend=backend) as session:            # note: no `service=` kwarg
    estimator = EstimatorV2(mode=session)            # note: `mode=`, not `session=`
    def energy(theta):
        job = estimator.run([(isa_ansatz, isa_op, [theta])])
        return float(job.result()[0].data.evs[0])
    res = scipy.optimize.minimize(energy, x0=initial_point, method="COBYLA",
                                  options={"maxiter": 20 * ansatz.num_parameters})
```
Local path — fix the budget, seed, and convergence check:
```diff
- optimizer = COBYLA(maxiter=40)
+ n_params  = ansatz.num_parameters
+ optimizer = COBYLA(maxiter=max(200, 20 * n_params))   # COBYLA needs >= n+1 just to start
+ rng = np.random.default_rng(seed)
+ initial_point = rng.uniform(0, 2*np.pi, n_params)
- vqe = VQE(estimator, ansatz, optimizer, callback=callback)
+ vqe = VQE(estimator, ansatz, optimizer, callback=callback, initial_point=initial_point)
  result = vqe.compute_minimum_eigenvalue(qubit_op)
+ gap_mHa = abs(float(result.eigenvalue) - fci_energy) * 1000.0
+ converged = gap_mHa < 1.6                              # chemical accuracy
```
Same change at `qrl_optimizer.py:68-70` (currently `maxiter=15` for 12 parameters).

### H.1.9 — Never synthesize a result on failure (**A14, H1**)

`simulation.py:1168-1178` and `:1223-1233`:
```diff
  except Exception as e:
-     final_energy = fci_energy
-     history = [{"step": i, "energy": fci_energy + 1.62 * (0.88 ** i)} for i in range(41)]
+     logger.exception("VQE failed")
+     return {"status": "vqe_failed", "error": str(e), "history": history_so_far}
```
`simulation.py:1200-1220` — delete the sinusoidal noise synthesis entirely and return the real callback trace. If a noise study is wanted, use a real model:
```python
from qiskit_aer.noise import NoiseModel
from qiskit_ibm_runtime.fake_provider import FakeManilaV2
noise_model = NoiseModel.from_backend(FakeManilaV2())
```

### H.1.10 — Inverted fitness sign (**A20**)

`generator.py:622`:
```diff
- docking_fit = max(0, min(100, 100 - (scaled_docking - (-12.0)) * -10.0))
+ # -6 kcal/mol -> 0, -22 kcal/mol -> 100; stronger binding scores higher.
+ docking_fit = max(0.0, min(100.0, (abs(scaled_docking) - 6.0) / 16.0 * 100.0))
```
`generator.py:625` — clamp it like its siblings:
```diff
- admet_fit = 100 - violations * 25 - tox_penalty
+ admet_fit = max(0, min(100, 100 - violations * 25 - tox_penalty))
```
Regression test:
```python
@pytest.mark.parametrize("score,expected", [(-6.0, 0.0), (-14.0, 50.0), (-22.0, 100.0)])
def test_docking_fit_monotone(score, expected):
    assert docking_fit(score) == pytest.approx(expected, abs=1.0)
```

### H.1.11 — Docking unit error (**A7**)

`generator.py:343-352`:
```diff
+ HARTREE_TO_KCAL = 627.5094740631
+ COULOMB_K       = 332.0637        # kcal*Ang / (mol*e^2)
+ DIELECTRIC      = 4.0             # distance-independent protein interior approximation

  v_lj = D_e * ((r_e / dist)**12 - 2 * (r_e / dist)**6)
- v_coul = (achg * rchg) / (dist * 1.88973) if achg and rchg else 0.0
+ # both terms now in kcal/mol; note `is not None`, not truthiness — 0.0 charge is valid
+ v_coul = (COULOMB_K * achg * rchg) / (DIELECTRIC * dist) \
+          if (achg is not None and rchg is not None) else 0.0
  energy += v_lj + v_coul
```
`generator.py:549-550` — remove the clamp that manufactures picomolar binders:
```diff
- scaled_docking = -14.0 + 0.8 * (docking_score_raw - 2.0)
- scaled_docking = max(-22.0, min(-6.0, scaled_docking))
+ # Report the raw heuristic in its own units. Do NOT map it onto kcal/mol until
+ # it has been calibrated against a labelled set (PDBbind core / CASF-2016).
+ heuristic_score = docking_score_raw
```
Sanity test that would have caught the original defect:
```python
def test_docking_discriminates():
    tb = PRESET_POCKETS['tuberculosis']
    ethanol   = score("CCO", tb)
    isoniazid = score("c1cc(ccn1)C(=O)NN", tb)
    assert isoniazid < ethanol, "scorer cannot distinguish a drug from a solvent"
```
**Preferred alternative:** shell out to `smina` and delete the hand-rolled potential:
```python
subprocess.run(["smina", "-r", receptor_pdbqt, "-l", ligand_sdf,
                "--autobox_ligand", ref_sdf, "--seed", str(seed),
                "--exhaustiveness", "8", "-o", out_sdf, "--log", log], check=True)
```

### H.1.12 — Determinism (**D2**)

New file `seeds.py`:
```python
import os, random
import numpy as np
import torch

DEFAULT_SEED = int(os.getenv("QS_SEED", "1337"))

def set_global_seed(seed: int = DEFAULT_SEED) -> int:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    return seed

def rng(seed: int = DEFAULT_SEED) -> np.random.Generator:
    """Per-call generator. Prefer this over module-global np.random."""
    return np.random.default_rng(seed)
```
`app.py` — call once at startup and echo the seed in every response:
```python
from seeds import set_global_seed, DEFAULT_SEED
SEED = set_global_seed()
...
result["provenance"] = {
    "seed": SEED,
    "git_sha": subprocess.check_output(["git","rev-parse","--short","HEAD"]).decode().strip(),
    "config_hash": config_hash,
    "pocket_source": pocket_source,     # "alphafold" | "curated" — never "synthetic"
    "is_synthetic": False,
}
```
`simulation.py:935` — remove the global reseed inside `calculate_qpu_codesign`:
```diff
- np.random.seed(100 + i)
+ local_rng = np.random.default_rng(100 + i)   # then use local_rng.* below
```
Verification test:
```python
def test_run_is_deterministic():
    kw = dict(molecule_id='inh-q1', active_orbitals=4, ansatz_type='custom',
              noise_level=15.0, error_mitigation=True, mapper='parity',
              pathogen_name='Tuberculosis')
    set_global_seed(42); a = run_vqe_simulation(**kw)
    set_global_seed(42); b = run_vqe_simulation(**kw)
    for k in ('final_energy', 'fci_energy', 'binding_energy', 'free_energy'):
        assert a[k] == b[k], f"{k} is non-deterministic"
```

### H.1.13 — Remove the impossible mitigation coupling (**A2**)

`simulation.py:1309-1310`:
```diff
- if error_mitigation:
-     binding_energy -= 0.3
```
Delete unconditionally. A quantum error-mitigation toggle cannot move a classical Lennard-Jones score.

### H.1.14 — Input validation (**B6**)

`app.py` — replace manual `int()`/`float()` parsing with a validated model (`pydantic` is already a dependency):
```python
from pydantic import BaseModel, Field, ValidationError

class SimulateRequest(BaseModel):
    molecule_id: str = "inh-q1"
    active_orbitals: int = Field(4, ge=1, le=6)   # >6 -> 2^24 dense matrix -> OOM
    ansatz_type: str = "custom"
    noise_level: float = Field(15.0, ge=0.0, le=100.0)
    error_mitigation: bool = True
    mapper: str = "parity"
    pathogen_name: str = "unknown"

@app.route('/simulate', methods=['POST'])
def simulate():
    try:
        req = SimulateRequest(**(request.json or {}))
    except ValidationError as e:
        return jsonify({"status": "invalid_request", "errors": e.errors()}), 400
```

### H.1.15 — Licensing and provenance (**D1**)

```bash
curl -o LICENSE https://www.apache.org/licenses/LICENSE-2.0.txt
curl -o smiles_lstm/LICENSE https://raw.githubusercontent.com/MolecularAI/Reinvent/master/LICENSE
sha256sum pretrained.rnn.pth > pretrained.rnn.pth.sha256
touch smiles_lstm/__init__.py smiles_lstm/model/__init__.py smiles_lstm/utils/__init__.py
```
`NOTICE`:
```
QuantumShield
Copyright (c) 2026 <authors>

This product includes software derived from REINVENT
(https://github.com/MolecularAI/Reinvent), Copyright (c) AstraZeneca,
licensed under the Apache License, Version 2.0. Modified files:
smiles_lstm/model/{smiles_lstm,smiles_dataset,smiles_trainer,smiles_vocabulary}.py
smiles_lstm/utils/{load,misc}.py
```
`model_card.md` must state: architecture (3×512 LSTM, 512-d embedding, dropout 0.2, 57-token vocabulary, max length 256 — all verified by loading), training corpus and its citation, filters applied, split and split seed, epochs, final validation loss, and the SHA-256.

Then re-save as a `state_dict` to close the RCE (**B3**):
```python
torch.save({"state_dict": model.network.state_dict(),
            "vocabulary": model.vocabulary,
            "max_sequence_length": model.max_sequence_length,
            "network_params": model.network_params}, "pretrained.rnn.v2.pth")
# load with weights_only=True thereafter
```

### H.1.16 — Sampling hyperparameters (**D4, D6**)

`generator.py:462-473`:
```diff
- for step in range(128 - 1):
+ for step in range(self.max_sequence_length - 1):   # 256, from the checkpoint
      ...
-     probabilities = (logits / 0.8).softmax(dim=1)
+     probabilities = (logits / self.temperature).softmax(dim=1)
```
Make both constructor parameters with documented defaults, expose them in `config.yaml`, and wrap the whole loop:
```diff
+ model.eval()
+ with torch.no_grad():
      for step in ...
```

---

## H.2 — Phase 2 patches (weeks)

### H.2.1 — Replace invented property models (**A22, A24, A23**)

```python
# Synthetic accessibility — Ertl & Schuffenhauer (2009), ships with RDKit
import sys, os
from rdkit.Chem import RDConfig
sys.path.append(os.path.join(RDConfig.RDContribDir, 'SA_Score'))
import sascorer
sa = sascorer.calculateScore(mol)          # 1 (easy) .. 10 (hard)

# Structural alerts — replaces the unreachable element-count rules
from rdkit.Chem import FilterCatalog
params = FilterCatalog.FilterCatalogParams()
for c in (params.FilterCatalogs.PAINS,
          params.FilterCatalogs.BRENK,
          params.FilterCatalogs.NIH):
    params.AddCatalog(c)
CATALOG = FilterCatalog.FilterCatalog(params)     # build ONCE at import
alerts = [e.GetDescription() for e in CATALOG.GetMatches(mol)]

# Fsp3 — replaces the 1.6 Ang distance heuristic
from rdkit.Chem import Lipinski
fsp3 = Lipinski.FractionCSP3(mol)

# Lipinski: allow the one violation the rule actually permits
compliant = violations <= 1
```
Delete all three divergent `sa_score` formulas (`generator.py:663`, `:721`, `simulation.py:1916`, `qrl_optimizer.py:683`, `app.py:545`) and the `retro_steps` derivation. If retrosynthesis is wanted, use **AiZynthFinder**; otherwise remove the claim.

### H.2.2 — Real electronic-structure Hamiltonian (**A1**)

```python
# pip install qiskit-nature pyscf
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer
from qiskit_nature.second_q.mappers import ParityMapper
from qiskit_nature.second_q.circuit.library import HartreeFock, UCCSD

driver  = PySCFDriver(atom=xyz_string, basis="sto3g", charge=0, spin=0)
problem = driver.run()
problem = ActiveSpaceTransformer(num_electrons=4, num_spatial_orbitals=4).transform(problem)

mapper   = ParityMapper(num_particles=problem.num_particles)
qubit_op = mapper.map(problem.hamiltonian.second_q_op())

init  = HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper)
ansatz = UCCSD(problem.num_spatial_orbitals, problem.num_particles, mapper, initial_state=init)
```
Validate before claiming anything: run H₂ at 0.735 Å and compare against the published FCI/STO-3G value; assert the error is under 1.6 mHa. Only then move to larger fragments.

### H.2.3 — Real RL loop (**A3, A4**)

```python
# 1. Persist the agent outside the request handler
AGENT = QuantumRLAgent(num_qubits=8, lr=0.05)
if os.path.exists(CKPT):
    AGENT.theta = np.load(CKPT)

# 2. Sample from the policy — this is what makes the gradient valid
probs = AGENT.policy(state, mask)
action_idx = int(rng.choice(len(probs), p=probs))     # NOT argmax over lookahead rewards

# 3. Update per episode, over many episodes, and record the curve
for ep in range(n_episodes):
    traj = rollout(env, AGENT, rng)
    AGENT.update_policy(*traj)
    history.append({"episode": ep, "return": traj.total_reward, "seed": seed})
np.save(CKPT, AGENT.theta)
```
Fix the encoding absorption (**A32**) — interleave, so the re-upload is not algebraically merged:
```diff
  for i in range(8):
      qc.ry(np.clip(state[i], 0, 1) * np.pi, i)
+ for i in range(7):
+     qc.cx(i, i+1)              # non-commuting layer between encoding and variational
  for i in range(8):
      qc.ry(theta[i], i)
```
Then run the baselines that make the result mean something: random policy, greedy search, and a classical MLP with identical inputs, reward, and budget. Report all four with mean ± SD over ≥5 seeds.

### H.2.4 — Test suite and CI (**F1, F2**)

`pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = ["integration: hits live external APIs (deselect with -m 'not integration')"]
addopts = "-m 'not integration' --cov=src/quantumshield --cov-fail-under=70"
```
`.github/workflows/ci.yml`:
```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.10"}
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: ruff check .
      - run: mypy src/
      - run: pytest
      - run: pip-audit
      - uses: gitleaks/gitleaks-action@v2
  integration:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps: [...]           # weekly: catches external API drift like C2 and C5
```
Replace every `print()` with `logging`, and replace the 65 broad handlers with specific exceptions. The rule that prevents recurrence: **never substitute a value in an `except` block.**

---

## H.3 — Fix-to-score map

Each row states what the fix unlocks. Score arithmetic is in `audit_summary.md` §9.

| Fix group | Items | Dimensions moved |
|---|---|---|
| H.0.1–H.0.2 | Secrets, debug server | Software engineering |
| H.0.3–H.0.6 | Lead polishing, tool names, success literals, synthetic labels | **Scientific validity**, documentation |
| H.0.7, H.1.12, H.1.15 | Version control, seeding, license + model card | **Reproducibility** |
| H.1.1–H.1.7 | Seven verified crashes and dead paths | Code quality |
| H.1.8, H.1.10, H.1.11 | Optimizer budget, fitness sign, unit error | **Scientific validity**, code quality |
| H.1.14, H.2.4 | Validation, tests, CI, logging | Software engineering, maintainability |
| H.2.1 | Published property models | Scientific validity |
| H.2.2–H.2.3 | Real Hamiltonian, real RL loop + baselines | **Scientific validity**, novelty |
