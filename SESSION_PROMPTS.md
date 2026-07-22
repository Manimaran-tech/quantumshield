# SESSION_PROMPTS.md — session kickoff prompts for the remediation plan

Companion to `fix.md`, `research_improvements.md`, `audit_summary.md` (audit of 2026-07-22).

**Read this first.** No single session reaches 9.1/10. That score requires ~9 months of research: converged CASSCF on a transition-metal centre, DMRG baselines with bond-dimension studies, and a real scientific result. A model can write the code; it cannot run the science for you, and it cannot supply the domain expertise flagged in `audit_summary.md` §10.5.

What these prompts do is keep each session on-plan, verified, and free of the failure modes the audit found.

**Order is not optional.** Lane B (P0 → P2) before Lane A (A0 → A6). Lane A on an unseeded, untested, unlicensed codebase produces numbers nobody — including you — can verify.

---

## 0. Session primer — paste at the top of EVERY session

```
CONTEXT
Repo: C:\Quantum\quantumshield  (QuantumShield — quantum/ML drug-discovery pipeline)
A full research audit was completed 2026-07-22. Read these three files before doing
anything else, in this order:
  1. audit_summary.md        — findings, scores, the two-lane remediation plan
  2. fix.md                  — ~90 findings with file:line; Part H has patch-level fixes
  3. research_improvements.md — §10 is the full quantum-chemistry (Lane A) plan

The audit found systemic fabrication: a molecule-independent Hamiltonian, an RL agent
that never learns, a post-hoc step that edited results when they lost to the baseline,
a docking score that rates ethanol above isoniazid, and benchmarks that print "PASSED"
as a string literal. Assume nothing in this repo is correct until you have executed it.

HARD RULES — these are what caused the audit findings; do not reintroduce them
1. NEVER invent a fallback value. If a computation fails, propagate a typed error.
   Do not substitute a plausible number, a canned molecule, or a default dict.
2. NEVER name a tool in code, comments, docstrings, logs, or UI text unless that tool
   actually executes in this repo. (Past offenders: AutoDock Vina, GROMACS, OpenMM,
   P2Rank, Qiskit Metal.)
3. NEVER print an unconditional success string. "PASSED", "converged", "[PROVED]",
   "[SUCCESS]" must sit behind a real comparison that can fail.
4. NEVER label synthetic data as measured. Any fabricated or sampled value carries
   is_synthetic=true through to the UI.
5. VERIFY BY EXECUTION, not assertion. Run the code and paste the real output. If you
   cannot run it, write "UNVERIFIED" explicitly. Do not report what you expect to happen.
6. CITE OR DELETE. Any scientific constant, formula, or threshold needs a citation with
   a DOI, or it does not ship.
7. Every result-producing change gets a regression test that FAILS on the old behaviour.
8. Seed everything. Echo seed + git SHA + config hash in every output payload.

SCOPE
Defensive, in-silico, simulation-only research. Nothing here concerns synthesis,
laboratory work, or clinical use.

TASK
<paste the phase prompt below>
```

---

## Lane B — 2.0 → 7.2 (~5 weeks). Do this first.

### P0 — Integrity pass (~1 day) · 2.0 → 3.8

```
Execute fix.md Part H.0 in full. This phase is almost entirely deletion — do not add
features, do not refactor beyond what each item requires.

1. H.0.1 Secrets. Strip the live key from the .env comment. Replace the hardcoded
   nvapi- literals in the five scratch/ files with os.environ["NVIDIA_API_KEY"] (raise
   if unset — no fallback). Add scratch/ to .gitignore. Then tell me, as a checklist I
   must action myself, exactly which credentials to revoke and where.
2. H.0.2 debug=False, bind 127.0.0.1, refuse to start the debugger on a non-loopback host.
3. H.0.3 Delete the "Lead Polishing" block, qrl_optimizer.py:2050-2084, entirely.
4. H.0.4 Remove every false tool attribution in app.py:651-694, generator.py:756,
   qrl_optimizer.py:462-463, app.py:763, test_drug_accuracy.py:61. Replace each string
   with an accurate description of what the code actually does.
5. H.0.5 Make PASSED/[SUCCESS]/[PROVED] conditional; exit non-zero on failure.
6. H.0.6 Rename measured_binding -> synthetic_binding; add is_synthetic + a note field;
   rename the /api/validation/wetlab route.
7. H.0.7 git add requirements.txt; add transformers; pip install pytest.

Line numbers are from the audit and will drift as you edit — match on the quoted code.
After each item, show me the diff. At the end, run the app and paste real startup output.
```

### P1 — Correctness and reproducibility (~1 week) · 3.8 → 6.3

