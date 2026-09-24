/* ============================================================
   QuantumShield — Scene content + inline SVG art
   18 scenes (0–17). Engine renders them into #deck.
   Optional raster images go in /images/<file> and lazy-load
   over the SVG art when present (see MANIFEST.md).
   ============================================================ */

// ---------- SVG art helpers (compact, premium motifs) ----------
const svg = (inner, vb = '0 0 100 100') =>
  `<svg viewBox="${vb}" fill="none" stroke-linecap="round" stroke-linejoin="round">${inner}</svg>`;

const helixArt = `
  <g stroke-width="1.3">
    <path class="svg-teal" d="M34 10 Q66 25 34 40 Q2 55 34 70 Q66 85 34 98" />
    <path class="svg-grey" d="M66 10 Q34 25 66 40 Q98 55 66 70 Q34 85 66 98" />
  </g>
  <g stroke-width="1" opacity=".6">
    <line class="svg-grey" x1="40" y1="18" x2="60" y2="18"/>
    <line class="svg-grey" x1="38" y1="30" x2="62" y2="30"/>
    <line class="svg-grey" x1="36" y1="42" x2="64" y2="42"/>
    <line class="svg-grey" x1="36" y1="58" x2="64" y2="58"/>
    <line class="svg-grey" x1="38" y1="70" x2="62" y2="70"/>
    <line class="svg-grey" x1="40" y1="82" x2="60" y2="82"/>
  </g>
  <g>
    <circle class="svg-fill-teal" cx="34" cy="18" r="2.4"/><circle class="svg-fill-grey" cx="66" cy="18" r="2.4"/>
    <circle class="svg-fill-teal" cx="34" cy="42" r="2.4"/><circle class="svg-fill-grey" cx="66" cy="42" r="2.4"/>
    <circle class="svg-fill-teal" cx="34" cy="70" r="2.4"/><circle class="svg-fill-grey" cx="66" cy="70" r="2.4"/>
  </g>`;

const orbitArt = ``;

const latticeArt = `
  <g stroke-width="1" opacity=".7">
    <line class="svg-grey" x1="20" y1="20" x2="80" y2="20"/>
    <line class="svg-grey" x1="20" y1="50" x2="80" y2="50"/>
    <line class="svg-grey" x1="20" y1="80" x2="80" y2="80"/>
    <line class="svg-grey" x1="20" y1="20" x2="20" y2="80"/>
    <line class="svg-grey" x1="50" y1="20" x2="50" y2="80"/>
    <line class="svg-grey" x1="80" y1="20" x2="80" y2="80"/>
    <line class="svg-teal" x1="20" y1="20" x2="80" y2="80" opacity=".4"/>
    <line class="svg-teal" x1="80" y1="20" x2="20" y2="80" opacity=".4"/>
  </g>
  <g>
    <circle class="svg-fill-teal" cx="20" cy="20" r="3"/><circle class="svg-fill-teal" cx="50" cy="20" r="3"/>
    <circle class="svg-fill-teal" cx="80" cy="20" r="3"/><circle class="svg-fill-grey" cx="20" cy="50" r="3"/>
    <circle class="svg-fill-teal" cx="50" cy="50" r="4"/><circle class="svg-fill-grey" cx="80" cy="50" r="3"/>
    <circle class="svg-fill-teal" cx="20" cy="80" r="3"/><circle class="svg-fill-teal" cx="50" cy="80" r="3"/>
    <circle class="svg-fill-teal" cx="80" cy="80" r="3"/>
  </g>`;

const waveArt = `
  <g stroke-width="1.4">
    <polyline class="svg-teal" points="8,78 22,60 36,66 50,40 64,48 78,18 92,30"/>
  </g>
  <g stroke-width="1" opacity=".5">
    <polyline class="svg-grey" points="8,86 22,80 36,82 50,72 64,74 78,60 92,62"/>
  </g>
  <g>
    <circle class="svg-fill-teal" cx="22" cy="60" r="2"/><circle class="svg-fill-teal" cx="50" cy="40" r="2"/>
    <circle class="svg-fill-teal" cx="78" cy="18" r="2.6"/>
  </g>`;

