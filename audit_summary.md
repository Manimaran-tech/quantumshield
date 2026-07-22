# audit_summary.md — Research Audit Summary

**Project:** QuantumShield — "Quantum-Powered Antibiotic Discovery against Drug-Resistant Tuberculosis"
**Audit date:** 2026-07-22
**Auditor role:** senior research mentor (computational biology / cheminformatics / ML / quantum computing), reviewing for publication readiness
**Scope:** in-silico, simulation-only, defensive/educational computational research
**Companion documents:** [`fix.md`](fix.md) (prioritized defects) · [`research_improvements.md`](research_improvements.md) (path to publication)
**Prior audit preserved as:** `fix.2026-07-19.bak.md`, `research_improvements.2026-07-19.bak.md`

---

## Method and evidence standard

Roughly 7,650 lines of Python across `app.py` (945), `generator.py` (913), `simulation.py` (1,977), `qrl_optimizer.py` (2,172), `smiles_lstm/` (4 modules), `utils.py`, `real_benchmark.py`, `scratch_huckel_test.py`, and 9 test files were read in full, alongside the frontend (`src/App.tsx`, 9,035 lines), the four Markdown design documents, and all configuration.

Unlike the 2026-07-19 review, this audit **executed the code** in the project's own `venv` (Python 3.10.11, `qiskit 2.4.2`, `qiskit-algorithms 0.4.0`, `qiskit-ibm-runtime 0.47.0`, `torch 2.12.1+cpu`, `rdkit 2026.3.3`) and **issued live HTTP requests** to all seven external services. Findings therefore carry evidence tags:

- **[EXECUTED]** — the code was run and the output observed.
- **[LIVE-API]** — the actual endpoint was called.
- **[STATIC]** — read, not run.
- **[UNVERIFIED]** — stated explicitly wherever it applies.

Three items the previous audit could not resolve are now settled: the qiskit V1/V2 primitive question (**no mismatch** — VQE genuinely runs), the IBM Runtime path (**broken three ways** — never executed), and the reproducibility question (**measurably non-deterministic**).

---

## 1. Executive summary

QuantumShield is a substantial, largely working piece of software wrapped in claims that its own code does not support.

**What is real:** a functioning Flask + React application; a genuine pretrained SMILES LSTM (verified by loading the checkpoint — 3 layers, 512 units, 512-d embedding, self-consistent 57-token vocabulary); correct use of published RDKit methods (Crippen logP, TPSA, QED, Lipinski counts, ETKDG/MMFF94 embedding, MCS); live, working integrations with AlphaFold, UniProt, Open Targets, openFDA, ChEMBL, and CMS NADAC; a real Qiskit VQE invocation; and one block of genuinely correct superconducting-qubit physics.

**What is not real:** the science that the project is named for. The verified findings, in descending order of consequence:

1. **The qubit Hamiltonian contains no molecular information.** [EXECUTED] Five different molecules — water, H₂, pyridine, and two drug candidates — produce **identical non-identity Pauli coefficients**. The only molecule-dependent term is the identity coefficient, a global energy offset that commutes with everything and therefore cannot influence the eigenvector, the variational landscape, or the optimizer. The VQE solves one fixed 6-qubit toy problem for every molecule the product will ever process.
2. **The reported binding energy never touches the quantum result.** It is an affine remap of a classical heuristic, clamped to [−22, −6] kcal/mol, with a 0.3 kcal/mol adjustment applied by a UI error-mitigation toggle — a physically impossible coupling.
3. **The reinforcement-learning agent never learns.** Weights are re-randomized on every HTTP request, updated exactly once *after* the rollout ends, used only to draw a picture, and discarded. Nothing persists.
4. **The RL gradient estimates nothing.** Actions are chosen by greedy reward lookahead rather than sampled from the policy, so the REINFORCE estimator is invalid. When ≤3 actions are valid, the quantum circuit has literally zero influence on the choice.
5. **A post-hoc step edits the output when it loses to the baseline.** `# Lead Polishing: ensure the QRL candidate beats the reference drug's free energy` fires only on failure, applies hardcoded chemist edits, and returns the result as the agent's recommendation. This is the single most serious research-integrity finding.
6. **The docking score cannot discriminate.** [EXECUTED] Ethanol (MW 46) scores **better** against the InhA pocket than isoniazid, and is reported at Kd = 5.8 pM. The dynamic range across a 10× mass span is 0.9 kcal/mol. Root cause: Hartree and kcal·mol⁻¹ summed directly (627× apart), plus a clamp that forces every molecule into "picomolar binder" territory.
7. **The accuracy benchmark cannot fail.** `PASSED`, `[SUCCESS]`, and `[PROVED]` are string literals inside f-strings, printed over a metric that is structurally pinned near 100 % because the VQE failure path sets `final_energy = fci_energy`, and because "FCI" is exact diagonalization of the same fabricated operator.
8. **Software that never runs is named in the output:** AutoDock Vina, GROMACS/OpenMM, P2Rank, Qiskit Metal, "100 ns trajectories", "1000 candidates", "CAS(4,4)", "Genetic Algorithm". None are dependencies; several are invented provenance for hash-of-string values.
9. **Fabricated biology reaches the user:** binding pockets generated from `random.Random(sum(ord(c) for c in pathogen_name))`; resistance panels listing SARS-CoV-2 **spike** variants against an **Mpro** target; `InhA S315T`, which is a *katG* mutation; and mutant labels like `"HIS110 to VAL"` derived from an array index plus 108.
10. **Synthetic data is labelled as measurement.** `/api/validation/wetlab` returns `np.random.normal` draws under the key `measured_binding`, on a curve that is Kd-invariant by construction (always 9/23/50/75/91 %). Given the biomedical framing, this is the highest-risk mislabel for a non-expert reader.

