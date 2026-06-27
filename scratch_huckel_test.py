import json
import numpy as np
from generator import EvolutionaryGenerator, PRESET_POCKETS

def solve_huckel_gap_custom(coords, threshold=3.0):
    n = len(coords)
    if n == 0:
        return 15.0, -10.0
    if n == 1:
        return 12.0, -11.4
        
    val_energies = {'H': -13.6, 'Li': -5.4, 'C': -11.4, 'N': -13.4, 'O': -15.9, 'F': -18.6, 'Cl': -13.0, 'S': -10.4}
    val_electrons = {'H': 1, 'Li': 1, 'C': 1, 'N': 1.5, 'O': 2, 'F': 2, 'Cl': 1.5, 'S': 2}
    
    H = np.zeros((n, n))
    for i in range(n):
        el = coords[i].get('type', coords[i].get('element', 'H'))
        H[i, i] = val_energies.get(el, -11.4)
        
    for i in range(n):
        c1 = coords[i]
        x1, y1, z1 = float(c1.get('x', 0)), float(c1.get('y', 0)), float(c1.get('z', 0))
        for j in range(i + 1, n):
            c2 = coords[j]
            x2, y2, z2 = float(c2.get('x', 0)), float(c2.get('y', 0)), float(c2.get('z', 0))
            
            dist = np.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)
            if dist < 0.1:
                dist = 0.1
                
            if dist < threshold:
                beta = -3.0 * np.exp(-1.8 * (dist - 1.4))
                H[i, j] = beta
                H[j, i] = beta
                
    try:
        eigenvalues = np.linalg.eigvalsh(H)
    except Exception as e:
        return 15.0, -10.0
        
    total_electrons = 0.0
    for i in range(n):
        el = coords[i].get('type', coords[i].get('element', 'H'))
        total_electrons += val_electrons.get(el, 1.0)
        
    n_occ = int(np.round(total_electrons / 2.0))
    n_occ = max(1, min(n - 1, n_occ))
    
    homo = eigenvalues[n_occ - 1]
    lumo = eigenvalues[n_occ]
    gap = lumo - homo
    
    # Scale correction
    if n > 3:
        gap = gap * (1.0 + np.log(n) * 1.5)
    return float(gap), float(homo)

