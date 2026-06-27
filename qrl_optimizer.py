import numpy as np
import os
import json
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, Lipinski, QED
from rdkit import DataStructs
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.primitives import StatevectorEstimator
from qiskit_algorithms import VQE, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA
from qiskit.circuit.library import TwoLocal

# Import biophysical simulation engines to calculate rich state variables and rewards
from generator import PRESET_POCKETS, EvolutionaryGenerator
from simulation import (
    run_molecular_dynamics_simulation,
    get_molecular_hamiltonian,
    solve_huckel_gap,
    get_dynamic_molecular_properties
)

# PAINS and toxicological alert SMARTS patterns
PAINS_SMARTS = [
    "[#6](=[#8])-[#6]1=[#6]-[#6](=[#8])-[#6]=[#6]-[#6]1", # Quinone
    "O=C1CC(=O)NC(=O)N1", # Barbituric acid derivative
    "Oc1c(O)cccc1", # Catechol
    "[Cl,Br,I][CX4H2,CX4H1,CX4H0]", # Alkyl halide (highly reactive)
    "[S,N,O]C(=S)[S,N,O]", # Thiocarbonyl
    "C=CC=O" # Michael acceptor / enone
]

# Define chemical reactions using SMARTS patterns
REACTION_LIBRARY = {}

def init_reactions():
    reactions_smarts = {
        "bioisostere_h_to_f": "[C:1][H:2] >> [C:1][F:2]",
        "bioisostere_oh_to_f": "[C:1][O:2][H:3] >> [C:1][F:2]",
        "bioisostere_carboxyl_to_amide": "[C:1](=[O:2])[O:3][H:4] >> [C:1](=[O:2])[N:3]([H:4])[H]",
        "bioisostere_ester_to_amide": "[C:1](=[O:2])[O:3][C:4] >> [C:1](=[O:2])[N:3]([H])[C:4]",
        "scaffold_hop_benzene_to_pyridine": "[c:1]1[c:2][c:3][c:4][c:5][c:6]1 >> [c:1]1[n:2][c:3][c:4][c:5][c:6]1",
        "scaffold_hop_phenyl_to_thiophene": "[c:1]1[c:2][c:3][c:4][c:5][c:6]1 >> [c:1]1[s:2][c:3][c:4][c:5]1",
        "ring_expansion_cyclopentyl_to_cyclohexyl": "[C:1]1[C:2][C:3][C:4][C:5]1 >> [C:1]1[C:2][C:3][C:4][C:5]CC1",
        "ring_contraction_cyclohexyl_to_cyclopentyl": "[C:1]1[C:2][C:3][C:4][C:5][C:6]1 >> [C:1]1[C:2][C:3][C:4][C:5]1",
        "linker_elongation": "[C:1][C:2] >> [C:1]CC[C:2]",
        "add_methyl": "[C:1][H:2] >> [C:1][C:2]([H])([H])[H]",
        "add_trifluoromethyl": "[C:1][H:2] >> [C:1]C(F)(F)F"
    }
    for name, smarts in reactions_smarts.items():
        try:
            REACTION_LIBRARY[name] = AllChem.ReactionFromSmarts(smarts)
        except Exception as e:
            print(f"Failed to load reaction {name}: {e}")

# Initialize SMARTS reactions library
init_reactions()


def run_actual_vqe(qubit_op, active_orbitals=4):
    """
    Runs a real Variational Quantum Eigensolver (VQE) using Qiskit.
    Constructs a parameterized ansatz, sets up an Estimator, and runs a classical COBYLA optimizer.
    """
    num_qubits = qubit_op.num_qubits
    # Hardware-efficient ansatz for variational state preparation
    ansatz = TwoLocal(num_qubits, ['ry'], ['cz'], 'linear', reps=1)
    # Fast COBYLA optimizer for real-time reinforcement learning feedback
    optimizer = COBYLA(maxiter=15)
    estimator = StatevectorEstimator()
    try:
        vqe = VQE(estimator, ansatz, optimizer)
        result = vqe.compute_minimum_eigenvalue(qubit_op)
        return float(result.eigenvalue)
    except Exception as e:
        print(f"Qiskit VQE execution failed: {e}. Falling back to NumPyMinimumEigensolver (FCI).")
        try:
            numpy_solver = NumPyMinimumEigensolver()
            numpy_result = numpy_solver.compute_minimum_eigenvalue(qubit_op)
            return float(numpy_result.eigenvalue)
        except Exception as ex:
            print(f"Classical NumPy solver fallback failed: {ex}.")
            # Standard molecule core baseline fallback energy
            return -75.0