const flowArt = `
  <g stroke-width="1.1">
    <rect class="svg-teal" x="6" y="6" width="22" height="14" fill="rgba(19,138,165,.05)"/>
    <rect class="svg-grey" x="39" y="6" width="22" height="14" fill="none"/>
    <rect class="svg-grey" x="72" y="6" width="22" height="14" fill="none"/>
    <rect class="svg-teal" x="39" y="43" width="22" height="14" fill="rgba(19,138,165,.05)"/>
    <rect class="svg-teal" x="6" y="80" width="22" height="14" fill="rgba(19,138,165,.05)"/>
    <rect class="svg-grey" x="39" y="80" width="22" height="14" fill="none"/>
    <rect class="svg-grey" x="72" y="80" width="22" height="14" fill="none"/>
    <path class="svg-grey" d="M28 13 H39 M61 13 H72"/>
    <path class="svg-teal" d="M50 20 V43 M50 57 V80"/>
    <path class="svg-grey" d="M18 20 V80 M82 20 V80" opacity=".4"/>
    <path class="svg-teal" d="M17 50 H39 M61 50 H83"/>
    <circle class="svg-fill-teal" cx="50" cy="50" r="3"/>
  </g>`;

const chipArt = `
  <g stroke-width="1.1">
    <rect class="svg-teal" x="30" y="30" width="40" height="40" fill="rgba(19,138,165,.06)"/>
    <g class="svg-grey">
      <line x1="30" y1="38" x2="22" y2="38"/><line x1="30" y1="46" x2="22" y2="46"/>
      <line x1="30" y1="54" x2="22" y2="54"/><line x1="30" y1="62" x2="22" y2="62"/>
      <line x1="70" y1="38" x2="78" y2="38"/><line x1="70" y1="46" x2="78" y2="46"/>
      <line x1="70" y1="54" x2="78" y2="54"/><line x1="70" y1="62" x2="78" y2="62"/>
      <line x1="38" y1="30" x2="38" y2="22"/><line x1="46" y1="30" x2="46" y2="22"/>
      <line x1="54" y1="30" x2="54" y2="22"/><line x1="62" y1="30" x2="62" y2="22"/>
      <line x1="38" y1="70" x2="38" y2="78"/><line x1="46" y1="70" x2="46" y2="78"/>
      <line x1="54" y1="70" x2="54" y2="78"/><line x1="62" y1="70" x2="62" y2="78"/>
    </g>
    <circle class="svg-fill-teal" cx="50" cy="50" r="6"/>
    <circle class="svg-fill-grey" cx="42" cy="42" r="2"/><circle class="svg-fill-grey" cx="58" cy="42" r="2"/>
    <circle class="svg-fill-grey" cx="42" cy="58" r="2"/><circle class="svg-fill-grey" cx="58" cy="58" r="2"/>
  </g>`;

const apiArt = `
  <g stroke-width="1.2">
    <circle class="svg-teal" cx="22" cy="50" r="10" fill="rgba(19,138,165,.06)"/>
    <circle class="svg-grey" cx="78" cy="30" r="9" fill="none"/>
    <circle class="svg-grey" cx="78" cy="70" r="9" fill="none"/>
    <path class="svg-teal" d="M31 46 L69 32"/><path class="svg-teal" d="M31 54 L69 68"/>
    <text x="22" y="54" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="8" fill="3e4145">QS</text>
  </g>`;

// ---------- Module motifs (for the Modules reveal-grid scene) ----------
const lstmArtMod = `
  <g stroke-width="1.2">
    <rect class="svg-teal" x="8" y="44" width="14" height="14" fill="rgba(19,138,165,.08)"/>
    <rect class="svg-grey" x="30" y="40" width="14" height="22" fill="none"/>
    <rect class="svg-grey" x="52" y="36" width="14" height="30" fill="none"/>
    <rect class="svg-teal" x="74" y="32" width="14" height="38" fill="rgba(19,138,165,.08)"/>
    <circle class="svg-fill-grey" cx="15" cy="51" r="2"/>
    <path class="svg-teal" d="M22 51 H30 M44 51 H52 M66 51 H74"/>
  </g>`;