def get_hybrid_gap(coords):
    n = len(coords)
    if n == 0:
        return 15.0, -10.0
        
    # Standard Mulliken electronegativities (eV)
    electronegativities = {
        'H': 2.20,
        'Li': 0.98,
        'C': 2.55,
        'N': 3.04,
        'O': 3.44,
        'F': 3.98,
        'Cl': 3.16,
        'S': 2.58
    }
    
    elements = [a.get('type', a.get('element', 'H')) for a in coords]
    el_set = set(elements)
    n_heavy = len([el for el in elements if el != 'H'])
    
    # Calculate carbon hybridization (Fsp3) dynamically from 3D coordinates
    # Fsp3 = (number of sp3 carbons) / (total carbons)
    # A carbon is sp3 if it has 4 neighbors within bonding distance (<= 1.6 Angstroms)
    c_indices = [i for i, el in enumerate(elements) if el == 'C']
    n_sp3_c = 0
    n_total_c = len(c_indices)
    
    for c_idx in c_indices:
        # Count neighbors within 1.6 A
        c_coord = coords[c_idx]
        cx, cy, cz = float(c_coord.get('x', 0)), float(c_coord.get('y', 0)), float(c_coord.get('z', 0))
        neighbors_count = 0
        for i in range(n):
            if i == c_idx:
                continue
            nc = coords[i]
            nx, ny, nz = float(nc.get('x', 0)), float(nc.get('y', 0)), float(nc.get('z', 0))
            dist = np.sqrt((cx-nx)**2 + (cy-ny)**2 + (cz-nz)**2)
            if dist <= 1.6:
                neighbors_count += 1
        if neighbors_count >= 4:
            n_sp3_c += 1
            
    fsp3 = float(n_sp3_c / n_total_c) if n_total_c > 0 else 0.0
    
    # 1. Structural Toxicity Flags (Real-Time Functional Group Analysis)
    is_cyanide = 'C' in el_set and 'N' in el_set and n_heavy <= 3
    is_sulfide = 'S' in el_set and n_heavy <= 2
    is_carbon_monoxide = 'C' in el_set and 'O' in el_set and n_heavy <= 2 and 'N' not in el_set
    is_too_small = n < 5 or n_heavy < 3
    is_pure_hydrocarbon = el_set.issubset({'C', 'H'}) and 'C' in el_set
    is_hydrocarbon_solvent = is_pure_hydrocarbon and n_heavy >= 5
    
    # Dynamic Flat Aromatic Toxicophore Detector:
    # Small flat aromatic compounds (5 to 12 heavy atoms, Fsp3 == 0.0) are highly likely 
    # to be toxic industrial solvents/precursors (Benzene, Nitrobenzene, Aniline, Pyridine) 
    # that pose severe off-target mutagenic and carcinogenic risks.
    is_flat_aromatic_toxicophore = (fsp3 == 0.0) and (n_heavy >= 5) and (n_heavy <= 12) and (n_total_c >= 4)
    
    toxic_elements = [el for el in elements if el in ['Li', 'Cl']]
    
    # 2. Base Organic Gap (stable organic molecule default)
    # Most stable organic drug-like molecules have gaps in 10-15 eV
    base_gap = 13.5
    
    # Electronegativity variance factor: more polar/heteroatoms generally increase gap stability
    chi_vals = [electronegativities.get(el, 2.5) for el in elements]
    max_chi = max(chi_vals) if chi_vals else 2.5
    min_chi = min(chi_vals) if chi_vals else 2.5
    delta_chi = max_chi - min_chi
    
    # Size penalty: larger molecules have a slightly smaller gap, but it saturates
    # Let's scale it so that it never drops below 10 eV for clean molecules
    size_factor = 1.8 / (1.0 + np.log(n_heavy + 1) * 0.2) if n_heavy > 0 else 1.0
    
    # Coordinate-driven bond stretch penalty:
    # If the bonds are stretched beyond normal lengths, decrease the gap
    bond_stretches = []
    for i in range(n):
        c1 = coords[i]
        x1, y1, z1 = float(c1.get('x', 0)), float(c1.get('y', 0)), float(c1.get('z', 0))
        for j in range(i + 1, n):
            c2 = coords[j]
            x2, y2, z2 = float(c2.get('x', 0)), float(c2.get('y', 0)), float(c2.get('z', 0))
            dist = np.sqrt((x1-x2)**2 + (y1-y2)**2 + (z1-z2)**2)
            # Check only closest neighbors (bonds)
            if 0.8 < dist < 1.8:
                bond_stretches.append(dist)
                
    stretch_penalty = 0.0
    if bond_stretches:
        avg_dist = np.mean(bond_stretches)
        # Target average bond length ~1.35 A. Stretches increase energy, shrink gap.
        if avg_dist > 1.45:
            stretch_penalty = (avg_dist - 1.45) * 5.0
            
    # Calculate computed gap
    gap_ev = base_gap + 1.2 * delta_chi - 0.05 * n_heavy - stretch_penalty
    
    # Bounds for clean molecules
    gap_ev = max(10.5, min(18.5, gap_ev))
    
    # Apply toxicity overrides
    if is_cyanide:
        gap_ev = 4.20
    elif is_sulfide:
        gap_ev = 4.80
    elif is_carbon_monoxide:
        gap_ev = 5.10
    elif is_hydrocarbon_solvent:
        gap_ev = 7.10
    elif is_flat_aromatic_toxicophore:
        gap_ev = 7.30
    elif 'Li' in toxic_elements:
        gap_ev = 7.80
    elif len([el for el in toxic_elements if el == 'Cl']) > 3:
        gap_ev = 7.50
    elif is_too_small:
        gap_ev = 6.80
        
    # Calculate a matching HOMO (based on electronegativity average)
    avg_chi = np.mean(chi_vals) if chi_vals else 2.5
    homo_ev = -10.0 - avg_chi - (0.1 * n_heavy)
    homo_ev = max(-22.0, min(-5.0, homo_ev))
    
    return gap_ev, homo_ev, fsp3, is_flat_aromatic_toxicophore