**Security and reproducibility compound the problem.** Live API keys sit in plaintext on disk (one annotated "compromised"); the server runs `debug=True` on `0.0.0.0`, exposing the Werkzeug RCE console; the 25 MB model checkpoint is loaded with `weights_only=False` from an undocumented source; `requirements.txt` is untracked; `pytest` is not installed; five of nine test files contain zero assertions; and the repository has **no LICENSE** despite vendoring Apache-2.0 REINVENT-derived code.

**Bottom line:** the gap between this project and a publishable one is almost entirely a **claims** gap, not a **code** gap. That is unusually good news — claims are the cheapest thing in a project to fix.

---

## 2. Strengths

These are genuine, verified, and worth protecting through any remediation:

1. **System integration is real and non-trivial.** Seven live biomedical APIs, an AlphaFold structure-fetch path with secondary-accession resolution and parallel candidate probing, a React frontend, and a Flask backend — working end to end. This is more integration work than most student projects attempt.
2. **The generative model is genuine.** Verified by loading: `SmilesLSTM`, 3 × 512 LSTM, 512-d embedding, dropout 0.2, 57-token vocabulary consistent with the checkpoint's output layer, `max_sequence_length=256`, saved in eval mode.
3. **RDKit is used correctly where it is used.** Crippen `MolLogP`, `TPSA`, `Lipinski` counts, `QED.qed` (Bickerton), `CalcMolFormula`, ETKDG + MMFF94 embedding, `rdFMCS`. The Morgan fingerprint call in `app.py:730` uses the current `rdFingerprintGenerator` API rather than the deprecated one — a small sign of care.
4. **The VQE call is real.** [EXECUTED] `qiskit-algorithms 0.4.0` accepts the V2 `StatevectorEstimator`; no silent fallback occurs. The machinery works — it is pointed at the wrong operator and given an insufficient optimizer budget.
5. **The QPU co-design module is scientifically sound.** `simulation.py:858-1031` uses correct constants (Φ₀ = 2.067833848 × 10⁻¹⁵ Wb, h, e, ε_r,Si = 11.7) and correct transmon relations: `E_J = I_cΦ₀/2π`, `E_C = e²/2C`, `f_q = √(8E_J E_C) − E_C`, `α ≈ −E_C`, half-wave CPW `f_r = v/2L`. **This is the most defensible block in the repository and is currently buried** behind three layers of fabricated chemistry.
6. **The parameter-shift gradient implementation is real.** 65 statevector evaluations per timestep, correctly structured. The infrastructure for genuine quantum RL exists; only the surrounding loop is broken.
7. **No fabricated bibliography.** The eight references in `ppt.md` were spot-checked and are genuine — Lovering, Bikker & Humblet (2009) *J. Med. Chem.* 52(21):6752-6756 is cited correctly. Hardcoded `P08668` is genuinely *Hantaan virus* (reviewed Swiss-Prot) [LIVE-API]. Exactly one citation-shaped claim ("Wang et al. inspired scoring function") cannot be verified.
8. **`.env` was never committed.** Verified with `git log --all -- .env`. The `.gitignore` is correct. The key exposure is local, not historical.
9. **Prior self-audit exists.** A thorough static review was performed three days before this one and several findings were partially acted on (the `qrl_optimizer` PubChem resolver was fixed; hardcoded overrides were removed, leaving stray `pass` statements). The instinct to audit is present and should be reinforced.

---

## 3. Weaknesses

