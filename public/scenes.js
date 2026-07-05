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

const orbitArt = `
  <g stroke-width="1">
    <circle class="svg-teal" cx="50" cy="50" r="42" opacity=".5"/>
    <ellipse class="svg-grey" cx="50" cy="50" rx="42" ry="16" opacity=".6"/>
    <ellipse class="svg-teal" cx="50" cy="50" rx="16" ry="42" opacity=".5"/>
  </g>
  <circle class="svg-fill-teal" cx="50" cy="50" r="5"/>
  <circle class="svg-fill-grey" cx="92" cy="50" r="2.6"/>
  <circle class="svg-fill-grey" cx="34" cy="34" r="2.2"/>
  <circle class="svg-fill-teal" cx="50" cy="8" r="2.6"/>`;

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
  // 00 — Hero
  {
    id: 'hero', stacked: true,
    eyebrow: ['Quantum-Powered Bio-Simulation'],
    title: 'QUANTUMSHIELD',
    lede: `We map the active electronic space of mutated pathogen targets — <strong>TB's InhA, COVID-19's M<sub>pro</sub></strong> — directly onto quantum processors, computing exact interatomic binding energies to compress early-stage drug discovery from <strong>5–7 years to 12–24 hours</strong>.`,
    scrollHint: 'SCROLL FOR MORE INFORMATION ↓'
  },
  // 01 — Who We Are
  {
    id: 'who', num: '01', img: 'who-we-are.png',
    eyebrow: ['Who We Are', 'A research platform', ''],
    title: 'We render molecules <em>in qubits</em>',
    lede: `QuantumShield is a hybrid <strong>QM/MM</strong> drug-discovery platform that pairs a Variational Quantum Eigensolver with reinforcement-learning generative chemistry. We are not replacing chemists — we are removing the classical computational ceiling that makes novel antibiotic design take a decade. <span class="muted">From pathogen name to verified candidate to comparative-cost report, in one supervised pipeline.</span>`,
    facts: [
      ['Founded on', `<b>QM/MM hybrid modeling</b> + Quantum Reinforcement Learning`],
      ['Built against', `Drug-resistant <b>M. tuberculosis</b>, <b>SARS-CoV-2</b>, <b>Salmonella</b>`],
      ['Deployed on', `Local CPU statevector <i>and</i> physical IBM QPUs`],
    ],
    art: ()=>svg(orbitArt)
  },
  // 02 — What We're Doing
  {
    id: 'what', num: '02', img: 'what-we-do.png', dual:'left',
    eyebrow: ['What We\'re Doing', 'The central thesis', ''],
    title: 'Years → Hours. Millions → <span class="accent">Cost of a run</span>',
    lede: `Traditional preclinical R&D spends <strong>$800M–$2.6B and 5–7 years</strong> per drug. Our QRL-guided pipeline resolves candidates in <strong>12–24 hours at ~$5M–$10M</strong> by computing the thermodynamic truth (ΔG, K<sub>d</sub>) instead of approximating it.`,
    facts: [
      ['10⁶⁰', 'Drug-like molecules in chemical space — classically intractable to enumerate'],
      ['5–7 yr', 'Classical timeline, replaced by a single optimized pipeline pass'],
      ['$800M↑', 'Vs. our run-cost reduction of roughly two orders of magnitude'],
    ],
    art: ()=>svg(waveArt)
  },
  // 03 — Theory
  {
    id: 'theory', num: '03', img: 'theory.png',
    eyebrow: ['Project Overview', 'Theory & physics', ''],
    title: 'The physics behind <span class="accent">every score</span>',
    lede: `Four parameters decide whether a generated molecule becomes a drug.`,
    formula: { cap:'Binding energy → affinity', body:'ΔG = RT ln(Kd)  ⟹  Kd ≈ 10^(ΔG/1.36) M  (room temp)' },
    facts: [
      ['ΔG', `<b>Thermodynamic binding energy</b>. More negative = tighter, more stable blockade of the target pocket.`],
      ['Kd', `<b>Dissociation constant</b> — concentration inhibiting 50% of receptors. Derived from ΔG.`],
      ['HOMO–LUMO', `<b>Frontier-orbital gap</b>. Wide = stable & shelf-safe. Narrow (<8 eV) = toxicity flag (covalent latch).`],
      ['Fsp³', `<b>Carbon saturation index</b>. Fsp³=0.0 = flat aromatic = <b>Extreme Risk</b> DNA intercalation.`],
    ],
    art: ()=>svg(latticeArt)
  },
  // 04 — Pipeline overview
  {
    id: 'pipeline', num: '04', stacked:true,
    eyebrow: ['Architecture', 'The 6-layer pipeline', ''],
    title: 'Input → Verified candidate & report',
    lede: `Every run flows sequentially across six logical layers.`,
    layers: [
      ['L1','Input & Pathogen Resolution','NVIDIA NIM + AlphaFold','Resolves target / UniProt / seed SMILES'],
      ['L2','Generative Chemistry & QRL','SMILES LSTM + PyTorch RL','Samples & optimizes candidate structures'],
      ['L3','Conformation & 3D Docking','RDKit · MMFF94','Relaxes & aligns molecule to pocket'],
      ['L4','Quantum Mechanics & VQE','Qiskit / IBM QPU','Maps orbitals → qubits, solves ground state'],
      ['L5','ADMET & DNA Validation','RDKit + Fsp³','Drug-likeness & mutagenicity gates'],
      ['L6','Reporting & Cost','MD sim + live price APIs','Assay, NADAC/INR pricing, PDF docs'],
    ],
    art: ()=>svg(flowArt)
  },
  // 05 — Layer 1
  {
    id: 'l1', num: '05', img: 'layer-1.png', dual:'left',
    eyebrow: ['Layer 1', 'Input & Pathogen Resolution', ''],
    title: 'Name a pathogen. <span class="accent">Resolve the target.</span>',
    lede: `The user names a pathogen (or picks a preset — TB / COVID-19). We query the <strong>NVIDIA NIM</strong> <code>meta/llama-3.1-8b-instruct</code> model to extract the target receptor, its <strong>UniProt ID</strong>, and a seed SMILES, then pull the predicted <strong>3D AlphaFold</strong> structure and parse the 10 closest active-site residues for docking.`,
    facts: [
      ['LLM', 'NVIDIA NIM · llama-3.1-8b-instruct (NVIDIA_API_KEY)'],
      ['Structures', 'EBI AlphaFold API · PDB parse → pocket residues'],
      ['Failover', 'UniProt KB primary-accession + search API'],
    ],
    art: ()=>svg(apiArt)
  },
  // 06 — Layer 2
  {
    id: 'l2', num: '06', img: 'layer-2.png',
    eyebrow: ['Layer 2', 'Generative Chemistry & QRL', ''],
    title: 'Generate, <span class="accent">score</span>, reinforce.',
    lede: `A character-level <strong>SMILES LSTM</strong> (AstraZeneca REINVENT lineage) samples raw candidate strings token-by-token. A <strong>PyTorch QRL agent</strong> computes policy-gradient updates against a reward blending drug-likeness (QED), synthetic accessibility (SA), and VQE binding affinity — reinforcing molecules that are strong <i>and</i> synthesizable.`,
    facts: [
      ['Model', '3-layer LSTM · embedding 256 · hidden 512'],
      ['Policy', 'PyTorch QRL · policy-gradient optimization'],
      ['Reward', 'QED + SA Score + VQE binding energy'],
    ],
    art: ()=>svg(helixArt)
  },
  // 07 — Layer 3
  {
    id: 'l3', num: '07', img: 'layer-3.png', dual:'left',
    eyebrow: ['Layer 3', 'Conformation & 3D Docking', ''],
    title: 'Relax to lowest energy. <span class="accent">Align to pocket.</span>',
    lede: `RDKit builds <strong>3D conformers</strong> of each generated molecule and relaxes bond lengths, angles, and torsions with the <strong>MMFF94</strong> force field. The relaxed molecule is translated and rotated so its center of mass lands at the spatial center of the AlphaFold pocket — ready for electronic Hamiltonian construction.`,
    facts: [
      ['Conformer', 'RDKit 3D embedding'],
      ['Force field', 'MMFF94 relaxation'],
      ['Alignment', 'Center-of-mass → pocket centroid'],
    ],
    art: ()=>svg(orbitArt)
  },
  // 08 — Layer 4 — VQE
  {
    id: 'l4', num: '08', img: 'layer-4.png',
    eyebrow: ['Layer 4', 'Quantum Mechanics & VQE', ''],
    title: 'The exact ground state, <span class="accent">not an approximation.</span>',
    lede: `Valence orbitals map from fermionic to qubit operators via <strong>Jordan–Wigner / Parity (Z₂-symmetry) / Bravyi–Kitaev</strong>. A <strong>TwoLocal</strong> ansatz (RY + CZ) is classically optimized by <strong>COBYLA/SPSA</strong> to minimize ⟨H⟩ — locally on Qiskit's <code>StatevectorEstimator</code> or on a physical IBM QPU. The converged eigenvalue → ΔG → K<sub>d</sub>.`,
    formula: { cap:'Variational eigensolver', body:'E(θ) = ⟨ψ(θ)|H|ψ(θ)⟩  →  minimize over θ to reach ground-state E₀' },
    facts: [
      ['Mapping', 'Jordan–Wigner · Parity + Z₂ · Bravyi-Kitaev'],
      ['Ansatz', 'TwoLocal (RY rotations, CZ entanglers)'],
      ['Optimizer', 'COBYLA · SSPA'],
    ],
    art: ()=>svg(chipArt)
  },
  // 09 — Layer 5
  {
    id: 'l5', num: '09', img: 'layer-5.png', dual:'left',
    eyebrow: ['Layer 5', 'ADMET & DNA Validation', ''],
    title: 'Will it survive the body? <span class="accent">Will it reach DNA?</span>',
    lede: `RDKit computes molecular weight, LogP, H-bond donors/acceptors, TPSA, and <strong>Lipinski violations</strong>. The coordinate engine independently calculates the <strong>Fsp³</strong> saturation index — a perfectly flat aromatic scaffold (Fsp³=0) is flagged <b>Extreme Risk · Flat Aromatic Toxicophore</b> for DNA intercalation.`,
    facts: [
      ['ADMET', 'MW · LogP · HBD/HBA · TPSA · Lipinski'],
      ['Mutagenicity', 'Fsp³ carbon-saturation index'],
      ['Alert', 'Flat aromatic (Fsp³=0) → DNA intercalation risk'],
    ],
    art: ()=>svg(latticeArt)
  },
  // 10 — Layer 6
  {
    id: 'l6', num: '10', img: 'layer-6.png',
    eyebrow: ['Layer 6', 'Reporting & Cost', ''],
    title: 'From binding curve to <span class="accent">price tag</span>',
    lede: `We simulate a molecular-dynamics stability trajectory and a <strong>5-point log-dilution wet-lab assay</strong> centered on K<sub>d</sub>, then resolve <strong>live market prices</strong>: <strong>US Medicaid NADAC</strong> wholesale and <strong>myUpchar</strong> Indian retail (INR), against our generated candidate — outputting comparison charts, validation metrics, and PDF-style documentation.`,
    facts: [
      ['Assay', '5-point log-dilution centered on Kd'],
      ['MD', 'Stability trajectory simulation'],
      ['Pricing', 'CMS NADAC (wholesale) + myUpchar (INR retail)'],
    ],
    art: ()=>svg(waveArt)
  },
  // 11 — SMILES LSTM
  {
    id: 'lstm', num: '11', img: 'smiles-lstm.png', dual:'left',
    eyebrow: ['Generative ML', 'SMILES LSTM', ''],
    title: 'A character-level chemist <span class="accent">that learns</span>',
    lede: `Our generator is a recurrent language model over the <strong>SMILES</strong> alphabet. Token <code>^</code> starts a sequence, <code>$</code> completes it; the network learns the grammar of valid chemistry and samples new scaffolds as medicine.`,
    facts: [
      ['Embedding', '256 dims'],
      ['Recurrent', '3× LSTM / GRU · hidden 512'],
      ['Output', 'Linear → vocabulary logits'],
      ['Weights', 'pretrained.rnn.pth (PyTorch)'],
      ['Lineage', 'AstraZeneca REINVENT (MolecularAI/Reinvent)'],
    ],
    art: ()=>svg(`
      <g stroke-width="1.2">
        <rect class="svg-teal" x="8" y="44" width="14" height="14" fill="rgba(19,138,165,.08)"/>
        <rect class="svg-grey" x="30" y="40" width="14" height="22" fill="none"/>
        <rect class="svg-grey" x="52" y="36" width="14" height="30" fill="none"/>
        <rect class="svg-teal" x="74" y="32" width="14" height="38" fill="rgba(19,138,165,.08)"/>
        <circle class="svg-fill-grey" cx="15" cy="51" r="2"/>
        <path class="svg-teal" d="M22 51 H30 M44 51 H52 M66 51 H74"/>
      </g>`)
  },
  // 12 — AlphaFold
  {
    id: 'alphafold', num: '12', img: 'alphafold.png',
    eyebrow: ['3D Structure', 'AlphaFold resolution', ''],
    title: 'No manual coordinates. <span class="accent">Predicted pockets.</span>',
    lede: `For a custom pathogen we query <code>alphafold.ebi.ac.uk/api/prediction/{uniprot}</code> for predicted structure metadata, failover through UniProt KB for secondary accessions and keyword search (non-human organisms prioritized), then download the PDB and run <strong>parse_pdb_to_pocket</strong> to extract the 3D coordinates (X,Y,Z, element, charge) of the 10 nearest active-site residues.`,
    facts: [
      ['Primary', 'AlphaFold EBI prediction API → pdbUrl'],
      ['Failover', 'UniProt KB JSON · search API by pathogen keyword'],
      ['Parser', 'parse_pdb_to_pocket → 10 closest residues'],
    ],
    art: ()=>svg(`
      <g stroke-width="1.2">
        <path class="svg-teal" d="M20 20 Q50 10 80 20 Q90 50 80 80 Q50 90 20 80 Q10 50 20 20Z" fill="rgba(19,138,165,.05)"/>
        <path class="svg-grey" d="M28 36 Q50 30 72 36 M28 64 Q50 70 72 64" opacity=".6"/>
        <circle class="svg-fill-teal" cx="50" cy="50" r="3.4"/><circle class="svg-fill-grey" cx="34" cy="40" r="2"/>
        <circle class="svg-fill-grey" cx="66" cy="40" r="2"/><circle class="svg-fill-grey" cx="34" cy="60" r="2"/>
        <circle class="svg-fill-grey" cx="66" cy="60" r="2"/>
      </g>`)
  },
  // 13 — Price & drug resolvers
  {
    id: 'price', num: '13', img: 'price-resolvers.png', dual:'left',
    eyebrow: ['Live APIs', 'Price & drug-name resolvers', ''],
    title: 'Wholesale dollar. <span class="accent">Retail rupee.</span>',
    dataApi: true,
    lede: `To benchmark R&D cost against the real market, the backend coordinates three live streams: NVIDIA NIM for pathogen→reference-drug translation, <strong>US CMS Medicaid NADAC</strong> for wholesale unit prices, and <strong>myUpchar</strong> for Indian retail MRP in INR.`,
    facts: [
      ['NIM', 'integrate.api.nvidia.com → llama-3.1-8b-instruct'],
      ['NADAC', 'data.medicaid.gov → LIKE match reference drug'],
      ['myUpchar', 'beta.myupchar.com → INR retail (MYUPCHAR_API_KEY)'],
    ],
    art: ()=>svg(apiArt)
  },
  // 14 — Local quantum
  {
    id: 'local', num: '14', img: 'local-sim.png',
    eyebrow: ['Local mode', 'Classical quantum simulation', ''],
    title: 'Offline VQE <span class="accent">on the CPU</span>',
    lede: `In offline mode we simulate the QPU classically on <strong>Qiskit v1.x primitives</strong>. We map the active-space Hamiltonian to qubit operators, prepare a <strong>TwoLocal</strong> trial state (RY + CZ, depth 2, CNOT 1), and iterate with <strong>COBYLA/SPSA</strong> to converge the ground state via <code>StatevectorEstimator</code>.`,
    facts: [
      ['SDK', 'Qiskit v1.x primitives'],
      ['Estimator', 'qiskit.primitives.StatevectorEstimator'],
      ['Ansatz', 'TwoLocal · RY + CZ · depth 2 · CNOT 1'],
    ],
    art: ()=>svg(chipArt)
  },
  // 15 — IBM hardware
  {
    id: 'ibm', num: '15', img: 'ibm-hardware.png', dual:'left', code:true,
    eyebrow: ['Physical hardware', 'IBM Quantum integration', ''],
    title: 'From laptop to a <span class="accent">real quantum chip</span>',
    lede: `Provide an IBM API token and the pipeline switches to a physical QPU. <strong>qiskit_ibm_runtime</strong> selects the backend (e.g. <code>ibm_brisbane</code>, <code>ibm_kyoto</code>) and opens a dedicated <strong>Session</strong> to bundle iterative VQE submissions — bypassing inter-step queue waits and returning error-mitigated counts.`,
    code: `from qiskit_ibm_runtime import QiskitRuntimeService, Estimator, Session\nservice = QiskitRuntimeService(channel="ibm_quantum", token=api_token)\nbackend = service.least_busy(operational=True)\nsession = Session(service=service, backend=backend)\nestimator = Estimator(session=session)`,
    facts: [
      ['Library', 'qiskit_ibm_runtime'],
      ['Backends', 'ibm_brisbane · ibm_kyoto · least-busy default'],
      ['Session', 'Dedicated Session → no inter-step queue waits'],
    ],
    art: ()=>svg(`
      <g stroke-width="1.2">
        <rect class="svg-teal" x="24" y="24" width="52" height="52" fill="rgba(19,138,165,.05)"/>
        <path class="svg-grey" d="M24 50 H76 M50 24 V76" opacity=".5"/>
        <circle class="svg-fill-teal" cx="50" cy="50" r="6"/>
        <circle class="svg-fill-grey" cx="36" cy="36" r="2.4"/><circle class="svg-fill-grey" cx="64" cy="36" r="2.4"/>
        <circle class="svg-fill-grey" cx="36" cy="64" r="2.4"/><circle class="svg-fill-grey" cx="64" cy="64" r="2.4"/>
      </g>`)
  },
  // 16 — Tech stack
  {
    id: 'stack', num: '16', stacked:true,
    eyebrow: ['Engineering', 'Technology stack', ''],
    title: 'What it\'s <span class="accent">built on</span>',
    lede: `A modern quantum-classical full stack, end to end.`,
    layers: [
      ['FE','Frontend','React 19 · Vite · Tailwind v4','Framer Motion · Lucide'],
      ['BE','Backend','Python 3.10+ · Flask · Flask-CORS','PyTorch · RDKit · Qiskit · Requests'],
      ['QM','Quantum','Qiskit v1.x · StatevectorEstimator','qiskit_ibm_runtime (physical QPU)'],
      ['ML','Generative','SMILES LSTM (REINVENT)','PyTorch QRL policy gradients'],
      ['EX','External APIs','Gemini · AlphaFold · UniProt','Medicaid NADAC · myUpchar · NVIDIA NIM'],
    ],
    art: ()=>svg(latticeArt)
  },
  // 17 — Modules gallery (image-rich hover reveal grid)
  {
    id: 'mods', num: '17', stacked:true,
    eyebrow: ['Methods', 'Module gallery', ''],
    title: 'Six engines <span class="accent">at the core</span>',
    lede: `Every figure on this page is produced by one of six engines. Hover a cell to load its rendered view — or keep scrolling to see the full pipeline. <span class="muted">Module renders are optional; the schematic stays if an image is missing.</span>`,
    mods: [
      { tag:'VQE',       t:'Variational eigensolver',  d:'Ground-state energy → ΔG → Kd',        m:modMotifs.vqe,    img:'mod-vqe.png' },
      { tag:'LSTM',      t:'SMILES generative chem',   d:'Token-by-token scaffold sampling',     m:modMotifs.lstm,   img:'mod-lstm.png' },
      { tag:'AlphaFold', t:'3D structure',            d:'Pocket residue resolution',            m:modMotifs.fold,   img:'mod-alphafold.png' },
      { tag:'RDKit',     t:'Conformer & docking',      d:'MMFF94 relax + pocket align',          m:modMotifs.dock,   img:'mod-docking.png' },
      { tag:'ADMET',     t:'Toxicity gating',         d:'Lipinski + Fsp³ DNA-intercalation',    m:modMotifs.admet,  img:'mod-admet.png' },
      { tag:'Price',     t:'Cost benchmark',           d:'NADAC USD · myUpchar INR',             m:modMotifs.price,  img:'mod-price.png' }
    ]
  },
  // 18 — CTA
  {
    id: 'cta', num: '18', stacked:true, cta:true,
    eyebrow: ['Enter the platform', 'Begin a discovery run', ''],
    title: 'Spin up the <span class="accent">pipeline</span>',
    lede: `Open the live workspace: name a pathogen, set the optimization flags, and watch the six layers resolve a quantum-verified candidate with full comparative reporting.`,
    art: ()=>svg(orbitArt)
  }
];

// expose
window.SCENES = SCENES;