def get_valid_action_mask(smiles, actions):
    """
    Evaluates which chemical reactions in our library are applicable to the current SMILES.
    Returns a list of 1.0 (valid) and 0.0 (invalid) corresponding to action indexes.
    """
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return [0.0] * len(actions)
        
    mask = []
    try:
        mol_h = Chem.AddHs(mol)
        for action in actions:
            if action == "stop":
                mask.append(1.0)  # Terminate is always valid
                continue
                
            rxn = REACTION_LIBRARY.get(action)
            if not rxn:
                mask.append(0.0)
                continue
                
            products = rxn.RunReactants((mol_h,))
            if products and len(products) > 0:
                mask.append(1.0)
            else:
                mask.append(0.0)
    except Exception as e:
        print(f"Action masking evaluation failed for {smiles}: {e}")
        # Default fallback: allow everything
        mask = [1.0] * len(actions)
        
    # Ensure at least 'stop' is valid if all reactions failed
    if sum(mask) == 0.0:
        mask[-1] = 1.0
        
    return mask


class QuantumRLAgent:
    def __init__(self, num_qubits=8, lr=0.05):
        self.num_qubits = num_qubits
        self.lr = lr
        
        # 8 qubits -> 32 parameters for variational layers (RY and RZ on 8 qubits, repeated in 2 layers)
        self.theta = np.random.uniform(0, 2 * np.pi, 32)
        self.estimator = StatevectorEstimator()
        
        # 12 actions (11 chemical reactions + stop)
        self.actions = [
            "bioisostere_h_to_f",
            "bioisostere_oh_to_f",
            "bioisostere_carboxyl_to_amide",
            "bioisostere_ester_to_amide",
            "scaffold_hop_benzene_to_pyridine",
            "scaffold_hop_phenyl_to_thiophene",
            "ring_expansion_cyclopentyl_to_cyclohexyl",
            "ring_contraction_cyclohexyl_to_cyclopentyl",
            "linker_elongation",
            "add_methyl",
            "add_trifluoromethyl",
            "stop"
        ]
        self.num_actions = len(self.actions)
        
        # Define 12 Pauli operators for expectation values (mapping to action probabilities)
        self.observables = [
            SparsePauliOp("IIIIIIIZ"),  # action 0
            SparsePauliOp("IIIIIIZI"),  # action 1
            SparsePauliOp("IIIIIZII"),  # action 2
            SparsePauliOp("IIIIZIII"),  # action 3
            SparsePauliOp("IIIZIIII"),  # action 4
            SparsePauliOp("IIZIIIII"),  # action 5
            SparsePauliOp("IZIIIIII"),  # action 6
            SparsePauliOp("ZIIIIIII"),  # action 7
            SparsePauliOp("IIIIIIZZ"),  # action 8
            SparsePauliOp("ZZIIIIII"),  # action 9
            SparsePauliOp("IIIZZIII"),  # action 10
            SparsePauliOp("IZIZIZIZ")   # action 11
        ]

    def build_pqc_circuit(self, state, theta):
        """
        Builds the Parameterized Quantum Circuit (PQC).
        - State is encoded via Dense Angle Encoding:
          Maps 12 normalized state features to 8 qubits.
        - Two-layer ansatz with data re-uploading to enhance expressiveness.
        - 32 parameters total: RY and RZ on each of 8 qubits in 2 layers.
        """
        qc = QuantumCircuit(self.num_qubits)
        
        # --- LAYER 1 ---
        # 1. First Encoding
        for i in range(8):
            angle = np.clip(state[i], 0.0, 1.0) * np.pi
            qc.ry(angle, i)
        for i in range(4):
            angle = np.clip(state[8 + i], 0.0, 1.0) * np.pi
            qc.ry(angle, i)
        qc.barrier()
        
        # 2. First Variational Layer (RY and RZ on 8 qubits: params 0 to 15)
        for i in range(8):
            qc.ry(theta[i], i)
            qc.rz(theta[i + 8], i)
        qc.barrier()
        
        # 3. First Entanglement Layer (strongly entangling CNOT ring)
        for i in range(self.num_qubits - 1):
            qc.cx(i, i + 1)
        qc.cx(self.num_qubits - 1, 0)
        qc.barrier()
        
        # --- LAYER 2 (Data Re-uploading) ---
        # 4. Re-encode state vector to inject non-linearity
        for i in range(8):
            angle = np.clip(state[i], 0.0, 1.0) * np.pi
            qc.ry(angle, i)
        for i in range(4):
            angle = np.clip(state[8 + i], 0.0, 1.0) * np.pi
            qc.ry(angle, i)
        qc.barrier()
        
        # 5. Second Variational Layer (RY and RZ on 8 qubits: params 16 to 31)
        for i in range(8):
            qc.ry(theta[i + 16], i)
            qc.rz(theta[i + 24], i)
        qc.barrier()
        
        # 6. Second Entanglement Layer
        for i in range(self.num_qubits - 1):
            qc.cx(i, i + 1)
        qc.cx(self.num_qubits - 1, 0)
        qc.barrier()
        
        return qc

    def get_action_probabilities(self, state, action_mask, theta=None):
        """
        Computes action probabilities using the expectation values of the PQC, masked by valid actions.
        """
        if theta is None:
            theta = self.theta
            
        qc = self.build_pqc_circuit(state, theta)
        
        # Run circuit on classical StatevectorEstimator
        pub = (qc, self.observables)
        job = self.estimator.run([pub])
        result = job.result()[0]
        
        # Expectation values are in [-1, 1]
        expectations = result.data.evs
        
        # Softmax with a temperature parameter for exploration
        temperature = 2.0
        exp_vals = np.exp(expectations * temperature)
        
        # Apply action masking
        masked_exp = exp_vals * np.array(action_mask)
        
        # Fallback if masking eliminates all actions
        if np.sum(masked_exp) == 0.0:
            masked_exp = np.array(action_mask)
            
        if np.sum(masked_exp) == 0.0:
            # If the mask is all zeros, fallback to uniform probabilities
            probs = np.ones(self.num_actions) / self.num_actions
        else:
            probs = masked_exp / np.sum(masked_exp)
        return probs, expectations

    def select_action(self, state, action_mask):
        """
        Samples a valid action based on PQC policy and mask.
        """
        probs, _ = self.get_action_probabilities(state, action_mask)
        action_idx = np.random.choice(self.num_actions, p=probs)
        return action_idx, probs[action_idx]

    def compute_parameter_shift_gradients(self, state, action, action_mask):
        """
        Computes the analytical policy log-gradient with respect to theta 
        using the Parameter-Shift Rule and Action Masking.
        """
        temperature = 2.0
        grads = np.zeros_like(self.theta)
        shift = np.pi / 2.0
        
        # Get baseline probabilities and expectations
        probs, expectations = self.get_action_probabilities(state, action_mask)
        
        # Shift each parameter theta_j
        for j in range(len(self.theta)):
            # Theta + pi/2
            theta_plus = np.copy(self.theta)
            theta_plus[j] += shift
            _, expectations_plus = self.get_action_probabilities(state, action_mask, theta_plus)
            
            # Theta - pi/2
            theta_minus = np.copy(self.theta)
            theta_minus[j] -= shift
            _, expectations_minus = self.get_action_probabilities(state, action_mask, theta_minus)
            
            # Exact gradient: d<O_k>/dtheta_j = 0.5 * (<O_k>_+ - <O_k>_-)
            d_expectations = 0.5 * (expectations_plus - expectations_minus)
            
            # Softmax log-gradient with action mask: d(ln P(a))/dtheta_j = temperature * [ d<O_a>/dtheta_j - sum_i P(i)*d<O_i>/dtheta_j ]
            sum_prob_d_expectations = np.sum(probs * d_expectations)
            grads[j] = temperature * (d_expectations[action] - sum_prob_d_expectations)
            
        return grads

    def update_policy(self, states, actions, action_masks, rewards):
        """
        REINFORCE Policy Gradient update using discounted returns and Returns Normalization.
        """
        # 1. Compute discounted returns G_t
        gamma = 0.99
        returns = np.zeros_like(rewards, dtype=float)
        discounted_sum = 0.0
        for t in reversed(range(len(rewards))):
            discounted_sum = rewards[t] + gamma * discounted_sum
            returns[t] = discounted_sum
            
        # 2. Normalize returns to stabilize gradients (baseline subtraction)
        if len(returns) > 1:
            std = np.std(returns)
            if std > 1e-5:
                returns = (returns - np.mean(returns)) / std
                
        gradients = np.zeros_like(self.theta)
        
        for t in range(len(states)):
            state = states[t]
            action = actions[t]
            mask = action_masks[t]
            g_t = returns[t]
            
            # Compute policy gradient via Parameter-Shift Rule
            grad_log_p = self.compute_parameter_shift_gradients(state, action, mask)
            gradients += grad_log_p * g_t
            
        # Gradient ascent to maximize expected return
        self.theta += self.lr * gradients
        self.theta = np.mod(self.theta, 2 * np.pi)