1. **Fabrication is systemic, not incidental.** It appears in every layer — Hamiltonian, docking, ADMET, toxicity, SA score, retrosynthesis, pocket detection, MD, mutation panels, cost model, confidence metric, and benchmark verdicts — and follows a consistent pattern: a plausible number is manufactured so the UI never shows an error.
2. **The failure-handling philosophy inverts scientific practice.** 65 broad exception handlers, many of which replace a failed computation with an invented value. A comment in `generator.py:259` states the goal plainly: *"This ensures the frontend ALWAYS receives coordinates and never crashes."* UI robustness was consistently chosen over correctness, which converts every silent failure into a fabricated result.
3. **No evaluation methodology of any kind.** No train/test split (the test dataloader is constructed and never used), no held-out set, no cross-validation, no baseline, no ablation, no statistical test, no error bars, n = 1. Novelty is never checked against the training corpus — and cannot be, since that corpus is undocumented.
4. **Nothing is reproducible.** [EXECUTED] Two identical calls returned binding energies of −17.04 and −16.92 kcal/mol. One seeding call exists in the entire repository, and it is a *global* reseed inside an unrelated function, coupling every downstream RNG consumer to a UI slider.
5. **Critical paths are dead code.** The AlphaFold pocket path raises `UnboundLocalError` on every call (swallowed); the IBM hardware path fails three ways under the installed SDK (swallowed); `app.py`'s PubChem resolver always returns `None` (silent); the EMA endpoint 404s (silent). All four degrade to fabricated substitutes with no signal.
6. **Duplication with divergence.** The same rescale formula appears four times with two different clamps, so the same quantity is reported on two scales in one project. `fetch_pubchem_smiles` exists twice, and only one copy was fixed. The toxicity block is duplicated four times.
7. **Security posture is unsuitable for any shared environment.** Plaintext keys, `debug=True` on `0.0.0.0`, wide-open CORS, no authentication, no rate limiting, no input validation, `weights_only=False` pickle loading, unbounded global state under a threaded server.
8. **Documentation actively misleads.** `README.md` is an untouched Google AI Studio scaffold describing a different project. Docstrings assert behaviours the code does not implement ("Zero hardcoded templates", "diagonalizing a Hückel Hamiltonian", "No hardcoded pathogen name logic") — each contradicted a few lines away.
9. **No engineering infrastructure.** No CI, no packaging, no linting, no type checking, no logging, no license, no `__init__.py` in either subpackage, and a circular import worked around by importing inside a per-candidate loop.

---

## 4. Critical blockers

Ordered by the severity of the consequence if the project were submitted as-is.

| # | Blocker | Consequence if unaddressed |
|---|---|---|
| 1 | **"Lead polishing" adjusts results only when they lose to the baseline** (`qrl_optimizer.py:2050-2084`) | If found post-publication, this is treated as fabricated results — the most serious outcome available |
| 2 | **Molecule-independent Hamiltonian** (`simulation.py:199-242`) [EXECUTED] | The project's central quantum claim is false; every VQE-derived number is meaningless |
| 3 | **Agent never learns; gradient is invalid** (`qrl_optimizer.py:133/1920/1946-1968`) | Every "training", "convergence", and "optimization" claim is unsupportable |
| 4 | **Non-discriminative docking; ethanol as a picomolar InhA binder** (`generator.py:272-379`) [EXECUTED] | Every affinity, Kd, ΔG, and ranking in the paper is invalid |
| 5 | **Benchmarks that cannot fail** (`test_accuracy_validation.py:144,148`) | The stated ">95 % accuracy" is a printed literal; retracting it is mandatory |
| 6 | **Synthetic data labelled `measured_binding`** (`simulation.py:1899-1910`) | Highest-risk mislabel for a lay or clinical reader, given the biomedical framing |
| 7 | **False tool attribution** (Vina, GROMACS/OpenMM, P2Rank, Qiskit Metal) | Naming software you did not run is treated as misrepresentation of methods |
| 8 | **Fabricated resistance biology** (spike variants vs an Mpro target; `InhA S315T`) | Domain reviewers will catch this immediately; it undermines all remaining credibility |
| 9 | **Live keys on disk + `debug=True` on `0.0.0.0`** | Remote code execution; credential compromise |
| 10 | **No LICENSE despite vendoring Apache-2.0 REINVENT code** | Blocks code release and most journal artifact policies outright |
| 11 | **Not reproducible; `requirements.txt` untracked; `pytest` missing** | No reviewer can verify any number |

---

## 5. Numerical scores

Scored against the standard for a peer-reviewed computational-science publication. Each is justified by verified evidence, not impression.

Scores are stated **as measured on 2026-07-22**. The two target columns are projections after the remediation plans in §9 (Lane B) and §10 (Lane A) — they are goals, not claims about the current codebase. Nothing in the current column moves until the corresponding code changes and is re-verified against the protocol in §9.6.

| Dimension | Current | Lane B target (§9) | Lane A target (§10) |
|---|---|---|---|
| Software engineering | **3.0 / 10** | 7.5 | 8.0 |
| Scientific validity | **1.5 / 10** | 6.5 | 9.5 |
| Reproducibility | **1.5 / 10** | 8.5 | 9.5 |
| Novelty | **3.0 / 10** | 5.0 | 8.5 |
| Documentation | **2.5 / 10** | 8.0 | 9.0 |
| Code quality | **3.0 / 10** | 7.5 | 8.5 |
| Maintainability | **2.5 / 10** | 7.0 | 7.5 |
| **Overall research readiness** | **2.0 / 10** | **7.2** | **9.1** |