const foldArtMod = `
  <g stroke-width="1.2">
    <path class="svg-teal" d="M20 20 Q50 10 80 20 Q90 50 80 80 Q50 90 20 80 Q10 50 20 20Z" fill="rgba(19,138,165,.05)"/>
    <path class="svg-grey" d="M28 36 Q50 30 72 36 M28 64 Q50 70 72 64" opacity=".6"/>
    <circle class="svg-fill-teal" cx="50" cy="50" r="3.4"/>
    <circle class="svg-fill-grey" cx="34" cy="40" r="2"/><circle class="svg-fill-grey" cx="66" cy="40" r="2"/>
    <circle class="svg-fill-grey" cx="34" cy="60" r="2"/><circle class="svg-fill-grey" cx="66" cy="60" r="2"/>
  </g>`;

const dockArtMod = `
  <g stroke-width="1.2">
    <ellipse class="svg-grey" cx="60" cy="62" rx="30" ry="13" opacity=".5"/>
    <ellipse class="svg-grey" cx="60" cy="62" rx="20" ry="8" opacity=".5"/>
    <line class="svg-teal" x1="30" y1="28" x2="42" y2="40"/>
    <line class="svg-teal" x1="42" y1="40" x2="38" y2="54"/>
    <circle class="svg-fill-teal" cx="30" cy="28" r="3"/><circle class="svg-fill-teal" cx="42" cy="40" r="3"/>
    <circle class="svg-fill-grey" cx="38" cy="54" r="2.4"/>
    <circle class="svg-fill-teal" cx="60" cy="62" r="2.4"/>
  </g>`;

const admetArtMod = `
  <g stroke-width="1.2">
    <polygon class="svg-grey" points="34,38 48,30 62,38 62,54 48,62 34,54" fill="none"/>
    <circle class="svg-fill-teal" cx="48" cy="46" r="2.4"/>
    <polygon class="svg-teal" points="78,44 86,40 86,52 78,58 70,52 70,40" fill="rgba(19,138,165,.08)"/>
    <line class="svg-grey" x1="18" y1="74" x2="84" y2="74" opacity=".35" stroke-dasharray="3 3"/>
  </g>`;

const modMotifs = {
  vqe: chipArt,
  lstm: lstmArtMod,
  fold: foldArtMod,
  dock: dockArtMod,
  admet: admetArtMod,
  price: apiArt
};

