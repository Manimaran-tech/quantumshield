# research_improvements.md — Toward Publication-Grade Research

**Project:** QuantumShield
**Audit date:** 2026-07-19
**Framing:** Defensive, simulation-only, educational computational research. All suggestions below are in-silico methodology and software improvements. None concern real-world synthesis, laboratory work, or clinical use.

The single most valuable change is **honesty of labeling**: separate what is genuinely computed (cheminformatics descriptors, a real quantum-RL policy, real database lookups) from what is illustrative (toy docking, mocked "VQE" energies, decorative noise). A project that says exactly what it does — a *quantum-RL molecular-design demonstrator with heuristic scoring* — is publishable as a systems/education contribution. A project that claims validated quantum drug discovery is not.

---

## 1. Scientific-method upgrades

### 1.1 Make the quantum chemistry real (or drop the claim)
- Integrate **Qiskit Nature + PySCF** to construct genuine electronic Hamiltonians for the small molecules already in scope (H₂, LiH, H₂O). Map with parity/Jordan-Wigner, run VQE, and **report the error vs FCI and vs experimental/CCSD(T) reference energies**. This turns the VQE panel from decoration into a verifiable result.
- If a chemistry backend is out of scope for this iteration, rename every "VQE / ground-state / Hartree / electronic energy" element to "classical force-field heuristic" and state the limitation in the paper. Reviewers forgive scope; they do not forgive mislabeling.

### 1.2 Give the quantum-RL agent a defensible objective
- The `QuantumRLAgent` (parameter-shift REINFORCE) is real and interesting. Its weakness is the reward, which mixes valid cheminformatics terms with toy docking/VQE terms. Rebuild the reward from **only defensible, cited components**: QED, SA score (Ertl & Schuffenhauer 2009), Lipinski/Veber filters, PAINS, Tanimoto novelty, and — if docking is wanted — a real docking score from **smina/AutoDock Vina** against a literature pocket. Then the RL curve *means* something.
- Report the classic generative-design metrics: **validity, uniqueness, novelty** (vs training set), QED/SA distributions, and internal diversity — the standard MOSES/GuacaMol battery.

### 1.3 Replace toy docking with a validated pipeline (if docking is a goal)
- Pocket detection: **fpocket** or **P2Rank** (P2Rank is already *named* in the code — actually run it).
- Docking: **AutoDock Vina / smina / gnina**, or at minimum document the electrostatic/steric heuristic honestly with its parameters.
- Benchmark the scorer against a labeled set (e.g., **DUD-E**, **PDBbind** core set) and report enrichment/AUC or RMSE to experimental affinities. Without a benchmark, "kcal/mol" is not defensible.

### 1.4 Real MD instead of a capped toy integrator
- The current Langevin integrator caps forces and velocities "to prevent explosion," which removes physical meaning. For a demonstrator this is fine **if labeled**. For research, use **OpenMM** with a real force field (the code already claims OpenMM/GROMACS in UI text) and report RMSD/RMSF from an actual trajectory with equilibration.

### 1.5 Toxicity / DNA-interaction claims
- `analyze_dna_interaction` cites "ICH M7" and "QSAR" but implements element-count heuristics. Replace with an established structural-alert engine (e.g., RDKit **FilterCatalog** with Brenk/PAINS/NIH alerts) and, for mutagenicity, a validated model or explicit "illustrative" labeling. Remove verdict text like "safe for human use / may proceed to preclinical" — it overstates a heuristic.

---

## 2. Evaluation, benchmarking & statistics

- **Baselines:** Compare the quantum-RL policy against (a) random action selection, (b) a classical neural policy of matched parameter count, and (c) a greedy/hill-climb baseline. The scientific question "does the PQC policy help?" is currently unanswerable.
- **Ablations:** quantum policy vs classical policy; data re-uploading on/off; entanglement layers on/off; reward-term ablations.
- **Statistics:** run each configuration over **N≥10 seeds**, report mean ± 95% CI, and use a proper test (Mann-Whitney U for reward distributions). Right now nothing is seeded and nothing is repeated.
- **No data leakage:** if any learned/statistical model is trained (the LSTM is pre-trained externally), document the train/validation/test split and confirm evaluation molecules are disjoint from training. State the LSTM's training corpus (ZINC?) and cite it.
- **Reference validity:** the LSTM validity/uniqueness numbers should be computed and reported, not asserted (`real_benchmark.py` prints a hardcoded "100.0% valid").

---

## 3. Reproducibility