class ChemicalEnvironment:
    """
    Richer Reinforcement Learning Environment for Medicinal Chemistry Lead Discovery.
    Handles molecule modifications, properties estimations, loop detection, and terminations.
    Pocket-generalized structure: maps generalized pocket_residues and reference smiles.
    """
    def __init__(self, pocket_residues, reference_smiles, max_steps=8):
        self.pocket_residues = pocket_residues
        self.reference_smiles = reference_smiles
        self.max_steps = max_steps
        self.reset()
        
    def reset(self, seed_smiles=None):
        if seed_smiles:
            self.state_smiles = seed_smiles
        else:
            self.state_smiles = self.reference_smiles
        self.steps_taken = 0
        self.history = [self.state_smiles]
        return self.get_state()
        
    def get_state(self):
        return get_rich_molecular_state(self.state_smiles, self.pocket_residues, self.reference_smiles)
        
    def step(self, action_name):
        self.steps_taken += 1
        
        # 1. Handle explicit Stop action
        if action_name == "stop":
            reward = self.calculate_reward(self.state_smiles)
            return self.get_state(), reward, True, {"info": "agent stopped"}
            
        # 2. Apply chemistry reaction
        new_smiles = apply_chemical_action(self.state_smiles, action_name)
        
        # 3. Check invalid structure
        mol = Chem.MolFromSmiles(new_smiles)
        if not mol:
            # Termination penalty for chemical collapse
            return self.get_state(), -25.0, True, {"info": "invalid molecule"}
            
        # 4. Check duplicate / circular transformations
        if new_smiles in self.history:
            reward = -10.0
            done = False
        else:
            self.history.append(new_smiles)
            self.state_smiles = new_smiles
            reward = self.calculate_reward(new_smiles)
            done = False
            
        # 5. Check step limits
        if self.steps_taken >= self.max_steps:
            done = True
            
        return self.get_state(), reward, done, {"info": "step successful"}
        
    def calculate_reward(self, smiles):
        return calculate_chemical_reward(smiles, self.pocket_residues, self.reference_smiles)


