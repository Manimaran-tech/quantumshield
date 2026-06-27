# QuantumShield

**QuantumShield** is a state-of-the-art, hybrid quantum-classical de novo drug discovery platform designed to design breakthrough covalent inhibitors against mutated, drug-resistant pathogens. By combining AI-driven pathogen lookup, AlphaFold structure databases, and Quantum Reinforcement Learning (QRL) running on Variational Quantum Eigensolver (VQE) chemistry simulations, the platform identifies and optimizes drug candidates with ultra-high precision.

---

## 🧬 Who We Are & Our Goal

We are a group of quantum biologists, chemical engineers, and AI researchers leveraging hybrid quantum computing to shield humanity from rapidly evolving viral and bacterial threats.

**Our Goal:** To bypass classical computational bottlenecks and reduce the time required to design, mutate, and validate candidate molecules from years to hours—neutralizing emerging pathogens before they can spread.

---

## 🛠️ Architecture & Core Components

1. **Target Identification (NVIDIA NIM)**: Resolves mutated pathogens to their target proteins using LLMs, locating drug-binding pockets.
2. **Structure Retrieval (AlphaFold)**: Downloads 3D coordinate matrices (.pdb) for targeted residues.
3. **Generative Modeling (SMILES LSTM)**: Samples seed molecules using a PyTorch recurrent neural network trained on the ZINC database.
4. **QRL Policy Agent**: Leverages a Parameterized Quantum Circuit (PQC) using superconducting qubits (via simulation) to mutate molecules.
5. **VQE Solver**: Computes molecular ground-state electronic energies to evaluate binding affinity.
6. **ADMET Classifier**: Evaluates drug candidates for clinical safety, absorption, and toxicity profile.

---

## ⚙️ Prerequisites & System Requirements

To run QuantumShield locally, ensure your system has the following installed:

* **Node.js** (v18 or higher)
* **npm** (v9 or higher)
* **Python** (v3.10 - v3.12)
* **PyTorch** (for the generative LSTM model)
* **RDKit** (for chemical informatics and SMILES handling)
* **Flask** (for the backend endpoints)

---

## 🚀 Local Installation & Setup

Follow these steps to set up and run the platform on your local machine:

### 1. Clone the Repository
```bash
git clone https://github.com/Manimaran-tech/quantumshield.git
cd quantumshield
```

### 2. Frontend Installation
Install the frontend dependencies and build the assets:
```bash
npm install
```

### 3. Backend Setup
Set up a Python virtual environment and install the required libraries:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install flask Flask-Cors rdkit torch numpy requests
```

### 4. Running the Application
Run both the Flask backend and Vite frontend development server:

* **Start Backend (Python/Flask):**
  ```bash
  python app.py
  ```

* **Start Frontend (Vite/React):**
  ```bash
  npm run dev
  ```

Open your browser and navigate to `http://localhost:3002` (or the port specified by Vite) to explore the QuantumShield interface.

---

## 🧪 Running Tests
You can verify the calculations and endpoints using the integration test suite:
```bash
python -m unittest test_integration.py
python -m unittest test_simulation.py
```