Lane B is ~5 weeks and needs no new science. Lane A is ~9 months on top of Lane B and requires CASSCF/active-space expertise the project does not currently have. They are sequential, not alternatives — Lane A assumes Lane B's integrity, reproducibility, and testing work is already done.

### Justifications

**Software engineering — 3.0.** *Credit:* a working full-stack application; real API integration with parallel candidate probing and secondary-accession fallback; a functioning build. *Against:* no packaging, no CI, no logging, no linting, no type checking; four monolithic modules (2,172 / 1,977 / 945 / 913 lines); a circular import worked around inside a per-candidate loop; missing `__init__.py`; 65 broad exception handlers; unbounded global state mutated under `threaded=True`; wide-open CORS with no authentication or validation. The system runs, which is worth something; almost none of the practices that make a system maintainable are present.

**Scientific validity — 1.5.** The four central claims — VQE quantum chemistry, quantum RL, docking affinity, and ADMET — are each independently invalid, and three of the four were disproved by execution rather than inference. The single point above zero reflects the genuinely correct components: RDKit descriptor usage, the correct Kd relation, and the transmon physics block. It cannot go higher while a molecule-independent operator is presented as a molecular Hamiltonian and a result-adjustment step fires on baseline failure.

**Reproducibility — 1.5.** [EXECUTED] identical inputs give different outputs. One global seed call exists, in the wrong place. `requirements.txt` is untracked; `transformers` is imported but unlisted; `pytest` is listed but uninstalled; `dist/` is gitignored but served; four core science files have uncommitted modifications; the model checkpoint has no documented corpus, no hyperparameters, and no checksum; sampling temperature and sequence length are hardcoded and undisclosed (and the length is half what the checkpoint was trained for). The half-point reflects that dependency *versions* are at least pinned in the untracked file.

**Novelty — 3.0.** The *combination* — LSTM generation + RL optimization + VQE + hardware co-design + live database resolution, in one interactive tool — is a genuinely uncommon integration, and the QPU co-design module is a small original contribution. But every individual component is either standard (REINVENT-style LSTM, hardware-efficient VQE, REINFORCE) or non-functional. Novelty of *claimed* results is zero, because the results are not produced by the claimed methods.

**Documentation — 2.5.** *Credit:* `completeworkflow.md` and `ppt.md` are substantial, contain real architecture diagrams, and cite genuine references — no fabricated bibliography was found, which is a meaningful positive. *Against:* `README.md` is the wrong project entirely; no LICENSE; no model card; no data card; no API reference; no limitations section; and several docstrings assert the opposite of what the adjacent code does.

**Code quality — 3.0.** *Credit:* generally readable, consistently named, reasonably commented; correct RDKit and Qiskit API usage including current (non-deprecated) calls. *Against:* verified crashes (`TypeError` on the default `/simulate` path; `UnboundLocalError` in three handlers; potential `NameError` in `/api/validation/run`; empty SMILES accepted as drug candidates); an inverted sign in the fitness function; a Hartree/kcal·mol⁻¹ unit error; silent in-place mutation of caller data; an O(n⁴) hot function called three times per simulation; dead code in every module.

**Maintainability — 2.5.** The duplication is the dominant factor: the same rescale in four places with two different clamps; `fetch_pubchem_smiles` in two places with only one fixed; the toxicity block four times; the pathogen-key mapping twice, substring-based and mis-firing. A single-threshold change requires four coordinated edits. Combined with zero effective test coverage and no CI, any change is high-risk.

**Overall research readiness — 2.0.** Weighted toward scientific validity and reproducibility, as a research audit must be. The engineering substrate is real and the remediation path is clear and mostly cheap, which is why this is 2.0 rather than 1.0. It is not 3.0 because the headline claims are not merely weakly supported — they are contradicted by the code's own execution.

---

## 6. Research-readiness verdict by venue

| Context | Now | After Lane B (§9) | After Lane A (§10) |
|---|---|---|---|
| Undergraduate research / final-year project | **Borderline** — strong engineering, claims would not survive a viva | **Strong** | Well beyond |
| Master's thesis | **No** | **Yes**, with a real evaluation chapter and limitations section | Well beyond |
| PhD-level prototype | **No** | No | **Yes** |
| Software/tools venue (JOSS, JOSE, SoftwareX) | **No** — no license, no tests, no README | **Yes — the natural fit** | Yes, as a companion artifact |
| Conference (quantum / ML / cheminformatics) | **No** | Systems/demo track, or a poster | **Yes**, full paper |
| Journal publication (methods) | **No** | No | **Yes** — quantum-chemistry methods venue |