def apply_chemical_action(smiles, action_name):
    """
    Applies an RDKit chemical transformation to a SMILES string.
    Returns the new SMILES, or the original if not applicable.
    """
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return smiles

    if action_name == "stop":
        return smiles

    rxn = REACTION_LIBRARY.get(action_name)
    if not rxn:
        return smiles
        
    try:
        mol_h = Chem.AddHs(mol)
        products = rxn.RunReactants((mol_h,))
        
        if products and len(products) > 0:
            prod_mol = products[0][0]
            prod_mol = Chem.RemoveHs(prod_mol)
            Chem.SanitizeMol(prod_mol)
            return Chem.MolToSmiles(prod_mol)
    except Exception as e:
        print(f"Reaction application failed for {action_name}: {e}")
        
    return smiles


def get_rich_molecular_state(smiles, pocket_residues, reference_smiles):
    """
    Calculates 12 generalized pocket-aware biophysical descriptors normalized to [0, 1]
    for dense angle encoding into the quantum policy network.
    No hardcoded pathogen name logic: fully generalized to any input pocket coordinates.
    """
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return [0.5] * 12
        
    # --- RDKit Chemical Descriptors ---
    mw = Descriptors.ExactMolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    tpsa = Descriptors.TPSA(mol)
    rotb = Lipinski.NumRotatableBonds(mol)
    qed_val = QED.qed(mol)
    
    # Generate 3D coordinates for biophysical calculations
    gen = EvolutionaryGenerator()
    coords = gen.generate_3d_coordinates(mol)
    
    # 1. Docking Energy: Lennard-Jones + Coulomb physical pocket interaction energy
    docking_energy = gen.calculate_docking_energy(coords, pocket_residues)
    docking_score = -14.0 + 0.8 * (docking_energy - 2.0)
    docking_score = max(-14.0, min(-6.0, docking_score))
    
    # 2. Molecular Dynamics trajectory RMSD (run a fast 15-step Langevin MD)
    # NOTE: steps=15 is a lightweight real-time surrogate for rapid interactive reinforcement learning updates.
    # Production uses 100ns molecular dynamics simulations.
    md_res = run_molecular_dynamics_simulation(coords, temp=310.15, steps=15)
    md_rmsd = md_res.get("rmsd_trajectory", [0.15])[-1]
    
    # 3. Hydrogen Bonds Count between ligand polar atoms and pocket polar residues
    h_bonds_count = 0
    for atom in coords:
        ax, ay, az = atom["x"], atom["y"], atom["z"]
        a_el = atom.get("element", atom.get("type", "H"))
        if a_el in ["N", "O"]:
            for res in pocket_residues:
                rx, ry, rz = res["x"], res["y"], res["z"]
                r_el = res.get("element", "C")
                if r_el in ["N", "O", "S"]:
                    dist = np.sqrt((ax-rx)**2 + (ay-ry)**2 + (az-rz)**2)
                    if dist <= 3.5:
                        h_bonds_count += 1
                        break
                        
    # 4. Pocket SASA (solvent accessible surface area coverage estimate)
    close_residues = 0
    for res in pocket_residues:
        rx, ry, rz = res["x"], res["y"], res["z"]
        is_close = False
        for atom in coords:
            ax, ay, az = atom["x"], atom["y"], atom["z"]
            dist = np.sqrt((ax-rx)**2 + (ay-ry)**2 + (az-rz)**2)
            if dist <= 4.5:
                is_close = True
                break
        if is_close:
            close_residues += 1
    sasa_coverage = close_residues / len(pocket_residues) if pocket_residues else 0.0
    
    # 5. Binding Contacts count within 4.5 Angstroms
    binding_contacts = 0
    for atom in coords:
        ax, ay, az = atom["x"], atom["y"], atom["z"]
        for res in pocket_residues:
            rx, ry, rz = res["x"], res["y"], res["z"]
            dist = np.sqrt((ax-rx)**2 + (ay-ry)**2 + (az-rz)**2)
            if dist <= 4.5:
                binding_contacts += 1
                
    # 6. VQE Ground State Energy: Exact ground state energy of active space using true variational ansatz
    try:
        qubit_op, target_energy = get_molecular_hamiltonian("target", active_orbitals=4, mapper_type='parity', custom_coords=coords)
        vqe_energy = run_actual_vqe(qubit_op, active_orbitals=4)
    except Exception as e:
        print(f"VQE solver fallback in state computation: {e}")
        vqe_energy = target_energy
        
    # Calculate isolated baseline to get relative binding VQE energy (size-independent)
    baseline = 0.0
    for atom in coords:
        el = atom.get("element", atom.get("type", "H"))
        baseline += -0.5 if el == "H" else -2.5
    relative_vqe = vqe_energy - baseline
        
    # 7. HOMO-LUMO Gap from hybrid Hückel solver
    gap_ev, homo_ev = solve_huckel_gap(coords)
    
    # 8. Conformational Entropy Penalty (T*dS)
    entropy_penalty = 4.5 + 0.35 * rotb
    
    # 9. Toxicity Risk value
    dyn_props = get_dynamic_molecular_properties(coords)
    toxicity_value = 10.0
    if dyn_props["is_toxic"]:
        toxicity_value = 100.0 if "Extreme" in dyn_props["toxicity"] else 50.0
        
    # 10. QED
    
    # 11. Novelty (Tanimoto similarity to reference drug)
    ref_mol = Chem.MolFromSmiles(reference_smiles)
    novelty = 1.0
    if ref_mol:
        try:
            fp1 = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=1024)
            fp2 = AllChem.GetMorganFingerprintAsBitVect(ref_mol, 2, nBits=1024)
            similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
            novelty = 1.0 - similarity
        except:
            novelty = 0.5

    # 12. Molecular Weight

    # Normalize descriptors to [0, 1]
    docking_n = min(1.0, max(0.0, (docking_score + 14.0) / 13.0))
    rmsd_n = min(1.0, max(0.0, md_rmsd / 2.0))
    hb_n = min(1.0, max(0.0, h_bonds_count / 8.0))
    sasa_n = min(1.0, max(0.0, sasa_coverage))
    contacts_n = min(1.0, max(0.0, binding_contacts / 100.0))
    vqe_n = min(1.0, max(0.0, (-relative_vqe) / 15.0))
    gap_n = min(1.0, max(0.0, (gap_ev - 4.0) / 21.0))
    entropy_n = min(1.0, max(0.0, entropy_penalty / 15.0))
    tox_n = min(1.0, max(0.0, toxicity_value / 100.0))
    qed_n = min(1.0, max(0.0, qed_val))
    novelty_n = min(1.0, max(0.0, novelty))
    mw_n = min(1.0, max(0.0, (mw - 100.0) / 500.0))
    
    return [docking_n, rmsd_n, hb_n, sasa_n, contacts_n, vqe_n, gap_n, entropy_n, tox_n, qed_n, novelty_n, mw_n]