```
Execute fix.md Part H.1, items H.1.1 through H.1.16, in order.

Gate for this phase, and you may not report it complete until this passes twice in a row:
    the determinism test in H.1.12 — identical inputs must produce byte-identical payloads.

Priority order if time is short:
  - H.1.1  empty SMILES accepted as a drug candidate  (verify with Chem.MolFromSmiles(""))
  - H.1.2  /simulate 500s on its own default (pathogen_name=None)
  - H.1.3  UnboundLocalError in three exception handlers
  - H.1.4  disease_info possibly unbound
  - H.1.6  never fabricate a pocket — raise TargetUnresolved instead
  - H.1.10 inverted fitness sign (weaker binding currently scores higher)
  - H.1.11 Hartree/kcal-per-mol unit error in the docking potential
  - H.1.12 seeds.py + provenance block
  - H.1.15 LICENSE + REINVENT NOTICE + model_card.md + SHA-256

Write a regression test for each that fails against the current code before your fix.
For H.1.11, the test is: isoniazid must outscore ethanol against the TB pocket. Paste
the before/after numbers.
```

### P2 — Published methods and infrastructure (~3 weeks) · 6.3 → 7.2 ✅

```
Execute fix.md Part H.2.

1. H.2.1 Replace every invented property model: RDKit sascorer (Ertl & Schuffenhauer
   2009), FilterCatalog for PAINS/Brenk/NIH, Lipinski.FractionCSP3. Delete all three
   divergent sa_score formulas and the retro_steps derivation. Allow Ro5's one
   permitted violation.
2. H.2.4 pytest suite, >=70% coverage on chem/quantum/rl; mock all network with
   `responses`; @pytest.mark.integration excluded by default.
3. GitHub Actions: ruff -> mypy -> pytest -> pip-audit -> gitleaks, plus a weekly
   integration job (that job is what catches external API drift like the dead PubChem
   property name and the 404 EMA endpoint).
4. Replace all 65 broad exception handlers with specific ones. No value substitution
   inside any except block.
5. Deduplicate: one rescale formula, one pathogen map, one toxicity block, one
   fetch_pubchem_smiles.
6. Write model_card.md, data_card.md per external source, and a Dockerfile.

Then re-verify against audit_summary.md §9.6 and produce the six required artifacts.
Report the six as evidence; do not restate the score without them.
```

---

## Lane A — 7.2 → 9.1 (~9 months). Only after Lane B.

Two blockers to clear before A0, both from `audit_summary.md` §10.5:
- **PySCF has no native Windows support.** Move to WSL2 or Linux.
- **A CASSCF-experienced collaborator.** This is the real bottleneck, not the Qiskit code.

### A0 — Environment and scaffolding (2 weeks)

```
Set up the Lane A environment per research_improvements.md §10.4.

- WSL2/Linux venv, separate requirements-qc.txt. Do NOT merge these deps into the web
  app's requirements — the Flask/React side must stay installable on Windows without a
  quantum-chemistry toolchain.
- Install: pyscf, qiskit-nature, qiskit-aer, openfermion, openfermionpyscf, block2, mthree.
- Create the src/quantumshield_qc/ package layout from §10.5.1.
- Delete everything in §10.3 (get_molecular_hamiltonian, calculate_coordinate_energy,
  solve_huckel_gap, the hardcoded HOMO table, the synthetic noise/convergence, run_actual_vqe,
  scratch_huckel_test.py). Do NOT delete simulation.py:858-1031 — the transmon physics is
  correct and becomes a secondary contribution.
- Smoke test: PySCF RHF on H2 at 0.735 Angstrom. Paste the real energy and compare it to
  the literature value.

Report installed versions and the smoke-test output. If any install fails on this
platform, say so — do not work around it with a stub.
```

### A1 — Validation ladder rungs 1–3 (4 weeks)

```
Implement research_improvements.md §10.5.2-10.5.6 and pass ladder rungs 1-3 (§10.6).

- electronic_structure/driver.py: PySCFDriver -> ElectronicStructureProblem, with a
  basis ladder STO-3G -> 6-31G* -> cc-pVDZ and a reported convergence study.
- quantum/hamiltonian.py: ParityMapper(num_particles) + problem.get_tapered_mapper().
  Report qubit counts before and after tapering as a table.
- quantum/ansatz.py: HartreeFock + UCCSD.
- quantum/solver.py: SLSQP + ParamShiftEstimatorGradient, maxiter >= 30*n_params,
  seeded initial_point near HF. (The audit measured 68-146 mHa error because the old
  code gave COBYLA 40 iterations for 64 parameters.)

GATE: H2/STO-3G at 0.735 A must land within 1.6 mHa of the published FCI value, then
LiH and BeH2 across their full dissociation curves. Encode every reference in
benchmarks/references.yaml WITH ITS DOI and assert against it in CI.

Report error in millihartree, over >=5 seeds, mean +/- SD. Do not proceed past a failing
rung — tell me it failed and why.
```

### A2 — Rungs 4–5, ADAPT-VQE, AVAS (4 weeks)