- **Global seed:** one `--seed` flag threaded through NumPy, PyTorch, and RDKit ETKDG; echo the seed into every result JSON. Remove the in-loop `np.random.seed(100+i)`.
- **Environment:** ship a lockfile (`uv.lock` or `pip-compile` output) that installs cleanly; verify every pin exists; add the missing `transformers` dependency; record Python and OS versions.
- **Model provenance:** document how `pretrained.rnn.pth` (25 MB) was trained (data, epochs, vocab), and re-save as a `state_dict` (also closes the pickle security hole). Provide a checksum.
- **Config, not constants:** move magic numbers (LJ params, reward weights, rescaling constants, noise coefficients) into a versioned `config.yaml` so experiments are describable and repeatable.
- **Determinism note:** state which parts are inherently stochastic (VQE optimizer, MD) and pin their seeds/optimizer settings.

---

## 4. Software-engineering improvements

- **Package layout:** convert the flat root into a package (`quantumshield/{api,chem,quantum,rl,data}`) with `pyproject.toml`; the current 350 KB across four files with duplicated pathogen-normalization logic is hard to maintain.
- **Deduplicate:** one `normalize_pathogen()`, one toxicophore analyzer, one docking/scoring module imported everywhere (see fix.md B3).
- **Typing & validation:** add type hints and validate request payloads with **pydantic** (already a dependency) instead of scattered `data.get(...)` with silent defaults.
- **Logging:** replace `print(...)` with the `logging` module and levels; never log secrets.
- **Tests + CI:** real `pytest` suite (SMILES parse, VQE≈FCI on a real Hamiltonian, reward monotonicity, API-mocking with `responses`) and a GitHub Actions workflow running lint (`ruff`), type-check, and tests. Remove the answer-leaking LLM "test."
- **Error handling:** the broad `except Exception` blocks that silently fall back to fabricated values hide failures — narrow them and surface real errors in dev.
- **Serving:** run behind `waitress`/`gunicorn` with `debug=False`; add per-endpoint input limits and rate limiting on the IBM `api_token` path.

---

## 5. Documentation

- **README rewrite** describing the real Python system, setup, env vars, and — prominently — the **simulation-only scope and the limits of each metric** (what is computed vs illustrative).
- **METHODS.md** giving the exact formula and provenance for every returned quantity, with citations (Ertl SA score, QED Bickerton 2012, transmon relations Koch 2007, parameter-shift Mitarai 2018 / Schuld 2019). Anything without a citation or derivation should be flagged illustrative.
- **Model card** for the LSTM and a **data statement** for the pathogen/target sources (Open Targets, ChEMBL, UniProt, OpenFDA, EMA, PubChem — all already used and creditable).
- **Figures:** clearly annotate which plots are schematic (the sine-jitter "noise" curve) vs measured.

---

## 6. Visualization

- Add uncertainty bands (CI over seeds) to the RL reward curve and any energy plot.
- Label axes with units and state the reference (FCI/experimental) line on energy plots.
- A single dashboard "provenance" badge per number: *computed* vs *database* vs *illustrative*. This alone would resolve most of the integrity concerns.

---

## 7. Suggested future work (in-silico only)

- Real active-space VQE with error mitigation (ZNE) on H₂/LiH, benchmarked vs FCI, as an honest "quantum" contribution.
- Quantum-RL vs classical-RL study on a public molecular-optimization benchmark (GuacaMol goal-directed tasks) — a genuinely publishable comparison.
- Multi-objective Pareto analysis (docking/QED/SA) instead of a single scalarized reward.
- Sensitivity analysis of the reward weights.
- Package the pathogen-metadata resolver as a standalone, tested micro-library — it is genuinely useful on its own.

---

## 8. Publication-readiness matrix

| Component | Current state | Minimum to publish honestly |
|---|---|---|
| Quantum-RL policy (PQC + parameter-shift) | Real, sound | Seed it; add baselines/ablations/CIs |
| VQE electronic energy | Mocked (toy operator) | Real Qiskit Nature/PySCF **or** relabel as heuristic |
| Docking / binding kcal/mol | Toy vs fake pocket | Real docking + benchmark **or** relabel |
| MD stability | Capped toy integrator | OpenMM real FF **or** relabel |
| Toxicity / DNA / ADMET | Heuristics w/ overstated labels | RDKit FilterCatalog + honest wording |
| Pathogen/target metadata | Real public APIs | Cite sources; add caching/tests |
| Cheminformatics descriptors | Real (RDKit) | Keep; report distributions |
| Reproducibility | None (unseeded, no lockfile) | Seeds + lockfile + model card |
| Tests/CI | None (print scripts) | pytest + CI |

Reframed honestly and with the above, this is a credible **undergraduate capstone / demonstrator paper** (systems + education venue). With real VQE benchmarking and an RL baseline study, it approaches a **workshop/conference** methods contribution.