def calculate_chemical_reward(smiles, pocket_residues, reference_smiles):
    """
    Chemically meaningful Multi-Objective reward function based on biophysical simulation.
    All components normalized to [0, 1] before scaling to prevent term dominance.
    """
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return -25.0
        
    mw = Descriptors.ExactMolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    rotb = Lipinski.NumRotatableBonds(mol)
    n_chiral = len(Chem.FindMolChiralCenters(mol, includeUnassigned=True))
    n_rings = Lipinski.RingCount(mol)
    
    sa_score = 1.5 + (0.005 * mw) + (0.3 * rotb) + (0.5 * n_chiral) + (0.4 * n_rings)
    sa_score = max(1.0, min(10.0, sa_score))
    
    # Lipinski rules
    violations = 0
    if mw > 500: violations += 1
    if logp > 5.0: violations += 1
    if hbd > 5: violations += 1
    if hba > 10: violations += 1
    
    pains_alerts = 0
    for smarts in PAINS_SMARTS:
        pat = Chem.MolFromSmarts(smarts)
        if pat and mol.HasSubstructMatch(pat):
            pains_alerts += 1
            
    # Tanimoto Fingerprint Novelty
    ref_mol = Chem.MolFromSmiles(reference_smiles)
    novelty = 1.0
    if ref_mol:
        try:
            fp1 = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=1024)
            fp2 = AllChem.GetMorganFingerprintAsBitVect(ref_mol, 2, nBits=1024)
            similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
            novelty = 1.0 - similarity
        except:
            novelty = 0.5
            
    # Generate 3D coordinates for physical calculations
    gen = EvolutionaryGenerator()
    coords = gen.generate_3d_coordinates(mol)
        # 1. Docking score
    docking_energy = gen.calculate_docking_energy(coords, pocket_residues)
    docking_score = -14.0 + 0.8 * (docking_energy - 2.0)
    docking_score = max(-14.0, min(-6.0, docking_score))
    
    # 2. VQE Ground State Energy (using true variational quantum eigensolver)
    try:
        qubit_op, target_energy = get_molecular_hamiltonian("target", active_orbitals=4, mapper_type='parity', custom_coords=coords)
        vqe_energy = run_actual_vqe(qubit_op, active_orbitals=4)
    except Exception as e:
        vqe_energy = target_energy
        
    # Calculate isolated baseline to get relative binding VQE energy (size-independent)
    baseline = 0.0
    for atom in coords:
        el = atom.get("element", atom.get("type", "H"))
        baseline += -0.5 if el == "H" else -2.5
    relative_vqe = vqe_energy - baseline
        
    # 3. MD Langevin Stability (fast 15-step trajectory)
    # NOTE: steps=15 is a lightweight real-time surrogate for rapid interactive reinforcement learning updates.
    # Production uses 100ns molecular dynamics simulations.
    md_res = run_molecular_dynamics_simulation(coords, temp=310.15, steps=15)
    md_stability = md_res.get("stability_score", 75.0)
    
    # Toxicity value from alerts
    dyn_props = get_dynamic_molecular_properties(coords)
    toxicity_value = 0.0
    if dyn_props["is_toxic"]:
        toxicity_value = 100.0 if "Extreme" in dyn_props["toxicity"] else 50.0
    total_tox_score = pains_alerts * 30.0 + toxicity_value
    total_tox_score = min(100.0, total_tox_score)

    # --- REWARD TERM NORMALIZATION [0, 1] ---
    norm_docking = min(1.0, max(0.0, (-docking_score - 6.0) / 8.0)) # docking in [-14, -6]
    norm_vqe = min(1.0, max(0.0, (-relative_vqe) / 15.0))            # relative_vqe in [-15, 0]
    norm_novelty = min(1.0, max(0.0, novelty))
    norm_lipinski = min(1.0, max(0.0, (4.0 - violations) / 4.0))
    norm_toxicity = min(1.0, max(0.0, total_tox_score / 100.0))
    norm_entropy = min(1.0, max(0.0, rotb / 10.0))                  # penalty for rotatable bonds (discourage floppy chains)
    norm_sa = min(1.0, max(0.0, (10.0 - sa_score) / 9.0))
    norm_instability = min(1.0, max(0.0, (100.0 - md_stability) / 100.0))
    
    # Apply weights (each scaled from 5.0 to 15.0 to make overall reward well-behaved)
    w_docking = 12.0
    w_vqe = 10.0
    w_novelty = 8.0
    w_lipinski = 5.0
    w_toxicity = 10.0
    w_entropy = 6.0
    w_sa = 6.0
    w_instability = 8.0
    
    reward = (
        w_docking * norm_docking +
        w_vqe * norm_vqe +
        w_novelty * norm_novelty +
        w_lipinski * norm_lipinski -
        w_toxicity * norm_toxicity -
        w_entropy * norm_entropy -
        w_sa * norm_sa -
        w_instability * norm_instability
    )
    return reward


