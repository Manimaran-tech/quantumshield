# research_improvements.md — Toward Publication-Grade Research

**Project:** QuantumShield
**Audit date:** 2026-07-22
**Supersedes:** `research_improvements.2026-07-19.bak.md`
**Framing:** Defensive, simulation-only, educational computational research. Every suggestion below concerns in-silico methodology and software engineering. None concerns real-world synthesis, laboratory work, chemical or biological manufacture, or clinical use.

---

## 0. The one decision that determines everything else

The audit found a large, genuinely working software system — a Flask/React pipeline, a real 3-layer/512-unit SMILES LSTM, correct RDKit descriptor usage, live integrations with seven public biomedical databases, a real Qiskit VQE call, and a block of correct superconducting-qubit physics — wrapped in claims that the code does not support.

**The single highest-value change is not a new algorithm. It is aligning the claims with the implementation.** Everything else follows from which of two lanes you pick.

| | **Lane B — relabel honestly** (do first) | **Lane A — make the science real** (§10) |
|---|---|---|
| Effort | ~5 weeks | ~9 months, **on top of** Lane B |
| Score | 2.0 → **7.2 / 10** | 7.2 → **9.1 / 10** |
| Claim | "An integrated, open pipeline and UI for quantum-inspired molecular design, with illustrative scoring" | "Active-space electronic structure of the KatG heme centre, benchmarked against DMRG, with fault-tolerant resource estimates" |
| Requires | Deleting labels, adding disclosure, tests, CI, a license, documenting what each module actually computes | PySCF/Qiskit Nature, AVAS active-space selection, ADAPT-VQE, DMRG baselines — **and a CASSCF-experienced collaborator** |
| Venue | A software/tools track (JOSS, JOSE, SoftwareX), a systems demo, an undergraduate or master's thesis | A quantum-chemistry methods journal; a quantum-computing conference |
| Risk | Low; the contribution is engineering and pedagogy, both real | DMRG likely wins at every tractable size — which is an acceptable, publishable negative result if framed that way from day one |

**The lanes are sequential, not alternatives.** Lane B is the honest description of what already exists and is publishable in weeks. Lane A assumes Lane B's integrity, reproducibility, and testing work is already done — building real quantum chemistry on an unseeded, untested, unlicensed codebase produces results nobody can verify.

**Lane A also requires changing the scientific question**, not just the Hamiltonian. See §10.1: a gas-phase active-space electronic energy does not predict a binding affinity, so fixing the operator without reframing simply substitutes an accurate number that answers the wrong question. §10.2 gives the reframe that tuberculosis happens to supply.

What is *not* publishable is the current state: Lane B's implementation carrying Lane A's claims.

---

## 1. Scientific-method upgrades

### 1.1 Make the quantum chemistry real, or drop the word

The current Hamiltonian is molecule-independent (verified by execution — five different molecules produce identical non-identity Pauli coefficients). Options:

- **Do it properly:** `qiskit-nature` + **PySCF**. Build an `ElectronicStructureProblem` from real geometries in a defined basis (STO-3G → 6-31G), define an active space with `ActiveSpaceTransformer`, map with `ParityMapper(num_particles=…)` including two-qubit reduction, and use `HartreeFock` as the initial state with a `UCCSD` ansatz. Start with H₂ and LiH, where FCI references are published and the answer is known.
- **Report the number that matters:** error vs FCI in **millihartree**, against the 1.6 mHa chemical-accuracy threshold. Current measured errors are 68–146 mHa — 43–91× outside it — largely because the optimizer budget (COBYLA `maxiter=40` for 64 parameters) is below what COBYLA needs to build its initial simplex. Fixing the budget is a one-line change that will materially improve the result.
- **Add noise honestly:** replace the hand-drawn sinusoidal "NISQ noise" with a real `qiskit_aer` `NoiseModel`, ideally one built from a `FakeBackend` calibration snapshot. Then the error-mitigation comparison becomes a real experiment rather than a tuned constant.
- **Scope it:** an honest paper says "we ran VQE on a CAS(2,2)/CAS(4,4) fragment of the ligand and compared to FCI; the quantum step is currently a demonstration, not a driver of the design decision." Reviewers forgive scope. They do not forgive mislabelling.

**Suggested reading:** Peruzzo et al. (2014) *Nat. Commun.* (VQE); Kandala et al. (2017) *Nature* (hardware-efficient ansätze); Tilly et al. (2022) *Phys. Rep.* (VQE review); Cao et al. (2019) *Chem. Rev.* (quantum chemistry in the age of quantum computing).

### 1.2 Give the RL agent a real learning problem

The parameter-shift REINFORCE machinery in `qrl_optimizer.py` is real and interesting code. Three changes make it a real experiment:

1. **Persist the agent.** Move it out of the request handler; add checkpoint save/load. Right now weights are re-randomized on every HTTP call, so nothing is ever learned.
2. **Sample from the policy.** Actions are currently chosen by greedy reward lookahead, which makes the REINFORCE gradient an estimator of nothing. Either sample from `π_θ`, or keep the greedy search and rename the method to "greedy one-step search with a learned ranker" — which is a legitimate method that just needs an accurate name.
3. **Plot a learning curve.** Reward vs episode, ≥5 seeds, mean ± SD. If the curve is flat, that is the result — report it. A flat curve with an honest explanation is publishable; a fabricated rising curve is not.

**Baselines you must beat (or honestly lose to):** random action selection; the greedy search itself; a classical MLP policy with identical inputs and reward; a genetic algorithm over the same reaction library. Without the classical-policy baseline there is no evidence the quantum circuit contributes anything, and the audit found the encoding is algebraically absorbed into the adjacent variational layer (`RY(a)·RY(b) = RY(a+b)`), so a priori it does not.

**Suggested reading:** Jerbi et al. (2021) *NeurIPS* (parametrized quantum policies for RL); Skolik, Jerbi & Dunjko (2022) *Quantum* (quantum agents in the Gym); Pérez-Salinas et al. (2020) *Quantum* (data re-uploading — note that it requires interleaving, which the current circuit does not do); Cerezo et al. (2021) *Nat. Commun.* (cost-function-dependent barren plateaus).

### 1.3 Replace the docking heuristic or benchmark it

Measured: the current scorer rates **ethanol (MW 46) as a better InhA binder than isoniazid**, with a total dynamic range of 0.9 kcal/mol across a 10× mass span, and reports ethanol at Kd = 5.8 pM. Two root causes — a Hartree/kcal·mol⁻¹ unit mismatch and a clamp to [−22, −6] that forces every molecule into the "picomolar binder" range.