```
Add ADAPT-VQE (Grimsley et al. 2019) and AVAS active-space selection
(Sayfutyarova et al. 2017), then pass ladder rungs 4-5.

Rung 4 is N2 triple-bond breaking and it is the phase gate. It is the multireference
stress test — single-reference methods fail there by construction. If the method cannot
break N2 correctly it cannot say anything about a heme centre, and a referee knows this.
Target: non-parallelity error < 5 mHa vs CASSCF/NEVPT2.

For AVAS: report the selected orbital indices, their occupations, and their symmetry
labels. Cross-check against natural-orbital-occupation selection and show the result is
stable under the choice — active-space sensitivity is the first thing a referee probes.

Also add quantum/noise.py: NoiseModel.from_backend(FakeSherbrooke), ZNE, mthree readout
mitigation. Report unmitigated -> ZNE -> ZNE+readout against exact.
```

### A3 — Classical baselines (6 weeks)

```
Build the classical reference stack per research_improvements.md §10.7: HF, MP2,
CCSD(T), CASSCF, NEVPT2, DMRG (block2), AFQMC (ipie), and FCI where tractable.

DMRG is the one that matters — it is the real competitor to any quantum claim, not
CCSD(T). Produce a bond-dimension convergence study; an advantage claim measured against
an unconverged DMRG calculation will not survive review.

Report every method with wall-clock alongside the energy. Expect CCSD(T) to fail on
strongly correlated cases — that failure is a result, so plot it.
```

### A4 — Fe-porphyrin, rung 6 (6 weeks)

```
Ladder rung 6: an Fe-porphyrin model system, no protein.
Target: spin-state gaps within 5 mHa of the DMRG reference.

Expect CASSCF convergence trouble. Standard remedies: stepwise orbital rotation,
state-averaging, careful initial guesses. If it will not converge, say so and show me
the diagnostics — do not tune numbers until they look reasonable.

Report the active space you settled on, why, and how sensitive the result is to it.
```

### A5 — KatG WT and S315T, rungs 7–8 (6 weeks)

```
Build the KatG heme cluster model (structures/katg_heme.py) and run the full pipeline
for wild type and the S315T variant. This is the scientific result.

Context: isoniazid is a prodrug; KatG (heme b) oxidizes it to the isonicotinoyl radical,
which couples to NAD+ to form the INH-NAD adduct that inhibits InhA. katG S315T impairs
the ACTIVATION step, not binding.

Report spin-state energetics WT vs S315T, reproducible across >=5 seeds, with the
active-space sensitivity documented. Cite the structural source for the cluster model.
```

### A6 — Resource estimates and writing (8 weeks)

```
1. quantum/resources.py per §10.5.8: openfermion.resource_estimates double-factorization
   costing. Report logical qubits, Toffoli/T counts, and — with the physical error rate
   stated — implied physical qubits and runtime. Place the KatG number against the FeMoco
   (Reiher 2017) and P450 (Goings 2022) anchors.
2. Compute the HF/CASSCF overlap with the true ground state and its scaling as the active
   space grows. This is the crux of Lee et al. 2023 (PRX Quantum 4, 020329) and it is
   directly measurable — the Discussion must engage it head on.
3. Calibrate the transmon module (simulation.py:858-1031) against published IBM device
   parameters: predicted vs reported f_q, anharmonicity, T1/T2, gate error. Fit the four
   fudge factors; switch eps_eff to the CPW expression.
4. Draft the paper per §10.9: 8 figures, 5 tables, and the Zenodo artifact.

If DMRG beats VQE at every tractable size — the expected outcome — frame that as the
result. A rigorous negative result with a crossover estimate is more useful and more
citable than another optimistic demonstration. Do not bury it.
```

---

## Prompts that will make things worse

Avoid these. Each maps to a specific finding in `fix.md`.

| Do not say | Why | Instead |
|---|---|---|
| "Make the VQE results look better" | Produced the tuned sinusoidal noise (A13) | "Fix the optimizer budget and report the FCI gap in mHa" |
| "Make sure the pipeline never errors out" | Produced the fabricated-fallback pattern throughout | "Return a typed error the UI can render" |
| "Make our candidate beat the reference drug" | Produced the Lead Polishing block (A5) | "Report both, with the comparison unconditioned" |
| "Add ADMET predictions" | Produced six invented linear formulas (A23) | "Wire up RDKit sascorer and FilterCatalog, with citations" |
| "Get the tests passing" | Produced zero-assertion print scripts (F1) | "Write a test that fails on the current behaviour, then fix it" |
| "Speed up the audit, skip verification" | The 2026-07-19 static audit missed the dead PubChem resolver, the broken IBM path, and the non-determinism | "Execute it and paste the real output" |

---

## Per-session close-out

End every session with:

```
Summarize: what you changed, what you verified BY EXECUTION (paste the output), what
remains UNVERIFIED, and which phase gate is now open or still closed. Then update
audit_summary.md §5 ONLY if you produced the six artifacts required by §9.6. If you did
not, say the score is unchanged and why.
```

That last clause is the point of this file. The project reached 2.0/10 because numbers were asserted rather than measured. Do not let the remediation repeat the pattern.