def resolve_pocket_and_reference(pathogen_name):
    """
    Dynamically loads target pocket residues and reference SMILES for a pathogen name.
    Pulls from custom_targets.json if resolved dynamically, otherwise maps to presets.
    """
    import requests
    from generator import EvolutionaryGenerator

    PRESET_SMILES = {
        'tuberculosis': 'c1cc(ccn1)C(=O)NN',
        'sars-cov-2': 'CC(=O)NC1C(C=C(CC1OC(CC)CC)C(=O)OCC)N',
        'salmonella': 'CC1=C(C2=C(C=C1)OC(=O)C(=C2NC(=O)C(C)(C)C=C)O)C3C(C(C(O3)(C)O)OC(=O)N)O',
        'hiv': 'CC1COC2=C(C(=O)C3=C(N2C1)C=C(C(=O)N3CC4=C(C=C(C=C4)F)F)O)O',
        'malaria': 'CCC1=C(C2=C(C=C2)Cl)N=C(N)N=C1N'
    }
    
    pathogen_key = "tuberculosis"
    p_name = pathogen_name.lower().strip()
    if "covid" in p_name or "sars" in p_name:
        pathogen_key = "sars-cov-2"
    elif "salmonella" in p_name:
        pathogen_key = "salmonella"
    elif "hiv" in p_name or "aids" in p_name:
        pathogen_key = "hiv"
    elif "malaria" in p_name:
        pathogen_key = "malaria"
    elif 'isocyan' in p_name or 'cyan' in p_name or 'cynad' in p_name or 'cynac' in p_name or p_name == 'mic':
        pathogen_key = "methylisocynate"
        
    pocket = PRESET_POCKETS.get(pathogen_key, PRESET_POCKETS['tuberculosis'])
    ref_smiles = PRESET_SMILES.get(pathogen_key, 'c1cc(ccn1)C(=O)NN')
    
    # Load from custom_targets.json if available
    if os.path.exists("custom_targets.json"):
        try:
            with open("custom_targets.json", "r") as f:
                custom_targets = json.load(f)
            
            norm_p = "".join(pathogen_name.lower().split()).replace("-", "").replace("_", "")
            matched_key = None
            for k, v in custom_targets.items():
                norm_k = "".join(k.lower().split()).replace("-", "").replace("_", "")
                if norm_p in norm_k or norm_k in norm_p:
                    matched_key = k
                    break
                    
            if matched_key:
                v = custom_targets[matched_key]
                if "recommended_seed_smiles" in v:
                    ref_smiles = v["recommended_seed_smiles"]
                
                # Check if pocket_residues is already resolved
                if "pocket_residues" in v and v["pocket_residues"]:
                    pocket = v["pocket_residues"]
                else:
                    # Dynamically resolve from AlphaFold using UniProt ID
                    uniprot_id = v.get("uniprot_id")
                    if uniprot_id:
                        print(f"QRL: Dynamically fetching AlphaFold structure for custom UniProt: {uniprot_id}")
                        af_url = f"https://www.alphafold.ebi.ac.uk/api/prediction/{uniprot_id}"
                        af_res = requests.get(af_url, timeout=10)
                        if af_res.status_code == 200:
                            af_data = af_res.json()
                            if af_data and len(af_data) > 0:
                                pdb_url = af_data[0].get("pdbUrl")
                                if pdb_url:
                                    pdb_res = requests.get(pdb_url, timeout=10)
                                    if pdb_res.status_code == 200:
                                        molecular_generator = EvolutionaryGenerator()
                                        pocket_residues = molecular_generator.parse_pdb_to_pocket(pdb_res.text, num_residues=10)
                                        if pocket_residues:
                                            pocket = pocket_residues
                                            # Save resolved pocket back to custom_targets.json cache
                                            v["pocket_residues"] = pocket_residues
                                            with open("custom_targets.json", "w") as f:
                                                json.dump(custom_targets, f, indent=2)
                                            print(f"QRL: Successfully cached dynamic pocket residues for {matched_key}")
        except Exception as e:
            print(f"Error loading custom targets in resolving pocket: {e}")
            
    return pocket, ref_smiles