Note the split in the last two rows: Lane B and Lane A produce **two separate outputs**, not one stronger one. See §10.4.

---

## 7. Recommended next steps

### Today — under a day, mostly deletions
1. **Revoke and rotate all three API keys.** Treat the Gemini key annotated "compromised" as public. Remove the key text from the `.env` comment; replace the five `scratch/` literals with `os.getenv`; add `scratch/` to `.gitignore`.
2. **`debug=False`; bind `127.0.0.1`.**
3. **Delete `# Lead Polishing`** (`qrl_optimizer.py:2050-2084`). This is the highest-integrity-risk item and takes one commit.
4. **Delete every false tool attribution** — Vina, GROMACS/OpenMM, P2Rank, Qiskit Metal, "100ns", "1000 candidates", "CAS(4,4)", "Genetic Algorithm".
5. **Delete the `PASSED` / `[SUCCESS]` / `[PROVED]` literals.**
6. **Rename `measured_binding` → `synthetic_binding`** and add a visible "SYNTHETIC — NOT EXPERIMENTAL" banner.
7. **`git add requirements.txt`; commit the working tree.**

### This week
8. Fix the four verified crashes: empty-SMILES acceptance, `pathogen_name=None`, the three `UnboundLocalError` handlers, the possibly-unbound `disease_info`.
9. Fix `app.py`'s dead PubChem resolver — delete it and import the working copy from `qrl_optimizer`.
10. Remove or migrate the IBM Runtime path and the 404 EMA endpoint.
11. Add `set_global_seed()`; echo seed + config + git SHA in every response.
12. Install `pytest`; add golden-value regression tests pinning the isoniazid docking score, the fitness-sign endpoints, empty-SMILES rejection, and the `/simulate` default path.
13. Fix the inverted fitness sign and the Hartree/kcal·mol⁻¹ unit error.
14. Add `LICENSE` + REINVENT `NOTICE`; write a real `README.md` with a **Scope and Limitations** section placed early.

### This month — finish Lane B (§9, `research_improvements.md` §0)
Complete the honest-labelling pass, add the test suite and CI, swap in RDKit `sascorer` and `FilterCatalog`, write the model card and data cards, publish as a tools/education contribution. **7.2 / 10.** This is a real, defensible contribution that the existing code already supports.

### Then, if the ambition is a methods paper — Lane A (§10, `research_improvements.md` §10)
~9 months. Reframe from "quantum binding affinity" to KatG heme active-space electronic structure; Qiskit Nature + PySCF; AVAS active-space selection; ADAPT-VQE; DMRG baselines; fault-tolerant resource estimates. **9.1 / 10.** Lanes are **sequential, not alternatives** — Lane A assumes Lane B's integrity and reproducibility work is done. Resolve the two blockers in §10.5 (WSL2/Linux for PySCF; a CASSCF-experienced collaborator) before committing to it.

### The highest-value single experiment
Calibrate and validate the **QPU co-design module** (`simulation.py:858-1031`) against published IBM device parameters — predicted vs reported qubit frequency, anharmonicity, T₁/T₂, and gate error. It is the one component whose physics is already correct, it is small and self-contained, and it is the most likely thing in this repository to become a genuine, publishable result. Right now it is buried underneath three layers of fabricated chemistry.

---

## 8. A note on framing

The most valuable thing this project could publish is an honest account of what it built and what it found — including that a molecule-independent model Hamiltonian produces no useful signal, that a quantum policy with an absorbed encoding cannot outperform a classical one, and that a simplified LJ docking heuristic cannot distinguish ethanol from a real inhibitor.

Those are real findings. They are also exactly the findings this codebase currently conceals behind fabricated numbers. A project that says precisely what it does — *an integrated, open-source pipeline and UI for quantum-inspired molecular design, with illustrative scoring and a validated hardware co-design model* — is defensible, useful, and publishable. A project that claims validated quantum drug discovery is neither.

The engineering here is real. The path forward is mostly subtraction.

---

## 9. Path to 7.0 / 10 — costed plan

**Target: overall research readiness 7.0 / 10** — the level at which this is a defensible master's-thesis artifact and a credible submission to a software/tools venue (JOSS, JOSE, SoftwareX) or a systems/demo track.

This is reachable **without** solving quantum chemistry. The largest single gain comes from deletions, not new science: five of the eight dimensions are held down by claims and missing infrastructure rather than by hard research problems.

Patch-level instructions for every item are in [`fix.md` Part H](fix.md).

### 9.1 Score arithmetic

Overall readiness is weighted toward the dimensions a research reviewer actually checks: scientific validity ×0.30, reproducibility ×0.25, documentation ×0.15, code quality ×0.10, software engineering ×0.10, maintainability ×0.05, novelty ×0.05.