// ---------- Scene definitions ----------
const SCENES = [
  // 00 — Hero (Older style & color with updated detection & discovery information)
  {
    id: 'hero', stacked: true,
    eyebrow: ['Quantum Clinical AI', 'Preclinical Bio-Simulation', ''],
    title: 'QUANTUMSHIELD',
    lede: `We pair multi-modality diagnostic vision (Chest X-Ray, Retinal OCT, Dermatoscopy, Histopathology) with <strong>Parameterized Quantum Circuits (VQC)</strong> to detect sub-visual pathology at Stage 0 — and solve the active electronic space of mutated pathogen targets to compress novel drug discovery from <strong>5–7 years to 12–24 hours</strong>.`,
    scrollHint: 'SCROLL FOR MORE INFORMATION ↓'
  },
  // 01 — Who We Are (Restored with updated clinical + quantum vision)
  {
    id: 'who', num: '01', img: 'who-we-are.png',
    eyebrow: ['Who We Are', 'Unified Clinical & Quantum Platform', ''],
    title: 'We render diagnostic vision & molecules <span class="accent">in qubits</span>',
    lede: `QuantumShield is a unified clinical AI and hybrid <strong>QM/MM</strong> bio-simulation platform. We pair multi-modality diagnostic vision (Chest Radiography, Retinal OCT, Dermatoscopy, Histopathology) with <strong>Variational Quantum Classifiers (VQC)</strong> and VQE chemistry — detecting sub-visual pathology at Stage 0 and synthesizing targeted atomic countermeasures in 12–24 hours instead of a decade.`,
    facts: [
      ['Early Detection', '<b>Chest X-Ray</b> (98.8%), <b>Retinal OCT</b>, <b>Dermatoscopy</b>, <b>Histopathology</b>'],
      ['Quantum Core', '<b>VQC Anomaly Vision</b> + <b>Variational Quantum Eigensolver (VQE)</b>'],
      ['Deployed on', 'Local edge neural runtime <i>and</i> physical IBM Quantum QPUs'],
    ]
  },
  // 02 — What We're Doing
  {
    id: 'what', num: '02', img: 'what-we-do.png', dual: 'left',
    eyebrow: ['What We\'re Doing', 'The Central Thesis', ''],
    title: 'Years → Hours. Millions → <span class="accent">Cost of a run</span>',
    lede: `Traditional preclinical R&D spends <strong>$800M–$2.6B and 5–7 years</strong> per drug. Our unified diagnostic-to-countermeasure pipeline resolves verified therapeutic candidates in <strong>12–24 hours at ~$5M–$10M</strong> by computing thermodynamic ground-truth (ΔG, K<sub>d</sub>) directly from diagnostic findings.`,
    facts: [
      ['10⁶⁰', 'Drug-like molecules in chemical space — classically intractable to enumerate'],
      ['12–24h', 'From clinical detection to verified atomic countermeasure candidate'],
      ['$800M↑', 'Vs. our run-cost reduction of roughly two orders of magnitude'],
    ]
  },
  // 03 — Early Detection Paradigm
  {
    id: 'detect-overview', num: '03', img: 'detection-hero.png',
    eyebrow: ['Clinical AI', 'Multi-Modality Diagnostics', ''],
    title: 'Catching Pathology <span class="accent">Before Symptoms Emerge</span>',
    lede: `Traditional medicine detects disease only after macro-scale tissue destruction triggers clinical symptoms. QuantumShield combines deep convolutional vision with parameterized quantum circuits to detect sub-visual cellular, retinal, and pulmonary anomalies at Stage 0 — long before irreversible clinical progression.`,
    facts: [
      ['Four Modalities', '<b>Chest X-Ray</b>, <b>Retinal OCT</b>, <b>Dermatoscopy</b>, <b>Histopathology</b>'],
      ['Operating Point', 'Calibrated Platt scaling for zero-miss clinical sensitivity'],
      ['Explainability', 'Grad-CAM saliency heatmaps highlighting exact anatomical lesion margins'],
    ]
  },
  // 04 — Pulmonary Radiography / CXR
  {
    id: 'detect-cxr', num: '04', img: 'detection-histo.png', dual: 'left',
    eyebrow: ['Modality I', 'Pulmonary Radiography (CXR)', ''],
    title: 'TorchXRayVision + DenseNet-121 <span class="accent">at 98.8% Sensitivity</span>',
    lede: `Pretrained on over 828,000 hospital radiographs via <strong>TorchXRayVision DenseNet-121</strong>, our pulmonary engine resolves pediatric and adult pneumonia, pleural effusion, and lung consolidation in 1.2 seconds, outputting anatomical risk logits calibrated via Platt temperature scaling.`,
    facts: [
      ['Backbone', 'DenseNet-121 · 828K+ hospital X-rays (TorchXRayVision)'],
      ['Calibration', 'logit_calibrated = (raw_logit + 6.54) / 0.552'],
      ['Performance', '98.78% sensitivity on acute pediatric & viral pneumonia'],
    ]
  },
  // 05 — Retinal OCT Cross-Sections
  {
    id: 'detect-oct', num: '05', img: 'detection-oct.png',
    eyebrow: ['Modality II', 'Optical Coherence Tomography', ''],
    title: 'Retinal OCT: <span class="accent">Sub-Micron Tissue Cross-Sections</span>',
    lede: `Non-invasive optical coherence tomography captures the 10 micro-layers of the neurosensory retina at 3–5 µm axial optical resolution. Our model segments the fovea, detecting <strong>Diabetic Macular Edema (DME)</strong>, <strong>Choroidal Neovascularization (CNV)</strong>, and <strong>Drusen</strong> before irreversible vision impairment.`,
    facts: [
      ['Resolution', '3–5 µm axial optical resolution across retinal layers'],
      ['Target Pathology', 'Diabetic Macular Edema (DME), Sub-retinal fluid, Drusen'],
      ['Feature Engine', '3-channel aligned DenseNet feature embeddings'],
    ]
  },
  // 06 — Dermatoscopy & Cellular Histopathology
  {
    id: 'detect-derm', num: '06', img: 'detection-derm.png', dual: 'left',
    eyebrow: ['Modality III & IV', 'Surface Lesions & Tissue Biopsy', ''],
    title: 'From Epiluminescent Lesions <span class="accent">to Biopsy Margins</span>',
    lede: `From macroscopic epiluminescence dermoscopy (evaluating ABCD pigment networks for early Melanoma discrimination) to microscopic histopathology biopsy tiles (segmenting adenocarcinoma gland margins across the NCT-CRC-100K cohort), cellular abnormalities are identified at single-cell resolution.`,
    facts: [
      ['Dermatoscopy', 'HAM10000 cohort · Epiluminescence ABCD lesion scoring'],
      ['Histopathology', 'NCT-CRC-100K colorectal adenocarcinoma gland margins'],
      ['Cellular Gating', 'Automated nuclear contouring and dysplasia grading'],
    ]
  },
  // 07 — Quantum Vision & VQC
  {
    id: 'detect-vqc', num: '07', img: 'detection-vqc.png',
    eyebrow: ['Quantum Machine Learning', 'Parameterized Quantum Circuits', ''],
    title: 'Quantum Vision (QCAD): <span class="accent">Hilbert Space Anomaly Mapping</span>',
    lede: `When classical deep learning encounters subtle, atypical tissue presentations, QuantumShield projects deep feature vectors into an $N$-qubit Hilbert space via <strong>Angle Embedding</strong> ($R_y$ rotations + $CZ$ entanglement). The <strong>Variational Quantum Classifier (VQC)</strong> discovers complex non-linear decision boundaries that classical linear SVMs cannot resolve.`,
    formula: { cap: 'Quantum statevector angle embedding', body: '|ψ(x)⟩ = ⨂_{j=1}^N [cos(x_j/2)|0⟩ + sin(x_j/2)|1⟩]  →  U(θ)|ψ(x)⟩' },
    facts: [
      ['Embedding', 'Multi-qubit Angle & Amplitude embedding into 2ᴺ space'],
      ['Ansatz', 'Hardware-efficient TwoLocal (RY + CZ entanglement layers)'],
      ['Measurement', 'Pauli-Z expectation values ⟨Z₀⟩ → diagnostic probability'],
    ]
  },
  // 08 — Unified Loop: From Detection to Countermeasure
  {
    id: 'bridge', num: '08', img: 'theory.png', dual: 'left',
    eyebrow: ['The Paradigm Shift', 'Diagnosis → Countermeasure', ''],
    title: 'From Diagnostic Scan <span class="accent">to Atomic Countermeasure</span>',
    lede: `Early detection flags the biological threat; quantum simulation solves it. When a pathogen (*M. tuberculosis*, *SARS-CoV-2*) or mutated oncogenic receptor is detected, its UniProt sequence and AlphaFold 3D pocket are resolved immediately, initiating automated ligand generation and VQE binding energy optimization.`,
    facts: [
      ['Turnaround', '< 24 hours from diagnostic scan to verified candidate'],
      ['Pathogen Presets', 'TB InhA, COVID-19 M_pro, Salmonella FabH, EGFR mutations'],
      ['Thermodynamics', 'Exact interatomic binding energy (ΔG) and inhibition (Kd)'],
    ]
  },
  // 09 — 6-Layer Pipeline overview
  {
    id: 'pipeline', num: '09', stacked: true,
    eyebrow: ['Architecture', 'The 6-layer pipeline', ''],
    title: 'Input → Verified Candidate & Report',
    lede: `Every countermeasure flows sequentially across six logical layers.`,
    layers: [
      ['L1', 'Input & Pathogen Resolution', 'NVIDIA NIM + AlphaFold', 'Resolves target / UniProt / seed SMILES'],
      ['L2', 'Generative Chemistry & QRL', 'SMILES LSTM + PyTorch RL', 'Samples & optimizes candidate structures'],
      ['L3', 'Conformation & 3D Docking', 'RDKit · MMFF94', 'Relaxes & aligns molecule to pocket'],
      ['L4', 'Quantum Mechanics & VQE', 'Qiskit / IBM QPU', 'Maps orbitals → qubits, solves ground state'],
      ['L5', 'ADMET & DNA Validation', 'RDKit + Fsp³', 'Drug-likeness & mutagenicity gates'],
      ['L6', 'Reporting & Cost', 'MD sim + live price APIs', 'Assay, NADAC/INR pricing, PDF docs'],
    ],
    art: () => svg(flowArt)
  },
  // 10 — Layer 1
  {
    id: 'l1', num: '10', img: 'layer-1.png', dual: 'left',
    eyebrow: ['Layer 1', 'Input & Pathogen Resolution', ''],
    title: 'Resolve the target receptor. <span class="accent">Parse the pocket.</span>',
    lede: `We query the <strong>NVIDIA NIM</strong> <code>meta/llama-3.1-8b-instruct</code> model to extract the target receptor, its <strong>UniProt ID</strong>, and a seed SMILES, then pull the predicted <strong>3D AlphaFold</strong> structure and parse the 10 closest active-site residues for docking.`,
    facts: [
      ['LLM', 'NVIDIA NIM · llama-3.1-8b-instruct (NVIDIA_API_KEY)'],
      ['Structures', 'EBI AlphaFold API · PDB parse → pocket residues'],
      ['Failover', 'UniProt KB primary-accession + search API'],
    ]
  },
  // 11 — Layer 2
  {
    id: 'l2', num: '11', img: 'layer-2.png',
    eyebrow: ['Layer 2', 'Generative Chemistry & QRL', ''],
    title: 'Generate, <span class="accent">score</span>, reinforce.',
    lede: `A character-level <strong>SMILES LSTM</strong> (AstraZeneca REINVENT lineage) samples raw candidate strings token-by-token. A <strong>PyTorch QRL agent</strong> computes policy-gradient updates against a reward blending drug-likeness (QED), synthetic accessibility (SA), and VQE binding affinity.`,
    facts: [
      ['Model', '3-layer LSTM · embedding 256 · hidden 512'],
      ['Policy', 'PyTorch QRL · policy-gradient optimization'],
      ['Reward', 'QED + SA Score + VQE binding energy'],
    ]
  },
  // 12 — Layer 3
  {
    id: 'l3', num: '12', img: 'layer-3.png', dual: 'left',
    eyebrow: ['Layer 3', 'Conformation & 3D Docking', ''],
    title: 'Relax to lowest energy. <span class="accent">Align to pocket.</span>',
    lede: `RDKit builds <strong>3D conformers</strong> of each generated molecule and relaxes bond lengths, angles, and torsions with the <strong>MMFF94</strong> force field. The relaxed molecule is translated and rotated so its center of mass lands at the spatial center of the AlphaFold pocket.`,
    facts: [
      ['Conformer', 'RDKit 3D embedding'],
      ['Force field', 'MMFF94 relaxation'],
      ['Alignment', 'Center-of-mass → pocket centroid'],
    ]
  },
  // 13 — Layer 4 — VQE
  {
    id: 'l4', num: '13', img: 'layer-4.png',
    eyebrow: ['Layer 4', 'Quantum Mechanics & VQE', ''],
    title: 'The exact ground state, <span class="accent">not an approximation.</span>',
    lede: `Valence orbitals map from fermionic to qubit operators via <strong>Jordan–Wigner / Parity (Z₂-symmetry) / Bravyi–Kitaev</strong>. A <strong>TwoLocal</strong> ansatz (RY + CZ) is classically optimized by <strong>COBYLA/SPSA</strong> to minimize ⟨H⟩ — on CPU statevector or on a physical IBM QPU.`,
    formula: { cap: 'Variational eigensolver', body: 'E(θ) = ⟨ψ(θ)|H|ψ(θ)⟩  →  minimize over θ to reach ground-state E₀' },
    facts: [
      ['Mapping', 'Jordan–Wigner · Parity + Z₂ · Bravyi-Kitaev'],
      ['Ansatz', 'TwoLocal (RY rotations, CZ entanglers)'],
      ['Optimizer', 'COBYLA · SPSA'],
    ]
  },
  // 14 — Layer 5
  {
    id: 'l5', num: '14', img: 'layer-5.png', dual: 'left',
    eyebrow: ['Layer 5', 'ADMET & DNA Validation', ''],
    title: 'Will it survive the body? <span class="accent">Will it reach DNA?</span>',
    lede: `RDKit computes molecular weight, LogP, H-bond donors/acceptors, TPSA, and <strong>Lipinski violations</strong>. The coordinate engine independently calculates the <strong>Fsp³</strong> saturation index — a perfectly flat aromatic scaffold (Fsp³=0) is flagged <b>Extreme Risk · Flat Aromatic Toxicophore</b> for DNA intercalation.`,
    facts: [
      ['ADMET', 'MW · LogP · HBD/HBA · TPSA · Lipinski'],
      ['Mutagenicity', 'Fsp³ carbon-saturation index'],
      ['Alert', 'Flat aromatic (Fsp³=0) → DNA intercalation risk'],
    ]
  },
  // 15 — Layer 6
  {
    id: 'l6', num: '15', img: 'layer-6.png',
    eyebrow: ['Layer 6', 'Reporting & Cost', ''],
    title: 'From binding curve to <span class="accent">price tag</span>',
    lede: `We simulate a molecular-dynamics stability trajectory and a <strong>5-point log-dilution wet-lab assay</strong> centered on K<sub>d</sub>, then resolve <strong>live market prices</strong>: US Medicaid NADAC wholesale and Indian retail (INR), outputting comparative validation reports.`,
    facts: [
      ['Assay', '5-point log-dilution centered on Kd'],
      ['MD', 'Stability trajectory simulation'],
      ['Pricing', 'CMS NADAC (wholesale) + myUpchar (INR retail)'],
    ]
  },
  // 16 — Modules gallery (two parallel marquee ticker lanes: RTL & LTR)
  {
    id: 'mods', num: '16', stacked: true,
    eyebrow: ['Core Engines', 'Multi-Engine Architecture', ''],
    title: 'Engines operating <span class="accent">in concert</span>',
    lede: `Every figure and prediction on this platform is produced by specialized algorithmic engines running in real time. Hover any card to inspect its live computational role, or scroll smoothly to launch the full workspace.`,
    mods: [
      { tag: 'VQC', t: 'Quantum Vision', d: 'Hilbert-space anomaly detection', m: modMotifs.vqe, img: 'detection-vqc.png' },
      { tag: 'CXR', t: 'TorchXRayVision', d: '98.8% pediatric pneumonia sensitivity', m: modMotifs.fold, img: 'detection-hero.png' },
      { tag: 'OCT', t: 'Retinal Layer Engine', d: 'Sub-micron macular edema mapping', m: modMotifs.dock, img: 'detection-oct.png' },
      { tag: 'VQE', t: 'Variational Eigensolver', d: 'Ground-state energy → ΔG → Kd', m: modMotifs.vqe, img: 'mod-vqe.png' },
      { tag: 'LSTM', t: 'SMILES Generative Chem', d: 'Token-by-token scaffold sampling', m: modMotifs.lstm, img: 'mod-lstm.png' },
      { tag: 'AlphaFold', t: '3D Structure', d: 'EBI predicted pocket resolution', m: modMotifs.fold, img: 'mod-alphafold.png' },
      { tag: 'RDKit', t: 'Conformer & Docking', d: 'MMFF94 relax + pocket align', m: modMotifs.dock, img: 'mod-docking.png' },
      { tag: 'ADMET', t: 'DNA Mutagenicity Gating', d: 'Fsp³ carbon saturation & Lipinski', m: modMotifs.admet, img: 'mod-admet.png' },
      { tag: 'Price', t: 'Market Cost Benchmark', d: 'NADAC USD · myUpchar INR', m: modMotifs.price, img: 'mod-price.png' }
    ]
  },
  // 17 — IBM Hardware
  {
    id: 'ibm', num: '17', img: 'ibm-hardware.png', dual: 'left', code: true,
    eyebrow: ['Physical hardware', 'IBM Quantum integration', ''],
    title: 'From laptop to a <span class="accent">real quantum chip</span>',
    lede: `Provide an IBM API token and the pipeline switches to a physical QPU. <strong>qiskit_ibm_runtime</strong> selects the backend (e.g. <code>ibm_brisbane</code>, <code>ibm_kyoto</code>) and opens a dedicated <strong>Session</strong> to bundle iterative VQE submissions without queue delays.`,
    code: `from qiskit_ibm_runtime import QiskitRuntimeService, Estimator, Session\nservice = QiskitRuntimeService(channel="ibm_quantum", token=api_token)\nbackend = service.least_busy(operational=True)\nsession = Session(service=service, backend=backend)\nestimator = Estimator(session=session)`,
    facts: [
      ['Library', 'qiskit_ibm_runtime'],
      ['Backends', 'ibm_brisbane · ibm_kyoto · least-busy default'],
      ['Session', 'Dedicated Session → no inter-step queue waits'],
    ]
  },
  // 18 — Tech Stack
  {
    id: 'stack', num: '18', stacked: true,
    eyebrow: ['Engineering', 'Technology stack', ''],
    title: 'What it\'s <span class="accent">built on</span>',
    lede: `A unified clinical-quantum full stack, end to end.`,
    layers: [
      ['CV', 'Vision & Detection', 'TorchXRayVision · DenseNet-121', 'Kermany OCT · HAM10000 · NCT-CRC-100K'],
      ['QM', 'Quantum Vision & VQE', 'Qiskit v1.x · StatevectorEstimator', 'Parameterized Quantum Circuits (VQC) · IBM QPU'],
      ['ML', 'Generative Chemistry', 'SMILES LSTM (REINVENT)', 'PyTorch QRL Policy Gradients'],
      ['FE', 'Frontend', 'React 19 · Vite · Tailwind v4', 'Framer Motion · Lucide · Lenis Smooth Scroll'],
      ['BE', 'Backend', 'Python 3.10+ · Flask · Flask-CORS', 'PyTorch · RDKit · Qiskit · Requests'],
    ],
    art: () => svg(latticeArt)
  },
  // 19 — CTA
  {
    id: 'cta', num: '19', stacked: true, cta: true,
    eyebrow: ['Enter the platform', 'Begin a diagnostic & discovery run', ''],
    title: 'Spin up the <span class="accent">unified platform</span>',
    lede: `Launch the live clinical workspace: upload medical imagery for sub-visual early detection, identify mutated pathogen targets, and synthesize quantum-verified countermeasure candidates in real time.`,
    art: () => svg(chipArt)
  }
];

// expose
window.SCENES = SCENES;