- **Pocket detection:** run **fpocket** or **P2Rank** for real. P2Rank is already *named* in the output strings; running it costs one subprocess call and turns a fabrication into a feature.
- **Docking:** **smina** or **AutoDock Vina** via subprocess, or **gnina** if a learned scorer is wanted. Both are free, scriptable, and citable.
- **Benchmark, and report the benchmark:** correlation and RMSE against experimental affinities on the **PDBbind** core set (CASF-2016); enrichment factor and ROC-AUC on **DUD-E** or the less-biased **LIT-PICV**/**DEKOIS** sets. Without this, "kcal/mol" is a unit label, not a measurement.
- **Sanity tests as unit tests:** assert that a known strong binder outscores ethanol; assert monotonicity on a small congeneric series. These would have caught the current defect immediately.

**Suggested reading:** Trott & Olson (2010) *J. Comput. Chem.* (Vina); Koes, Baumgartner & Camacho (2013) *J. Chem. Inf. Model.* (smina); Su et al. (2019) *J. Chem. Inf. Model.* (CASF-2016); Krivák & Hoksza (2018) *J. Cheminform.* (P2Rank); Chen et al. (2019) *J. Chem. Inf. Model.* (on hidden bias in docking benchmarks).

### 1.4 Use published property models instead of invented formulas

Every ADMET, toxicity, and synthetic-accessibility number in the codebase is a hand-fitted linear formula. Free, citable replacements exist for all of them:

| Quantity | Currently | Replace with |
|---|---|---|
| Synthetic accessibility | 3 mutually inconsistent formulas keyed on Lipinski violations | RDKit `Contrib/SA_Score/sascorer.py` — Ertl & Schuffenhauer (2009) *J. Cheminform.* |
| Toxicity / liability | Element counts gated on ≤3 heavy atoms (unreachable for all real candidates) | RDKit `FilterCatalog` — PAINS (Baell & Holloway 2010), Brenk (2008), NIH alerts |
| Fsp3 | Recomputed from interatomic distances with a 1.6 Å cutoff | `Lipinski.FractionCSP3` |
| Drug-likeness | `100 - violations*25` | `QED.qed` (Bickerton et al. 2012 *Nat. Chem.*) — already used elsewhere in the file |
| Oral-absorption rules | Two-branch string | Veber et al. (2002) rules alongside Lipinski; report both, and allow Ro5's one permitted violation |
| Retrosynthesis | `int(2 + sa_score // 1.5)` | **AiZynthFinder** (Genheden et al. 2020 *J. Cheminform.*) — free, or drop the claim |
| ADMET endpoints | `papp = 15 + 3.5·logP − …` | **ADMETlab 3.0** or **admetSAR**, or a model you train on **TDC** (Therapeutics Data Commons) with a reported test-set metric |

The rule: if a number is shown to a user with a physical unit attached, it must come from a method with a citation, or be visibly labelled as illustrative.

### 1.5 Report the standard generative-model metrics

Nothing in the repo currently measures generative quality. The field has a settled battery — run it and publish the table:

- **Validity, uniqueness@1k/@10k, novelty vs the training corpus** (this last one is impossible today because the training corpus is undocumented — see §3.1).
- **Distribution metrics:** FCD, SNN, Fragment/Scaffold similarity, internal diversity — via **MOSES** (Polykovskiy et al. 2020 *Front. Pharmacol.*).
- **Goal-directed benchmarks:** **GuacaMol** (Brown et al. 2019 *J. Chem. Inf. Model.*) rediscovery and MPO tasks — these are exactly designed to test the kind of optimization loop this project implements, and would give the QRL agent a scoreboard other researchers recognize.
- **Report the sampling temperature.** It is currently hardcoded at 0.8 with a comment saying it was chosen "to increase validity", and the sequence length is truncated to 128 while the checkpoint was trained to 256. Any validity number reported today is a function of two undisclosed hyperparameters.

### 1.6 Statistical rigour

- **Every reported number needs n, a seed, and a dispersion measure.** Currently n = 1 and unseeded — two identical calls gave binding energies of −17.04 and −16.92 kcal/mol.
- **Comparisons need a test.** "QRL beats the reference drug" requires ≥30 paired runs and a Wilcoxon signed-rank (non-normal) or paired t-test, with an effect size (Cliff's δ or Cohen's d), not a single anecdote. And it requires that the comparison not be rigged by post-hoc "lead polishing".
- **Correct for multiple comparisons** when screening many candidates (Benjamini–Hochberg).
- **Report negative results.** If the quantum policy does not beat the classical one, say so with the numbers. That is the most scientifically valuable thing this project could produce.

---

## 2. Benchmarking

### 2.1 Replace `real_benchmark.py`

The current file times four unrelated operations once each, then prints a hardcoded `"100.0% chemically valid"` verdict, and its "genetic engine" performs the same deterministic operation 20 times. Rebuild it as:

- **Warm-up + ≥10 repetitions**, reporting median and IQR, using `time.perf_counter`.
- **Hardware disclosure:** CPU model, RAM, OS, Python, torch build, thread count.
- **Comparable units:** molecules/second for generation; seconds/ligand for docking; circuit executions/second for VQE. Do not put a cloud API latency in the same column as a local matrix operation without saying so.
- **Scaling curves, not points:** VQE wall-clock and circuit depth vs qubit count (2→16); docking time vs ligand heavy-atom count. These are the plots that show whether the approach scales, and they replace the current `f"{n} Qubits (Polynomial O(N^4))"` string, which asserts a complexity claim without measuring anything.

### 2.2 Add reference datasets

| Purpose | Dataset | Why |
|---|---|---|
| Docking accuracy | PDBbind core / CASF-2016 | Standard, has experimental affinities |
| Virtual-screening enrichment | DUD-E, DEKOIS 2.0, LIT-PCBA | LIT-PCBA is the least biased |
| Generative quality | MOSES, GuacaMol, ZINC-250k | Standard splits already published |
| Property prediction | MoleculeNet, Therapeutics Data Commons | Pre-split, leaderboards exist |
| TB-specific actives | ChEMBL *M. tuberculosis* InhA/KatG bioactivities | Directly relevant to the stated aim; ChEMBL is already integrated |
| Quantum chemistry | QM9, published H₂/LiH/BeH₂ FCI curves | Lets you state a real error bar |

Committing a small, dated, checksummed subset of one of these into `data/` would let any reviewer reproduce the headline numbers in minutes.

### 2.3 Ablations that would strengthen the paper

- Quantum policy vs classical MLP policy, identical reward and budget.
- Reward-term ablation: drop each of the nine terms in turn, report the effect on final candidate quality.
- Ansatz depth sweep: reps ∈ {1,2,3,4} — expressivity vs trainability, and a barren-plateau check (gradient variance vs qubit count).
- Optimizer budget sweep: maxiter ∈ {40, 200, 1000} — this alone will show that the current 40 is the dominant error source.
- Seed sensitivity: 10 seeds, report the spread. A method whose output varies by 49 kcal/mol between seeds needs this stated up front.

---

## 3. Reproducibility

### 3.1 Model and data provenance — the highest-priority item in this section

Nobody outside the project can currently reproduce anything the generative model does, because nothing about it is recorded.

- **Document the corpus.** Which ZINC release, which tranche, what filters (MW range, logP, charge, element set), how many molecules, and the train/valid/test split with its seed. Commit a `data/download.sh`.
- **Publish a checksum.** `sha256sum pretrained.rnn.pth` in the README, and a `model_card.md` giving architecture (verified: 3 layers, 512 units, 512-d embedding, dropout 0.2, 57-token vocabulary, max length 256), training config, epochs, and the validation loss curve.
- **Re-save as a `state_dict`.** The checkpoint is currently a pickled Python object loaded with `weights_only=False`, so cloning the repo and running it executes arbitrary code from a 25 MB binary of undocumented origin. `state_dict` + `weights_only=True` fixes provenance and security together.
- **Add the licenses.** `smiles_lstm/` is derived from REINVENT (Apache-2.0) per its own file headers, and the repository has no LICENSE file at all. Add the upstream `LICENSE` and `NOTICE`, plus a top-level license for your own code. Journals and code-release policies will check this.

### 3.2 Determinism

Exactly one seeding call exists in the entire repository, and it is a *global* NumPy reseed inside an unrelated function, which silently couples every downstream random consumer to a UI slider value.

```python
# seeds.py
def set_global_seed(seed: int) -> None:
    import random, numpy as np, torch
    random.seed(seed); np.random.seed(seed)
    torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
```
- Call it at process start and at every experiment entry point.
- Replace module-global `np.random` use with per-object `np.random.default_rng(seed)`.
- Pass `initial_point` to `VQE` and a seed to SPSA/COBYLA.
- **Echo the seed and the full resolved config in every API response and every results file.** This single habit converts an irreproducible demo into a reproducible experiment.

### 3.3 Environment capture

- `git add requirements.txt` — it is currently **untracked**, so a fresh clone has no dependency list.
- Add `transformers` (imported by `real_benchmark.py`, absent from requirements) and install `pytest` (listed but missing, so the suite cannot run).
- Pin with `pip-compile` → `requirements.lock`; add `pyproject.toml` and `environment.yml`; record Python and OS versions.
- Ship a `Dockerfile` — for a project with an RDKit + Qiskit + Torch + Node stack, this is the difference between "reviewers can run it" and "reviewers take your word for it".
- **Commit the working tree before generating paper numbers.** Four core science files currently have uncommitted modifications, so no existing result can be tied to a commit hash.
- Record a `run_manifest.json` with every result: git SHA, seed, config, package versions, timestamp, hardware.

### 3.4 Configuration

Move every hardcoded scientific constant into a versioned `config.yaml`: sampling temperature and length, optimizer budgets, ansatz reps, all nine reward weights, learning rate, qubit count, pocket residue count, MD steps and temperature (currently 310.15 K while the Kd conversion uses the 298 K constant 1.364 — pick one and state it), and the clamp ranges. Validate it with `pydantic`, which is already a declared dependency and currently unused.

---

## 4. Engineering improvements

### 4.1 Structure

```
quantumshield/
├── src/quantumshield/
│   ├── api/            # Flask routes only — no science
│   ├── chem/           # descriptors, docking, ADMET
│   ├── quantum/        # Hamiltonians, VQE, circuits
│   ├── rl/             # agent, environment, reward
│   ├── data/           # external API clients, cached
│   └── config.py
├── tests/{unit,integration}/
├── data/               # checksummed reference subsets
├── configs/
├── pyproject.toml
├── LICENSE  NOTICE  README.md  model_card.md
└── .github/workflows/ci.yml
```
This also breaks the current circular import between `simulation.py` and `generator.py`, which is presently worked around by importing inside a per-candidate loop.

### 4.2 Testing

- Convert the print-scripts to real assertions. Five of nine test files currently contain **zero** assertions.
- **Golden-value regression tests** are the most valuable addition: pin the docking score of isoniazid, the Kd of a known binder, the fitness of a reference molecule. Any of these would have caught the inverted fitness sign and the ethanol result.
- Property-based tests with `hypothesis` over valid SMILES: no NaN, no infinity, scores monotone in the intended direction, empty input rejected.
- Mock all network with `responses`; mark live-API tests `@pytest.mark.integration` and exclude them by default.
- Target ≥70 % line coverage on `chem/`, `quantum/`, and `rl/` via `pytest-cov`.

### 4.3 CI/CD

A minimal GitHub Actions workflow: `ruff` → `mypy` → `pytest` (unit) → `pip-audit` → `gitleaks`. A weekly scheduled job running the integration tests catches external-API breakage before a reviewer does — which is exactly how the dead PubChem property name and the 404 EMA endpoint went unnoticed.

### 4.4 Observability and error handling

- Replace all `print()` with `logging`; structured JSON logs; a request ID per API call.
- Replace the 65 broad `except Exception` / bare `except` handlers with specific exceptions.
- **Never substitute a fabricated value on failure.** Return `{"status": "error", "stage": "...", "reason": "..."}`. The current pattern — where an exception silently becomes a scientific number — is the mechanism behind most of the fabrication findings.
- Add a `"provenance"` block to every response: `{"source": "alphafold" | "synthetic", "seed": …, "config_hash": …, "git_sha": …}`. This is cheap, and it makes the honest-labelling problem structurally impossible to reintroduce.

### 4.5 Performance

- Cache external API responses (`requests_cache`), with retry/backoff and a descriptive `User-Agent` — EBI and NCBI both ask for one and rate-limit anonymous traffic.
- Call `resolve_pathogen_metadata` once per request, not twice; the current double call also risks reporting a target that does not match the pocket actually used.
- Compile PAINS SMARTS once at import, not per reward evaluation.
- Replace the O(n⁴) functional-group detector with `Chem.MolFromSmarts` substructure matching — O(n) in practice and more correct.
- Wrap generation in `torch.no_grad()`; use a `set` for deduplication.
- Move long-running work (QRL optimization can block for minutes) to a task queue with a job-status endpoint.

---

## 5. Documentation

1. **Rewrite `README.md`.** It is currently the untouched Google AI Studio scaffold and describes a different project entirely. It needs: what the system does, an architecture diagram, install steps, how to reproduce each figure, hardware requirements, license, citation, and — most importantly — an explicit **Scope and Limitations** section.
2. **Write the limitations section first, and put it early.** Something like: *"Binding affinities are produced by a simplified Lennard-Jones heuristic and have not been benchmarked against experimental data; they are illustrative and must not be interpreted as predicted affinities. The VQE module operates on a model Hamiltonian and does not currently perform electronic-structure calculation. The dose-response curves are synthetic."* A reviewer who reads this respects the work. A reviewer who discovers it themselves does not.
3. **`model_card.md`** for the LSTM; **`data_card.md`** for each external source with its access date and license.
4. **API reference** — OpenAPI/Swagger generated from `pydantic` request models.
5. **Fix the specific documentation errors identified:** the "< 8 eV HOMO–LUMO gap indicates toxicity" claim (would flag nearly every drug); the "reducing traditional timelines from years to hours" and "unprecedented accuracy" claims (unmeasured); the InhA/*katG* S315T mutation attribution; and the SARS-CoV-2 spike variants listed against an Mpro target.
6. **Provide the missing citation or remove the claim** for the "Wang et al. inspired scoring function" comment in `simulation.py:1882` — it is the only citation-shaped claim in the codebase that cannot be checked. (Positively: the eight references in `ppt.md` were spot-checked and are genuine; no fabricated bibliography was found.)

---

## 6. Visualization

- **Add uncertainty to every plot.** Error bars, confidence bands, and n. Single-run point estimates from a stochastic pipeline are misleading regardless of intent.
- **Visually distinguish computed from illustrative values** — a persistent badge, hatched fill, or muted colour for any synthetic quantity. This is the cheapest and most durable integrity control available.
- **Plot the real VQE convergence trace**, with the FCI reference as a horizontal line and the chemical-accuracy band shaded. That plot is genuinely interesting once the optimizer budget is fixed.
- **Learning curves** for the RL agent: reward vs episode, mean ± SD over seeds.
- **Chemical-space maps:** UMAP/t-SNE of Morgan fingerprints showing generated candidates against the reference drug and the training distribution — the standard figure for a generative-chemistry paper.
- **A Pareto front** for the multi-objective trade-off (affinity vs SA vs QED) instead of a single collapsed fitness scalar.
- **Accessibility:** colourblind-safe palettes (viridis/cividis), readable at greyscale, with axis units on every axis.

---

## 7. Research-integrity practices to adopt

These are process changes, not code changes, and they are what prevent a recurrence:

1. **A "no synthetic data without a flag" rule.** Any function that can return a fabricated value must set `is_synthetic: true` in its return, and the UI must render it.
2. **No tool name in user-facing text unless that tool executes.** The repo currently names AutoDock Vina, GROMACS, OpenMM, P2Rank, and Qiskit Metal in output strings; none of them run.
3. **No unconditional success strings.** `PASSED`, `[SUCCESS]`, `[PROVED]`, and "converged" must be behind an actual comparison.
4. **No post-hoc adjustment conditioned on beating a baseline.** The "lead polishing" block is the clearest example and should be deleted rather than fixed.
5. **Pre-register the analysis** for any comparison you intend to publish: metric, n, test, and threshold, written down before running it.
6. **Keep a lab notebook** — `experiments/YYYY-MM-DD-name/` with config, seed, git SHA, raw output, and a short interpretation.

---

## 8. Future work, ordered by value per unit effort

**Near term (weeks)**
1. Honest labelling pass across code, UI, and docs — highest value, lowest cost, unblocks everything else.
2. Global seeding + config capture + `run_manifest.json`.
3. Real `pytest` suite with golden-value regression tests.
4. Fix the optimizer budget (`maxiter ≥ 20·n_params`) and re-measure the VQE–FCI gap; this may improve the headline error by an order of magnitude for free.
5. Swap in RDKit `sascorer` and `FilterCatalog`.

**Medium term (months)**
6. Qiskit Nature + PySCF for H₂/LiH/BeH₂, validated against published FCI.
7. smina/Vina integration, benchmarked on CASF-2016.
8. A real RL training loop with persistence, on-policy sampling, and a classical-policy baseline.
9. MOSES/GuacaMol evaluation of the generator.
10. Dockerfile + CI + a public reproducibility artifact.

**Longer term (research directions, honestly framed)**
11. **Quantum-advantage null study.** Systematically compare the quantum policy against a matched classical policy across targets and seeds. Whatever the answer, it is publishable — and the field currently needs more careful negative results than more optimistic demos.
12. **Barren-plateau characterization** for this ansatz family: gradient variance vs qubit count and depth.
13. **Hardware-aware co-design.** The transmon block (`simulation.py:858-1031`) is the most scientifically defensible part of the codebase — correct constants, correct `f_q = √(8E_J E_C) − E_C`, correct CPW resonator relation. Calibrating its four fudge factors against published IBM device parameters and comparing predicted vs reported T₁/T₂ and gate errors would make a small, self-contained, genuinely novel contribution. **This is the most promising publishable kernel in the repository and is currently buried.**
14. **Active-learning loop** over public bioactivity data (ChEMBL is already integrated) — a defensible way to make the optimization loop learn from real labels.
15. **Uncertainty quantification** on property predictions (conformal prediction or deep ensembles), so candidates come with calibrated confidence rather than a formula named `confidence`.

---

## 9. Venue suitability, as the project stands and after remediation

| Venue | Now | After Lane B | After Lane A |
|---|---|---|---|
| Undergraduate capstone / final-year project | Borderline — the engineering is strong, the claims are not defensible | **Yes, strong** | Yes |
| Master's thesis | No | Yes, with a thorough limitations chapter | Yes, strong |
| PhD-level prototype | No | No | Plausible, if the null study is done well |
| Software/tools track (JOSS, JOSE, SoftwareX) | No — needs tests, license, docs | **Yes** — this is the natural fit | Yes |
| Cheminformatics methods journal | No | No | Yes, with the benchmark tables |
| Quantum-computing workshop | No | Poster, framed as a systems demo | Yes, especially as a negative result |

The engineering effort already invested here is substantial and real. The gap between where it is and where it is publishable is almost entirely a **claims** gap, not a **code** gap — which is unusually good news, because claims are the cheapest thing in a project to fix.

---

# 10. Lane A in full — the quantum-chemistry path to 9.0 / 10

`audit_summary.md` §9 costs the route to **7.2** (tools/systems venue, defensible thesis). This section costs the route to **9.1** — a methods paper in a peer-reviewed quantum-chemistry or quantum-computing venue. `audit_summary.md` §10 is the condensed version of this section.

**The single most important thing in this section is §10.1.** Fixing the Hamiltonian is necessary and not close to sufficient; without the reframe, perfect quantum chemistry still yields an invalid paper.

---

## 10.1 Why fixing the Hamiltonian alone caps you at ~6.5

Suppose you do everything in §1.1 correctly: PySCF driver, real integrals, correct mapping, converged VQE, error under 1.6 mHa against FCI. You would then have **an accurate ground-state electronic energy for a 4–8 orbital active space of a molecular fragment.**

That quantity does not predict binding affinity. Binding free energy decomposes roughly as

```
ΔG_bind  =  ΔE_interaction  +  ΔG_solvation  +  −TΔS_conformational  +  ΔG_desolvation  +  strain
```

A gas-phase active-space electronic energy addresses a small part of the first term only. It says nothing about solvation, nothing about entropy, nothing about conformational sampling — and those terms routinely dominate. Reporting a VQE energy and calling it a binding prediction is a **broken inference chain**, and a domain reviewer will identify it in the first pass.

So the current architecture has a structural problem that is independent of code quality:

> The project computes something quantum (an electronic energy), then reports something biological (a binding affinity), with no valid bridge between them.

There are exactly two honest resolutions:

- **(a) Build the bridge properly** — a defensible QM/MM partition with free-energy perturbation or thermodynamic integration, quantum only in the QM region. This is a large undertaking and the quantum part contributes a small fraction of the total error budget, which makes the quantum-advantage story weak.
- **(b) Change the question to one the quantum method actually answers.** Cheaper, more rigorous, and — for tuberculosis specifically — scientifically better. **This is the recommended path and the rest of §10 assumes it.**

---

## 10.2 The scientific question to ask instead — and why TB hands it to you

Isoniazid is a **prodrug**. The mechanism, well established in the literature:

1. **KatG** — a bifunctional catalase-peroxidase with a **heme b (Fe-protoporphyrin IX)** cofactor — oxidizes isoniazid to an isonicotinoyl radical.
2. That radical couples to NAD⁺, forming the **INH-NAD adduct**.
3. The adduct is the actual inhibitor of **InhA** (enoyl-ACP reductase), blocking mycolic-acid synthesis.
4. The dominant clinical resistance mutation, ***katG* S315T**, impairs **step 1** — the activation — not the binding in step 3.

This matters enormously for a quantum-chemistry paper, because:

- **Fe-porphyrin is the canonical strongly-correlated system.** Near-degenerate Fe 3d orbitals, multiple close-lying spin states, and significant static correlation. Single-reference methods (HF, DFT, CCSD(T)) are unreliable; CASSCF/NEVPT2 or DMRG are required. This is precisely the regime where quantum algorithms are argued to have a plausible advantage — the same reasoning behind the FeMoco (Reiher et al. 2017, *PNAS*) and cytochrome P450 (Goings et al. 2022, *PNAS*) resource-estimate studies.
- **The question is a genuine chemistry question**, not a proxy: spin-state energetics of the KatG heme center, and the electronic structure along the isoniazid activation coordinate.
- **It connects to the drug-resistance story you already care about**, via S315T's effect on the activation step.
- **It is honest about scale.** Nobody expects a full protein. An active-space model of the heme site is exactly the right granularity, and is what the resource-estimate literature actually studies.

**Recommended paper framing:**

> *Active-space electronic structure of the Mycobacterium tuberculosis KatG heme centre along the isoniazid activation coordinate: a comparison of ADAPT-VQE against CASSCF, NEVPT2, and DMRG references, with fault-tolerant resource estimates and an assessment against classical-advantage skepticism.*

Legitimate alternatives at the same rigour level, if heme proves too heavy:

| Question | Why QM is the right tool | Reference for the target |
|---|---|---|
| Covalent-inhibition reaction barriers | Bond forming/breaking — QM required by definition | Any covalent TB inhibitor series |
| Tautomer / protonation-state energetics | Small energy differences that MM force fields get wrong | Isoniazid, pyrazinamide |
| Redox potentials of the INH radical intermediates | Open-shell, spin-state sensitive | The activation cascade above |
| Torsional profiles for force-field parameterization | A real, useful QM deliverable | The INH-NAD adduct |

Any of these produces a defensible paper. **"Quantum-computed binding affinity" does not, at any level of code quality.**

---

## 10.3 What to delete

Lane A is not built on top of the current quantum module — it replaces it. Delete outright:

| Delete | File | Reason |
|---|---|---|
| `get_molecular_hamiltonian` | `simulation.py:199-242` | Molecule-independent toy operator (verified). Nothing in it is salvageable |
| `calculate_coordinate_energy` | `simulation.py:139-197` | Invented constants, 1–2 orders of magnitude off, unit-inconsistent |
| `solve_huckel_gap` | `simulation.py:244-406` | No matrix, no diagonalization; an if/elif lookup table |
| Hardcoded HOMO/gap table | `simulation.py:1329-1355` | Ionization potentials copy-pasted into gap fields |
| Synthetic noise + synthetic convergence | `simulation.py:1168-1233` | Replaced by a real `NoiseModel` |
| `fci_energy` naming everywhere | `simulation.py:1117-1122` | It is exact diagonalization of a model operator, not FCI. Rename or delete |
| VQE→binding-energy coupling | `simulation.py:1306-1310` | The broken inference chain of §10.1 |
| `run_actual_vqe` | `qrl_optimizer.py:61-85` | 12 parameters, `maxiter=15`; superseded |
| `scratch_huckel_test.py` | whole file | Fractional π-electron counts, β applied to σ bonds and hydrogens |

**Keep and preserve:** the QPU co-design module (`simulation.py:858-1031`) — correct physics, and it becomes a genuine secondary contribution once calibrated (§10.9).

---

## 10.4 Environment — do this first, it is a real blocker

**PySCF does not support Windows natively.** The project is currently on Windows 11. Options, in order of preference:

1. **WSL2 + Ubuntu 22.04** — recommended. Full PySCF, block2, and OpenFermion support.
2. Linux workstation or HPC allocation — needed anyway for DMRG.
3. Docker on Windows — works, slower for the heavy runs.

```bash
# inside WSL2 / Linux
python -m venv .venv-qc && source .venv-qc/bin/activate
pip install \
  pyscf==2.7.0 \
  qiskit==2.4.2 qiskit-nature==0.7.2 qiskit-algorithms==0.4.0 \
  qiskit-aer==0.15.1 \
  openfermion==1.6.1 openfermionpyscf==0.5 \
  block2==0.5.3 \
  mthree==2.7.0 \
  pandas pyarrow
```

Add these to a **separate** `requirements-qc.txt`. Do not merge them into the web app's requirements — the Flask/React side must stay installable on Windows without a quantum-chemistry toolchain.

Hardware you will actually need: **≥64 GB RAM** for statevector beyond ~28 qubits, and DMRG on a heme active space is comfortable at 128 GB. Budget for this explicitly; it is a common reason these projects stall.

---

## 10.5 What to add — module by module

### 10.5.1 New package layout

```
src/quantumshield_qc/
├── structures/
│   ├── build.py          # active-site model construction, capping, geometry
│   └── katg_heme.py      # the KatG cluster model + S315T variant
├── electronic_structure/
│   ├── driver.py         # PySCF -> ElectronicStructureProblem
│   ├── active_space.py   # AVAS / NO-occupation selection
│   └── classical_ref.py  # CASSCF, NEVPT2, CCSD(T), DMRG references
├── quantum/
│   ├── hamiltonian.py    # mapping + tapering
│   ├── ansatz.py         # UCCSD / k-UpCCGSD / ADAPT
│   ├── solver.py         # VQE driver with gradients + convergence checks
│   ├── noise.py          # NoiseModel + ZNE + M3
│   └── resources.py      # fault-tolerant Toffoli/qubit counts
├── benchmarks/
│   ├── ladder.py         # H2 -> LiH -> BeH2 -> N2 -> Fe-porphyrin -> KatG
│   └── references.yaml   # published values with DOIs, for assertions
└── analysis/
    ├── plots.py
    └── tables.py
```

### 10.5.2 `electronic_structure/driver.py` — a real Hamiltonian

```python
from qiskit_nature.second_q.drivers import PySCFDriver
from qiskit_nature.second_q.transformers import ActiveSpaceTransformer, FreezeCoreTransformer

def build_problem(xyz: str, basis: str = "sto-3g", charge: int = 0, spin: int = 0,
                  freeze_core: bool = True):
    """Return a qiskit-nature ElectronicStructureProblem from real integrals."""
    driver = PySCFDriver(atom=xyz, basis=basis, charge=charge, spin=spin,
                         unit=DistanceUnit.ANGSTROM)
    problem = driver.run()
    if freeze_core:
        problem = FreezeCoreTransformer().transform(problem)
    return problem
```

**Basis-set ladder is not optional in a methods paper.** Report STO-3G → 6-31G* → cc-pVDZ (→ cc-pVTZ where feasible) and show convergence. A single-basis result reads as a demo.

### 10.5.3 `electronic_structure/active_space.py` — principled selection

The current code picks `active_orbitals` from a UI slider. That is indefensible. Use **AVAS** (Sayfutyarova et al. 2017, *JCTC*), which selects orbitals by projection onto chosen atomic valence orbitals — for heme, the Fe 3d set plus porphyrin π:

```python
from pyscf import gto, scf
from pyscf.mcscf import avas

def select_active_space(mol, mf, ao_labels=("Fe 3d", "Fe 4d", "N 2pz")):
    """AVAS: pick the active space by AO projection, not by hand."""
    ncas, nelecas, mo_coeff = avas.avas(mf, ao_labels, canonicalize=True)
    return ncas, nelecas, mo_coeff
```

Alternative/cross-check: natural-orbital occupation numbers from an MP2 or CCSD density — retain orbitals with occupations in roughly `[0.02, 1.98]`. **Report both, and show the result is stable under the choice.** Active-space sensitivity is the first thing a referee in this field probes.

Then hand it to qiskit-nature:

```python
problem = ActiveSpaceTransformer(
    num_electrons=nelecas, num_spatial_orbitals=ncas,
    active_orbitals=active_idx,          # explicit indices, logged
).transform(problem)
```

Log the chosen indices, their occupations, and their symmetry labels into the run manifest. This is a primary methods table in the paper.

### 10.5.4 `quantum/hamiltonian.py` — mapping and tapering

```python
from qiskit_nature.second_q.mappers import ParityMapper

def build_qubit_op(problem):
    mapper = ParityMapper(num_particles=problem.num_particles)   # 2-qubit reduction
    tapered = problem.get_tapered_mapper(mapper)                 # Z2 symmetry tapering
    qubit_op = tapered.map(problem.hamiltonian.second_q_op())
    return qubit_op, tapered
```

Z₂ tapering (Bravyi et al. 2017) exploits particle-number, S_z, and point-group symmetries. Report the qubit count **before and after** — it is a real result and it is what makes larger active spaces tractable:

| Active space | Spin orbitals | JW qubits | + parity reduction | + Z₂ tapering |
|---|---|---|---|---|
| CAS(2,2) — H₂ | 4 | 4 | 2 | 1 |
| CAS(4,4) | 8 | 8 | 6 | 4–5 |
| CAS(6,6) | 12 | 12 | 10 | 7–8 |
| CAS(8,8) | 16 | 16 | 14 | 10–12 |
| CAS(10,10) — minimal heme | 20 | 20 | 18 | 13–15 |
| CAS(16,16) — realistic heme | 32 | 32 | 30 | 24–26 |

Compare Jordan–Wigner, parity, and Bravyi–Kitaev on gate count after transpilation — a cheap, publishable comparison table.

### 10.5.5 `quantum/ansatz.py` — chemistry-appropriate, not hardware-efficient

The current `TwoLocal(['ry','rz'], ['cx'])` conserves nothing and explores unphysical Fock sectors. Replace:

```python
from qiskit_nature.second_q.circuit.library import HartreeFock, UCCSD

def build_uccsd(problem, mapper):
    init = HartreeFock(problem.num_spatial_orbitals, problem.num_particles, mapper)
    return UCCSD(problem.num_spatial_orbitals, problem.num_particles, mapper,
                 initial_state=init)
```

UCCSD parameter count scales as O(N⁴) in orbitals and becomes intractable quickly. Above roughly CAS(6,6), switch to **ADAPT-VQE** (Grimsley et al. 2019, *Nat. Commun.*) or **qubit-ADAPT-VQE** (Tang et al. 2021, *PRX Quantum*), which grow the ansatz operator-by-operator using gradient screening:

```python
from qiskit_algorithms import VQE, AdaptVQE

adapt = AdaptVQE(VQE(estimator, uccsd, optimizer), gradient_threshold=1e-3, max_iterations=50)
result = adapt.compute_minimum_eigenvalue(qubit_op)
```

Report ansatz depth, CNOT count post-transpilation, and parameter count for every rung of the ladder. **k-UpCCGSD** is a good third point on the expressivity/depth trade-off curve.

### 10.5.6 `quantum/solver.py` — an optimizer that actually converges

This is where the current code fails hardest — measured error 68–146 mHa, against a 1.6 mHa target, because COBYLA got 40 iterations for 64 parameters.

```python
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP, L_BFGS_B
from qiskit_algorithms.gradients import ParamShiftEstimatorGradient

def run_vqe(qubit_op, ansatz, estimator, seed, maxiter=None):
    n = ansatz.num_parameters
    rng = np.random.default_rng(seed)
    x0 = rng.normal(0.0, 1e-2, n)          # near-HF start, not uniform random
    grad = ParamShiftEstimatorGradient(estimator)
    opt  = SLSQP(maxiter=maxiter or max(500, 30 * n), ftol=1e-9)
    vqe  = VQE(estimator, ansatz, opt, gradient=grad, initial_point=x0,
               callback=record)
    res  = vqe.compute_minimum_eigenvalue(qubit_op)
    return res
```

Non-negotiable reporting for every run:
- error vs the classical reference in **millihartree**, against the 1.6 mHa chemical-accuracy line
- number of energy evaluations and whether the optimizer reported convergence
- ≥5 random seeds, mean ± SD — a method with a 49 kcal/mol seed spread (the current state) is not a method
- wall-clock and circuit-execution counts

### 10.5.7 `quantum/noise.py` — real noise, real mitigation

```python
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke
import mthree

backend = FakeSherbrooke()
noise_model = NoiseModel.from_backend(backend)
sim = AerSimulator(noise_model=noise_model)

mit = mthree.M3Mitigation(backend)      # Nation et al. 2021, readout mitigation
mit.cals_from_system(qubits)
```

Then a real mitigation study: **unmitigated → ZNE** (Temme/Bravyi/Gambetta 2017) **→ ZNE + readout mitigation**, each measured against the exact value. That table replaces the current hand-tuned sinusoid, and it is a legitimate paper contribution on its own.

### 10.5.8 `quantum/resources.py` — the item that makes it a methods paper

NISQ VQE will not beat DMRG on a heme active space. Saying so, quantitatively, is the strongest section you can write. Use OpenFermion's resource-estimation module, which implements the modern factorization-based qubitization costings (single-factorization, double-factorization, tensor hypercontraction):

```python
from openfermion.resource_estimates import df, sf, thc
from openfermion.resource_estimates.molecule import pyscf_to_cas

h1, eri, ecore, num_alpha, num_beta = pyscf_to_cas(mf, ncas, nelecas)
# double-factorization costing -> logical qubits and Toffoli count for QPE
lam, toffolis, logical_qubits = df.compute_cost(...)
```

Report: logical-qubit count, Toffoli/T count, and — using published surface-code overhead assumptions with the physical error rate stated — the implied physical-qubit count and runtime. Compare against the anchors: FeMoco ≈10¹¹ T gates (Reiher 2017), later reduced to ≈10¹⁰ (Lee et al. 2021); cytochrome P450 ≈10⁹–10¹⁰ Toffoli (Goings et al. 2022). A KatG number placed on that scale is a genuinely novel, citable contribution.

---

## 10.6 The validation ladder — each rung is a hard gate

Do not proceed to rung *n+1* until rung *n* passes in CI. Encode every published reference value in `benchmarks/references.yaml` **with its DOI**, and assert against it.

| # | System | Method | Gate |
|---|---|---|---|
| 1 | H₂, STO-3G, r = 0.735 Å | VQE vs FCI | error < 1.6 mHa; dissociation curve 0.4–3.0 Å |
| 2 | LiH, STO-3G/6-31G | VQE vs FCI | < 1.6 mHa across the full curve |
| 3 | BeH₂ | VQE vs FCI | < 1.6 mHa; matches Kandala et al. 2017 qualitatively |
| 4 | **N₂ triple-bond breaking** | ADAPT-VQE vs CASSCF/NEVPT2 | non-parallelity error < 5 mHa — **the multireference stress test; single-reference methods fail here by design** |
| 5 | H₂O, symmetric stretch | vs FCI | < 1.6 mHa at 1×, 1.5×, 2× r_e |
| 6 | Fe-porphyrin model (no protein) | ADAPT-VQE vs CASSCF/NEVPT2 **and DMRG** | spin-state gaps within 5 mHa of the DMRG reference |
| 7 | KatG heme cluster, WT | full pipeline | reproducible across ≥5 seeds; active-space sensitivity documented |
| 8 | KatG heme cluster, **S315T** | full pipeline | the actual scientific result |

Rung 4 is the one that separates a serious study from a demo. If your method cannot break N₂ correctly, it cannot say anything about a heme centre, and a referee knows this.

```python
# benchmarks/test_ladder.py
@pytest.mark.parametrize("system,ref_energy,doi", load_references())
def test_chemical_accuracy(system, ref_energy, doi):
    e = run_pipeline(system, seed=1337)
    err_mHa = abs(e - ref_energy) * 1000
    assert err_mHa < 1.6, f"{system}: {err_mHa:.3f} mHa vs {doi}"
```

---

## 10.7 Classical baselines — assume the referee thinks yours is weak

A quantum-chemistry referee's default hypothesis is that you compared against a straw man. Pre-empt it. **Every** quantum result needs these alongside it, with wall-clock:

| Baseline | Tool | Why it must be there |
|---|---|---|
| HF | PySCF `scf` | Establishes the correlation energy scale |
| MP2 | PySCF `mp` | Cheap correlation reference |
| CCSD(T) | PySCF `cc` | The "gold standard" — and it *fails* on strongly correlated heme, which is your point |
| CASSCF | PySCF `mcscf` | Static correlation, same active space |
| NEVPT2 | PySCF `mrpt` | Dynamic correlation on top of CASSCF (PySCF-native; CASPT2 requires OpenMolcas) |
| **DMRG** | `block2` | **The critical one.** Near-exact for these active spaces and the real competitor to any quantum claim |
| AFQMC | `ipie` | Independent high-accuracy cross-check |
| FCI | PySCF `fci` | Where tractable (≤ CAS(8,8)-ish) — the exact answer |

Report a bond-dimension convergence study for DMRG. A quantum-advantage claim against an unconverged DMRG calculation will not survive review.

---

## 10.8 Engage the skeptics — this is mandatory, not optional

**Lee et al. (2023), "Evaluating the evidence for exponential quantum advantage in ground-state quantum chemistry", *PRX Quantum* 4, 020329** argues that the case for exponential advantage in ground-state chemistry is substantially weaker than commonly claimed — that classical heuristics are stronger than assumed and the required state-preparation overlap degrades with system size.

A paper in this space that does not engage with it reads as unaware of its own field. Your Discussion section must address:

1. **State-preparation overlap.** What is the HF (or CASSCF) overlap with the true ground state for your KatG active space, and how does it scale as you enlarge the space? Compute and report it — this is the crux of the Lee et al. argument and it is directly measurable.
2. **Classical competitiveness.** Where does DMRG stop being feasible for this system, and at what bond dimension?
3. **The crossover estimate.** At what active-space size would the quantum approach plausibly win, and what hardware does §10.5.8 say that needs?

**A rigorously obtained negative result is a strong paper.** "For the KatG heme centre, DMRG remains competitive up to CAS(x,y), and the fault-tolerant resource requirement for the quantum approach is N Toffolis, implying hardware era Z" is more useful to the field — and more likely to be cited — than another optimistic small-molecule demonstration.

**Core bibliography to work from:** Peruzzo et al. 2014 *Nat. Commun.*; Kandala et al. 2017 *Nature*; Bravyi et al. 2017 (tapering); Sayfutyarova et al. 2017 *JCTC* (AVAS); Grimsley et al. 2019 *Nat. Commun.* (ADAPT-VQE); Tang et al. 2021 *PRX Quantum* (qubit-ADAPT); Cao et al. 2019 *Chem. Rev.*; Reiher et al. 2017 *PNAS* (FeMoco); von Burg et al. 2021 *Sci. Adv.*; Lee et al. 2021 *PRX Quantum* (tensor hypercontraction); Goings et al. 2022 *PNAS* (P450); Tilly et al. 2022 *Phys. Rep.* (VQE review); Lee et al. 2023 *PRX Quantum* (the skeptical analysis); Temme et al. 2017 *PRL* (ZNE); Nation et al. 2021 *PRX Quantum* (M3).

Verify every DOI before submission. This audit found no fabricated citations in the existing docs — keep that record intact.

---

## 10.9 Paper structure, figures, and tables

**Title (working):** *Active-space electronic structure of the M. tuberculosis KatG heme centre: ADAPT-VQE benchmarked against DMRG, with fault-tolerant resource estimates*

| Section | Content |
|---|---|
| 1. Introduction | INH activation mechanism; why heme is strongly correlated; why this is a quantum-algorithm testbed |
| 2. Methods | Cluster model construction; AVAS active-space selection; mapping + tapering; ansätze; optimizer; noise model; classical references |
| 3. Validation | The full ladder, rungs 1–6, with the chemical-accuracy line |
| 4. Results | KatG WT vs S315T; spin-state gaps; activation-coordinate scan |
| 5. Resource estimates | Toffoli/logical-qubit counts; physical-qubit and runtime projections |
| 6. Discussion | Explicit engagement with Lee et al. 2023; overlap scaling; DMRG crossover; honest limits |
| 7. Data availability | Zenodo DOI, container image, seeds, manifests |

**Figures**
1. Cluster model + active-space orbital plots (Fe 3d / porphyrin π), with occupations.
2. Validation ladder — error in mHa vs system, chemical-accuracy line shaded, error bars over 5 seeds.
3. N₂ dissociation curve: VQE vs CASSCF vs CCSD(T) vs FCI — CCSD(T) visibly failing.
4. ADAPT-VQE convergence: energy and operator count vs iteration, mean ± SD.
5. Noise study: unmitigated → ZNE → ZNE + readout, vs exact.
6. Qubit count before/after tapering, and CNOT count vs active-space size.
7. Resource estimates plotted against the FeMoco and P450 anchors.
8. Spin-state energetics, WT vs S315T.

**Tables**
1. Active-space composition with orbital indices, occupations, symmetries.
2. Qubit/gate/parameter counts per ansatz per system.
3. VQE vs every classical baseline, with wall-clock.
4. DMRG bond-dimension convergence.
5. Resource estimates under stated surface-code assumptions.

---

## 10.10 Timeline and staffing

| Phase | Duration | Deliverable |
|---|---|---|
| 0 | 2 weeks | WSL2/Linux environment; PySCF + block2 + OpenFermion installed and smoke-tested; hardware secured |
| 1 | 4 weeks | Ladder rungs 1–3 (H₂, LiH, BeH₂) passing in CI against published references |
| 2 | 4 weeks | Rungs 4–5 (N₂, H₂O stretch); ADAPT-VQE working; AVAS pipeline |
| 3 | 6 weeks | Classical reference stack: CASSCF, NEVPT2, CCSD(T), DMRG with convergence study |
| 4 | 6 weeks | Rung 6 — Fe-porphyrin model vs DMRG |
| 5 | 6 weeks | KatG cluster model, WT and S315T; noise + mitigation study |
| 6 | 4 weeks | Resource estimates; overlap-scaling analysis |
| 7 | 4 weeks | Writing, figures, Zenodo artifact, internal review |
| | **~9 months** | |

**Skills required — be honest about this.** The Qiskit code is the easy part. The gate is **CASSCF/active-space expertise**: choosing an active space, diagnosing convergence failures, and knowing when a multireference result is wrong. If nobody on the project has done a CASSCF calculation on a transition-metal complex before, budget a collaborator or an advisor with that background. This is the most common reason projects of this shape stall at rung 6.

---

## 10.11 What this buys — the 9.0 score arithmetic

Continuing the weighting in `audit_summary.md` §9.1 (scientific validity ×0.30, reproducibility ×0.25, documentation ×0.15, code quality ×0.10, software engineering ×0.10, maintainability ×0.05, novelty ×0.05):

| Dimension | After Lane B (7.0) | After Lane A | Why |
|---|---|---|---|
| Scientific validity | 6.5 | **9.5** | Real Hamiltonians, validated ladder, strong baselines, skeptic engagement |
| Reproducibility | 8.5 | **9.5** | Container + Zenodo + seeds + manifests + reference assertions in CI |
| Documentation | 8.0 | **9.0** | Methods section at journal standard; data availability statement |
| Code quality | 7.5 | **8.5** | Property-based tests against published physics |
| Software engineering | 7.5 | **8.0** | Numerical CI on an HPC runner |
| Maintainability | 7.0 | **7.5** | Modular, but a larger surface |
| Novelty | 5.0 | **8.5** | First KatG active-space quantum study + resource estimates |
| **Weighted overall** | **7.2** | **9.1** | |

Scientific validity does the heavy lifting — it carries 0.30 weight and moves 3.0 points. Note that **novelty alone cannot get you there**: at weight 0.05, even a perfect 10 on novelty moves the total by ~0.25.

### Secondary contribution worth ~0.3 on its own

Calibrate the **QPU co-design module** (`simulation.py:858-1031`) against published IBM device parameters — predicted vs reported f_q, anharmonicity, T₁/T₂, and gate error. The physics is already correct; only four fudge factors (`g_mhz = 95.0·√…`, `pocket_t1_factor`, `e_1q ×1.45`, `e_2q ×2.2`) need fitting, and `eps_eff` should use the CPW expression rather than the ideal-microstrip approximation. A validated device-parameter model pairs naturally with §10.5.8's resource estimates: *here is what the algorithm needs, and here is what the hardware provides.* That is a complete, coherent story.

---

## 10.12 Risks — what could sink this

| Risk | Likelihood | Mitigation |
|---|---|---|
| Active-space selection is unstable; results shift with the choice | **High** | Report AVAS and NO-occupation selections side by side; publish the sensitivity analysis rather than hiding it |
| CASSCF fails to converge on the heme centre | High | Standard practice: stepwise orbital rotation, state-averaging, good initial guesses. This is where domain expertise is non-negotiable |
| DMRG beats VQE decisively at every tractable size | **Very high** | This is the expected outcome. Frame it as the result from the start — §10.8 |
| Statevector simulation runs out of memory beyond ~28 qubits | High | Matrix-product-state simulation; tapering; smaller active spaces; HPC allocation |
| The paper is scooped on the specific system | Medium | KatG specifically is not well covered; and the reframe is what carries the novelty, not the enzyme |
| Reviewers reject the drug-discovery framing | Medium | **Drop the drug-discovery framing.** Submit it as a quantum-chemistry methods paper with a TB motivation, not as a drug-discovery paper |

The last row is the most important. The web application is a fine artifact and can be cited as a companion tool — but it should not be the paper. **Two separate outputs: the tools paper from Lane B (JOSS/JOSE), and the methods paper from Lane A.** Trying to make one submission carry both is what produced the current situation.