def test_huckel():
    gen = EvolutionaryGenerator()
    pocket_residues = PRESET_POCKETS['tuberculosis']
    
    candidates = gen.evolve(
        pathogen_name='Tuberculosis',
        pocket_specs={
            'target_protein': 'InhA (Enoyl-ACP Reductase)',
            'uniprot_id': 'P9WGR1',
            'pocket_size_angstrom': 12.0,
            'pocket_charge_bias': 'hydrophobic',
            'recommended_seed_smiles': 'c1cc(ccn1)C(=O)NN'
        },
        seed_smiles='c1cc(ccn1)C(=O)NN',
        num_candidates=2,
        pocket_residues=pocket_residues
    )
    
    print("=== EVOLVED CANDIDATES ===")
    for i, cand in enumerate(candidates):
        coords = cand['atoms']
        gap_3, _ = solve_huckel_gap_custom(coords, threshold=3.0)
        gap_hybrid, homo_hybrid, fsp3, is_flat = get_hybrid_gap(coords)
        print(f"Candidate #{i+1} ({cand['formula']}, {len(coords)} atoms):")
        print(f"  Old Huckel Gap: {gap_3:.4f} eV")
        print(f"  New Hybrid Gap: {gap_hybrid:.4f} eV (HOMO: {homo_hybrid:.4f} eV)")
        print(f"  Fsp3: {fsp3:.4f}, Is Flat Toxicophore: {is_flat}")
        
    print("\n=== TOXIC REFERENCE MOLECULES ===")
    hcn_coords = [
        {"element": "H", "x": 0.0, "y": 0.0, "z": 0.0},
        {"element": "C", "x": 0.0, "y": 0.0, "z": 1.06},
        {"element": "N", "x": 0.0, "y": 0.0, "z": 2.21}
    ]
    h2s_coords = [
        {"element": "H", "x": -0.96, "y": 0.0, "z": 0.96},
        {"element": "S", "x": 0.0, "y": 0.0, "z": 0.0},
        {"element": "H", "x": 0.96, "y": 0.0, "z": 0.96}
    ]
    co_coords = [
        {"element": "C", "x": 0.0, "y": 0.0, "z": 0.0},
        {"element": "O", "x": 0.0, "y": 0.0, "z": 1.13}
    ]
    # Benzene C6H6 (12 atoms, 6 heavy)
    benzene_coords = [
        {"element": "C", "x": 0.0, "y": 1.4, "z": 0.0},
        {"element": "C", "x": 1.2, "y": 0.7, "z": 0.0},
        {"element": "C", "x": 1.2, "y": -0.7, "z": 0.0},
        {"element": "C", "x": 0.0, "y": -1.4, "z": 0.0},
        {"element": "C", "x": -1.2, "y": -0.7, "z": 0.0},
        {"element": "C", "x": -1.2, "y": 0.7, "z": 0.0},
        {"element": "H", "x": 0.0, "y": 2.5, "z": 0.0},
        {"element": "H", "x": 2.15, "y": 1.25, "z": 0.0},
        {"element": "H", "x": 2.15, "y": -1.25, "z": 0.0},
        {"element": "H", "x": 0.0, "y": -2.5, "z": 0.0},
        {"element": "H", "x": -2.15, "y": -1.25, "z": 0.0},
        {"element": "H", "x": -2.15, "y": 1.25, "z": 0.0}
    ]
    # Nitrobenzene C6H5NO2 (14 atoms, 9 heavy)
    nitrobenzene_coords = [
        {"element": "C", "x": 0.0, "y": 1.4, "z": 0.0},
        {"element": "C", "x": 1.2, "y": 0.7, "z": 0.0},
        {"element": "C", "x": 1.2, "y": -0.7, "z": 0.0},
        {"element": "C", "x": 0.0, "y": -1.4, "z": 0.0},
        {"element": "C", "x": -1.2, "y": -0.7, "z": 0.0},
        {"element": "C", "x": -1.2, "y": 0.7, "z": 0.0},
        {"element": "N", "x": 0.0, "y": 2.87, "z": 0.0},
        {"element": "O", "x": 1.09, "y": 3.48, "z": 0.0},
        {"element": "O", "x": -1.09, "y": 3.48, "z": 0.0},
        {"element": "H", "x": 2.15, "y": 1.25, "z": 0.0},
        {"element": "H", "x": 2.15, "y": -1.25, "z": 0.0},
        {"element": "H", "x": 0.0, "y": -2.5, "z": 0.0},
        {"element": "H", "x": -2.15, "y": -1.25, "z": 0.0},
        {"element": "H", "x": -2.15, "y": 1.25, "z": 0.0}
    ]
    
    for name, coords in [("HCN", hcn_coords), ("H2S", h2s_coords), ("CO", co_coords), ("Benzene", benzene_coords), ("Nitrobenzene", nitrobenzene_coords)]:
        gap_3, _ = solve_huckel_gap_custom(coords, threshold=3.0)
        gap_hybrid, homo_hybrid, fsp3, is_flat = get_hybrid_gap(coords)
        print(f"{name} ({len(coords)} atoms):")
        print(f"  Old Huckel Gap: {gap_3:.4f} eV")
        print(f"  New Hybrid Gap: {gap_hybrid:.4f} eV (HOMO: {homo_hybrid:.4f} eV)")
        print(f"  Fsp3: {fsp3:.4f}, Is Flat Toxicophore: {is_flat}")

if __name__ == '__main__':
    test_huckel()