| Dimension | Now | After P0 | After P1 | After P2 | Weight |
|---|---|---|---|---|---|
| Scientific validity | 1.5 | 4.0 | 5.5 | 6.5 | 0.30 |
| Reproducibility | 1.5 | 3.0 | 7.5 | 8.5 | 0.25 |
| Documentation | 2.5 | 4.5 | 7.0 | 8.0 | 0.15 |
| Code quality | 3.0 | 3.5 | 6.5 | 7.5 | 0.10 |
| Software engineering | 3.0 | 4.0 | 6.0 | 7.5 | 0.10 |
| Maintainability | 2.5 | 2.5 | 5.0 | 7.0 | 0.05 |
| Novelty | 3.0 | 3.0 | 3.5 | 5.0 | 0.05 |
| **Weighted overall** | **2.0** | **3.8** | **6.3** | **7.2** | |

Phase 2 clears the 7.0 bar. Phase 1 alone does not — reproducibility and documentation reach target, but scientific validity stays at 5.5 because the property models are still invented.

### 9.2 Phase 0 — Integrity pass · ~1 day · **2.0 → 3.8**

Almost entirely deletion. No new science, no new dependencies.

| Action | `fix.md` | Moves |
|---|---|---|
| Revoke/rotate three API keys; `os.getenv` in `scratch/` | H.0.1 | SW eng 3.0→4.0 |
| `debug=False`, bind loopback | H.0.2 | SW eng |
| Delete "Lead Polishing" | H.0.3 | **Sci 1.5→4.0** |
| Delete Vina / GROMACS / P2Rank / Qiskit Metal / "1000 candidates" / "CAS(4,4)" / "100ns" | H.0.4 | **Sci**, Doc |
| Delete `PASSED` / `[SUCCESS]` / `[PROVED]` literals | H.0.5 | **Sci** |
| Rename `measured_binding` → `synthetic_binding` + banner | H.0.6 | **Sci**, Doc 2.5→4.5 |
| `git add requirements.txt`; commit working tree | H.0.7 | Repro 1.5→3.0 |

**Why scientific validity jumps 2.5 points for zero new science:** the score is dominated by *unsupported claims*, not by absent capability. Removing a false tool attribution converts a fabrication into an honest limitation. Four of the eleven critical blockers close here.

### 9.3 Phase 1 — Correctness and reproducibility · ~1 week · **3.8 → 6.3**

| Action | `fix.md` | Moves |
|---|---|---|
| Fix 7 verified crashes/dead paths (empty SMILES, `pathogen_name=None`, 3× `UnboundLocalError`, `disease_info`, dead AlphaFold path) | H.1.1–H.1.5 | **Code 3.0→6.5** |
| Never fabricate a pocket; `status: "unresolved"`; reject `P12345` | H.1.6 | **Sci** |
| Single PubChem implementation + contract test | H.1.7 | Code, SW eng |
| Remove or migrate IBM path; optimizer budget `20·n_params`; seeded `initial_point`; real convergence check | H.1.8 | **Sci 4.0→5.5** |
| Return `status: "vqe_failed"`; delete synthetic convergence curve and sinusoidal noise | H.1.9 | **Sci** |
| Fix inverted fitness sign; fix Hartree/kcal·mol⁻¹ unit error; delete `error_mitigation -= 0.3` | H.1.10, H.1.11, H.1.13 | **Sci**, Code |
| `seeds.py`; per-call `default_rng`; `provenance` block in every response | H.1.12 | **Repro 3.0→7.5** |
| `pydantic` request validation | H.1.14 | SW eng 4.0→6.0 |
| `LICENSE` + `NOTICE` + `model_card.md` + SHA-256 + `__init__.py`; `state_dict` re-save | H.1.15 | **Doc 4.5→7.0**, Repro |
| Expose sampling temperature and length; `model.eval()`; `torch.no_grad()` | H.1.16 | Repro, Code |
| Real `README.md` with an early Scope and Limitations section | §5 of `research_improvements.md` | **Doc** |
| ~10 golden-value regression tests (isoniazid docking, fitness endpoints, empty SMILES, determinism) | H.1.1, H.1.10–H.1.12 | Code, Maint 2.5→5.0 |

**Gate:** the determinism test in H.1.12 must pass twice in a row. Until identical inputs give identical outputs, reproducibility does not move regardless of what else is done.

### 9.4 Phase 2 — Published methods and infrastructure · ~3 weeks · **6.3 → 7.2** ✅