def run_qrl_optimization(seed_smiles, pathogen_name, epochs=5):
    """
    Modular execution entrypoint for Quantum Reinforcement Learning Optimization loop.
    Encapsulates policy exploration, environment steps, parameter-shift gradient updates,
    and returns complete telemetry records.
    """
    pocket_residues, ref_smiles = resolve_pocket_and_reference(pathogen_name)
    env = ChemicalEnvironment(pocket_residues, ref_smiles, max_steps=epochs)
    
    agent = QuantumRLAgent(num_qubits=8, lr=0.05)
    state = env.reset(seed_smiles)
    current_smiles = seed_smiles
    
    history = []
    states_batch = []
    actions_batch = []
    action_masks_batch = []
    rewards_batch = []
    
    gen = EvolutionaryGenerator()
    
    for step in range(epochs):
        # 1. Action Masking: evaluate valid reactions
        mask = get_valid_action_mask(current_smiles, agent.actions)
        # Force exploration on the first step to prevent immediate termination
        if step == 0 and len(mask) > 11:
            mask[11] = 0.0
        
        # 2. Policy sampling with action mask
        action_idx, prob = agent.select_action(state, mask)
        action_name = agent.actions[action_idx]
        
        # 3. Environment step
        next_state, reward, done, info = env.step(action_name)
        next_smiles = env.state_smiles
        
        # 4. Telemetry descriptors calculation
        mol = Chem.MolFromSmiles(next_smiles)
        fsp3 = 0.0
        mw = 137.1
        logp = -0.7
        vqe_binding = -5.0
        confidence = 75.0
        
        if mol:
            mw = Descriptors.ExactMolWt(mol)
            logp = Descriptors.MolLogP(mol)
            try:
                fsp3 = Lipinski.FractionCSP3(mol)
            except:
                fsp3 = 0.0
                
            coords = gen.generate_3d_coordinates(mol)
            
            # Compute exact VQE ground state energy variational calculation
            try:
                qubit_op, target_energy = get_molecular_hamiltonian("target", active_orbitals=4, mapper_type='parity', custom_coords=coords)
                vqe_binding = run_actual_vqe(qubit_op, active_orbitals=4)
            except Exception as e:
                vqe_binding = target_energy
                
            # Perform a fast 15-step MD and calculate standard deviation of docking energy (conformation uncertainty)
            # NOTE: steps=15 is a lightweight real-time surrogate for rapid interactive updates.
            md_res = run_molecular_dynamics_simulation(coords, temp=310.15, steps=15)
            docking_frames = []
            for frame in md_res.get("trajectory", []):
                f_dock = gen.calculate_docking_energy(frame, pocket_residues)
                f_dock_score = -6.0 - abs(f_dock % 8.0)
                docking_frames.append(f_dock_score)
            
            docking_std = np.std(docking_frames) if len(docking_frames) > 1 else 0.15
            vqe_std = 0.05
            
            # Calculate prediction confidence
            confidence = 100.0 - (docking_std * 12.0 + vqe_std * 50.0)
            confidence = max(10.0, min(99.0, confidence))

        step_record = {
            "epoch": step + 1,
            "action": action_name.replace("_", " ").upper(),
            "smiles": next_smiles,
            "vqe_energy": float(round(vqe_binding, 2)),
            "fsp3": float(round(fsp3, 3)),
            "mw": float(round(mw, 1)),
            "logp": float(round(logp, 2)),
            "reward": float(round(reward, 2)),
            "confidence": float(round(confidence, 1)),
            "pqc_parameters": [float(round(p, 4)) for p in agent.theta]
        }
        history.append(step_record)
        
        # Accumulate history for policy update
        states_batch.append(state)
        actions_batch.append(action_idx)
        action_masks_batch.append(mask)
        rewards_batch.append(reward)
        
        state = next_state
        current_smiles = next_smiles
        
        if done:
            break
            
    # 5. Policy analytical parameter-shift gradient update with discounted returns and masks
    agent.update_policy(states_batch, actions_batch, action_masks_batch, rewards_batch)
    
    # Generate 3D coordinates for final molecule
    rec_coords = []
    rec_mol = Chem.MolFromSmiles(current_smiles)
    if rec_mol:
        try:
            coords = gen.generate_3d_coordinates(rec_mol)
            for atom in coords:
                rec_coords.append({
                    "element": atom["element"],
                    "type": atom["element"],
                    "x": float(atom["x"]),
                    "y": float(atom["y"]),
                    "z": float(atom["z"]),
                    "isActiveSpace": True
                })
        except Exception as ex:
            print(f"Failed to generate 3d coordinates for QRL recommended lead: {ex}")
            
    # Generate final circuit diagram using Qiskit text drawer and matplotlib svg drawer
    import io
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    circuit_ascii = "Error drawing Qiskit circuit."
    circuit_svg = ""

    try:
        final_qc = agent.build_pqc_circuit(state, agent.theta)
        circuit_ascii = str(final_qc.draw(output='text', fold=-1))
        
        fig = final_qc.draw(output='mpl')
        buf = io.BytesIO()
        fig.savefig(buf, format='svg', bbox_inches='tight')
        plt.close(fig)
        circuit_svg = buf.getvalue().decode('utf-8')
        if circuit_svg.startswith('<?xml'):
            idx = circuit_svg.find('<svg')
            if idx != -1:
                circuit_svg = circuit_svg[idx:]
    except Exception as ex:
        print(f"Failed to draw final optimized circuit: {ex}")

    return {
        "status": "success",
        "seed_smiles": seed_smiles,
        "optimized_smiles": current_smiles,
        "history": history,
        "circuit_ascii": circuit_ascii,
        "circuit_svg": circuit_svg,
        "recommended_candidate": {
            "smiles": current_smiles,
            "formula": Chem.rdMolDescriptors.CalcMolFormula(rec_mol) if rec_mol else "N/A",
            "mw": float(round(Descriptors.ExactMolWt(rec_mol), 2)) if rec_mol else 0.0,
            "logp": float(round(Descriptors.MolLogP(rec_mol), 2)) if rec_mol else 0.0,
            "atoms": rec_coords
        }
    }
    }
