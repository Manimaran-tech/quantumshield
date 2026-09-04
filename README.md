# 🛡️ QuantumShield: Quantum & Machine Learning Drug-Discovery Pipeline

QuantumShield is an advanced, hybrid Quantum-Classical and Machine Learning-driven drug discovery pipeline. It accelerates the identification, screening, and optimization of therapeutic drug candidates against critical pathogens (e.g., *Mycobacterium tuberculosis* InhA, COVID-19 Mpro) by combining quantum-mechanical simulations with reinforcement learning and evolutionary algorithms.

---

## 🚀 Key Features

* **🔬 Variational Quantum Eigensolver (VQE)**: Leverages Qiskit to run molecular quantum chemistry simulations, estimating exact ground-state energies and HOMO-LUMO gaps under simulated NISQ-era decoherence noise.
* **⚡ Quantum Error Mitigation**: Implements Zero Noise Extrapolation (ZNE) and Pauli Twirling post-processing, significantly reducing systematic energy bias and step jitter.
* **🧬 QRL & Evolutionary Candidate Generator**: Features a Quantum Reinforcement Learning (QRL) and evolutionary agent to generate, modify, and optimize molecular SMILES strings.
* **🌡️ Molecular Dynamics (MD) Simulation**: Models dynamic coordinate changes and structural stability of ligand-protein systems under physiological temperatures (310.15 K).
* **⛓️ DNA Interaction & Docking Analysis**: Performs in-silico docking potential calculations, binding affinity estimation ($\Delta G$), and dissociation constant ($K_d$) screening.
* **🧪 Wet-Lab Validation Assays**: Simulates high-fidelity in-vitro assays to validate drug efficacy, synthetic accessibility (SA), drug-likeness (QED), and toxicological constraints.
* **🎛️ Interactive Dashboard**: React + TypeScript + Vite frontend offering real-time control over active space sizes (qubits/orbitals), ansatz transpilation metrics, noise parameters, and convergence curves.

---

## 🛠️ Technology Stack

* **Frontend**: React 19, TypeScript, Vite, TailwindCSS (v4), Motion (Framer Motion), Lucide Icons.
* **Backend**: Flask, Flask-CORS.
* **Quantum & Chem Engines**: Qiskit, Qiskit-Algorithms, RDKit, NumPy, SciPy, PyTorch.

---

## ⚙️ Setup & Installation

### Prerequisites
* **Node.js** (v18 or higher)
* **Python** (v3.10 or higher)

### 1. Clone & Navigate
```bash
git clone https://github.com/Manimaran-tech/quantumshield.git
cd quantumshield
```

### 2. Backend Setup
Create and activate a virtual environment, then install dependencies:
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

Create a `.env` file in the root directory:
```env
GEMINI_API_KEY="your-gemini-api-key"
APP_URL="http://localhost:3001"
```

Start the Flask backend:
```bash
python app.py
```
*The backend will start on [http://localhost:5000](http://localhost:5000).*

### 3. Frontend Setup
Install frontend node packages and start the Vite dev server:
```bash
# Install dependencies
npm install

# Start local dev server
npm run dev
```
*The frontend will run on [http://localhost:3001](http://localhost:3001).*

---

## 🧪 Verification & Testing

To run the automated test suite for validation and regression checks:
```bash
# Run backend unit and integration tests
pytest
```

---

## 📚 Scientific References & Rigor

QuantumShield adheres to rigorous in-silico simulation rules. For detailed technical, physical, and chemical design patterns, please refer to the following local documents:
* [Key Learnings & Study Guide](file:///d:/Quantum/quantumshield/learning.md): A conceptual manual detailing thermodynamic equations, VQE ansätze, and presentation workflows.
* [Research Audit Summary](file:///d:/Quantum/quantumshield/audit_summary.md): Audit findings and the two-lane validation roadmap.
* [Lane-B Remediation Fixes](file:///d:/Quantum/quantumshield/fix.md): Exact list of corrections made to ensure computation reproducibility and prevent data fabrication.
* [Quantum Chemistry Refinements](file:///d:/Quantum/quantumshield/research_improvements.md): Advanced orbital partitioning (CASSCF/DMRG) and quantum-classical codesign roadmap.