| Action | `fix.md` | Moves |
|---|---|---|
| RDKit `sascorer` (Ertl), `FilterCatalog` (PAINS/Brenk/NIH), `Lipinski.FractionCSP3`; delete 3 divergent SA formulas and the `retro_steps` claim; allow Ro5's one permitted violation | H.2.1 | **Sci 5.5→6.5** |
| `pytest` suite ≥70 % coverage on `chem/`/`quantum/`/`rl/`; mock all network; `@pytest.mark.integration` excluded by default | H.2.4 | **Code 6.5→7.5**, Maint 5.0→7.0 |
| GitHub Actions: `ruff` → `mypy` → `pytest` → `pip-audit` → `gitleaks`; weekly integration job | H.2.4 | **SW eng 6.0→7.5** |
| `logging` replaces 65 `print()`; specific exceptions; no value substitution in `except` | H.2.4 | Code, Maint |
| Deduplicate: one rescale, one pathogen map, one toxicity block, one PubChem fn | F3 | **Maint** |
| `model_card.md` + `data_card.md` per source; OpenAPI reference; `Dockerfile` | §3, §5 | **Doc 7.0→8.0**, Repro 7.5→8.5 |
| Calibrate the transmon module against published IBM device parameters (predicted vs reported f_q, α, T₁/T₂, gate error) | §8.13 | **Novelty 3.5→5.0**, Sci |

**The transmon calibration is the single highest value-per-hour research item in the plan.** The physics at `simulation.py:858-1031` is already correct — correct Φ₀, correct `f_q = √(8E_J E_C) − E_C`, correct CPW resonator relation. Only four fudge factors need calibrating. It is small, self-contained, genuinely novel, and it is the one component that can carry a real result. Currently it is buried under three layers of fabricated chemistry.

### 9.5 What 7.2 does and does not buy

**Unlocked:**
- Strong undergraduate capstone or defensible master's thesis
- JOSS / JOSE / SoftwareX submission
- Conference systems or demo track
- Public code release (license, provenance, and security are all clear)

**Still not unlocked — these require Lane A (§10):**
- Any claim of quantum advantage — needs a real Hamiltonian and a strong classical baseline
- Any binding affinity reported in kcal/mol — needs smina/Vina benchmarked on CASF-2016
- A quantum-chemistry or cheminformatics methods journal

Scientific validity is capped near 6.5 until the Hamiltonian is real, because a model operator cannot support a quantum-chemistry claim no matter how well the surrounding software is engineered. That cap is why Lane B targets 7.2 rather than 8.0+, and why it routes the project toward a tools/systems venue where the contribution is honest and the engineering is the point.

### 9.6 Verification protocol

Re-score only against re-run evidence. For each phase, the following must be captured and attached to the commit:

1. `pytest -m "not integration"` green, coverage report attached.
2. The determinism test passing twice, with the two identical payloads diffed.
3. `python -c "..."` transcript showing the Hamiltonian check — if the operator is still molecule-independent, scientific validity does not move past 6.5 regardless of other work.
4. The isoniazid-beats-ethanol docking assertion passing.
5. `gitleaks detect` clean on working tree and full history.
6. A `run_manifest.json` for one full pipeline execution: git SHA, seed, config hash, package versions, hardware.

Without those six artifacts, a revised score is an assertion rather than a measurement — which is the specific failure mode this audit exists to correct.

---

## 10. Path to 9.1 / 10 — Lane A, the quantum-chemistry methods paper

Full plan with code sketches, validation gates, and a bibliography: [`research_improvements.md` §10](research_improvements.md). Summary follows.

**Prerequisite: Lane B must be complete.** Lane A assumes seeding, testing, CI, licensing, and the integrity pass are already done. Building real quantum chemistry on top of an unseeded, untested, unlicensed codebase produces results nobody can verify.

### 10.1 The reframe is the load-bearing change, not the Hamiltonian

Fixing `get_molecular_hamiltonian` is necessary and insufficient. Even a perfect VQE on a drug fragment gives a **gas-phase active-space electronic energy**, which addresses a small part of ΔE_interaction and says nothing about solvation, conformational entropy, or desolvation — terms that routinely dominate binding free energy. The project would have replaced a fabricated number with an accurate number that answers a different question. That is still an invalid inference chain, and it is the first thing a domain referee tests.

**The fix is to change the question to one quantum chemistry actually answers**, and tuberculosis supplies an unusually good one:

Isoniazid is a prodrug. **KatG** — a catalase-peroxidase with a **heme b (Fe-protoporphyrin IX)** cofactor — oxidizes it to the isonicotinoyl radical, which couples to NAD⁺ to form the INH-NAD adduct that actually inhibits InhA. The dominant clinical resistance mutation, ***katG* S315T**, impairs the **activation** step, not the binding step.

Fe-porphyrin is the canonical strongly-correlated system: near-degenerate 3d orbitals, close-lying spin states, heavy static correlation. Single-reference methods including CCSD(T) are unreliable there **by construction** — which is precisely the regime where quantum advantage is seriously argued, and the same reasoning behind the FeMoco (Reiher et al. 2017) and cytochrome P450 (Goings et al. 2022) resource-estimate studies.

**Working title:** *Active-space electronic structure of the M. tuberculosis KatG heme centre along the isoniazid activation coordinate: ADAPT-VQE benchmarked against CASSCF, NEVPT2, and DMRG, with fault-tolerant resource estimates.*

That is a real methods paper. "Quantum-computed binding affinity" is not, at any level of code quality.

### 10.2 The seven technical changes

| # | Change | Replaces |
|---|---|---|
| 1 | PySCF driver → `ElectronicStructureProblem`, with a basis-set convergence ladder | The molecule-independent toy operator |
| 2 | **AVAS** or natural-orbital-occupation active-space selection, with a sensitivity study | An `active_orbitals` UI slider |
| 3 | `ParityMapper` two-qubit reduction + **Z₂ tapering** — CAS(16,16) goes 32 → 24–26 qubits | `mapper_type` subtracting 2 from a qubit count |
| 4 | `HartreeFock` + `UCCSD`, then **ADAPT-VQE** above CAS(6,6) | `TwoLocal(['ry','rz'],['cx'])`, which conserves nothing |
| 5 | SLSQP + analytic parameter-shift gradients, `maxiter ≥ 30·n_params` | COBYLA with 40 iterations for 64 parameters |
| 6 | Real `NoiseModel.from_backend` + ZNE + M3 readout mitigation | A hand-tuned sinusoid |
| 7 | OpenFermion double-factorization **resource estimates** (Toffoli + logical qubits) | Nothing — this is new, and it is what makes it a methods paper |

### 10.3 Three things that decide whether it succeeds

1. **The validation ladder is a set of hard gates**, not a checklist: H₂ → LiH → BeH₂ → **N₂ triple-bond breaking** → H₂O stretch → Fe-porphyrin vs DMRG → KatG WT → S315T. Rung 4 is the separator — a method that cannot break N₂ correctly cannot speak about a heme centre, and referees know it. Every rung asserted in CI against a published value with its DOI.
2. **DMRG is the real competitor, not CCSD(T).** `block2`, with a bond-dimension convergence study. A quantum-advantage claim measured against an unconverged DMRG calculation will not survive review.
3. **Lee et al. (2023), *PRX Quantum* 4, 020329** — "Evaluating the evidence for exponential quantum advantage in ground-state quantum chemistry" — must be engaged directly in the Discussion, including a computed HF/CASSCF **overlap-scaling** analysis for your active space. Ignoring it reads as unfamiliarity with the field.

**The expected outcome is that DMRG wins at every tractable active-space size.** This is marked "very high" likelihood in the risk table and should be the paper's framing from day one. A rigorous negative result — *"DMRG remains competitive to CAS(x,y); the quantum route needs N Toffolis, implying hardware era Z"* — is more useful and more citable than another optimistic small-molecule demonstration.

### 10.4 Two papers, not one

The most important structural recommendation: **do not try to make one submission carry both lanes.** That combination is what produced the current state.

- **Lane B output** — a tools/software paper (JOSS, JOSE, SoftwareX) on the integrated pipeline and UI, with honest illustrative scoring.
- **Lane A output** — a quantum-chemistry methods paper on KatG, with a TB *motivation* rather than a drug-discovery *claim*. The web application is cited as a companion artifact, not as the contribution.

### 10.5 Cost, and the actual bottleneck

**~9 months** in eight phases: environment (2 wk) → ladder rungs 1–3 (4 wk) → rungs 4–5 + ADAPT (4 wk) → classical reference stack (6 wk) → Fe-porphyrin (6 wk) → KatG WT/S315T + noise study (6 wk) → resource estimates (4 wk) → writing and artifact (4 wk).

Two practical blockers to resolve before starting:

- **PySCF has no native Windows support.** The project is on Windows 11. Move the quantum-chemistry work to WSL2 or Linux, in a **separate** `requirements-qc.txt` so the Flask/React side stays installable without a chemistry toolchain. Budget ≥64 GB RAM (statevector past ~28 qubits) and more for DMRG.
- **The gate is not Qiskit — it is CASSCF/active-space expertise.** Choosing an active space, diagnosing convergence failure, and recognising a wrong multireference result. If nobody on the project has run CASSCF on a transition-metal complex, secure a collaborator or advisor with that background before Phase 3. This is the single most common reason projects of this shape stall at rung 6.

### 10.6 Score arithmetic

Same weighting as §9.1. Scientific validity carries the change — weight 0.30, moving 6.5 → 9.5. Novelty at weight 0.05 cannot get you there on its own: even a perfect 10 moves the total by roughly 0.25.

A secondary contribution worth about **+0.3** and available cheaply: calibrate the QPU co-design module (`simulation.py:858-1031`) against published IBM device parameters. The physics is already correct; four fudge factors need fitting and `eps_eff` should use the CPW expression rather than the ideal-microstrip approximation. It pairs naturally with the resource estimates — *here is what the algorithm needs, here is what the hardware provides* — and completes the story.
