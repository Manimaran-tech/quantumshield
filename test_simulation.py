from simulation import run_vqe_simulation, get_dynamic_molecular_properties

def test_vqe_runs():
    print("Testing pre-defined hydrazine molecule...")
    res1 = run_vqe_simulation(
        molecule_id='hydrazine',
        active_orbitals=4,
        ansatz_type='custom',
        noise_level=10.0,
        error_mitigation=True,
        mapper='parity'
    )
    print("Pre-defined run complete:")
    print(f"  Final energy: {res1['final_energy']} Hartree")
    print(f"  Exact FCI energy: {res1['fci_energy']} Hartree")
    print(f"  Chemical Accuracy difference: {abs(res1['final_energy'] - res1['fci_energy'])} Hartree")
    print(f"  Binding energy: {res1['binding_energy']} kcal/mol")
    print(f"  Qubits required: {res1['qubits']}")
    print(f"  Steps run: {len(res1['history'])}")

    print("\nTesting custom coordinates...")
    custom_coords = [
        {"element": "H", "x": 0.0, "y": 0.0, "z": 0.0},
        {"element": "H", "x": 0.0, "y": 0.0, "z": 0.74}
    ]
    res2 = run_vqe_simulation(
        molecule_id='custom',
        active_orbitals=2,
        ansatz_type='custom',
        noise_level=5.0,
        error_mitigation=True,
        mapper='jw',
        custom_coords=custom_coords
    )
    print("Custom coordinate run complete:")
    print(f"  Final energy: {res2['final_energy']} Hartree")
    print(f"  Exact FCI energy: {res2['fci_energy']} Hartree")
    print(f"  Binding energy: {res2['binding_energy']} kcal/mol")

def test_toxicity_and_gap_classification():
    print("\nTesting toxicity and gap classification...")
    
    # 1. Test HCN (Toxic small molecule)
    hcn_coords = [
        {"element": "H", "x": 0.0, "y": 0.0, "z": 0.0},
        {"element": "C", "x": 0.0, "y": 0.0, "z": 1.06},
        {"element": "N", "x": 0.0, "y": 0.0, "z": 2.21}
    ]
    props_hcn = get_dynamic_molecular_properties(hcn_coords)
    print(f"HCN properties: Gap={props_hcn['gap_ev']:.2f} eV, Toxicity='{props_hcn['toxicity']}', is_toxic={props_hcn['is_toxic']}")
    assert props_hcn['is_toxic'] == True, "HCN should be flagged as toxic!"
    assert props_hcn['gap_ev'] < 8.0, "HCN gap should be below 8.0 eV!"

    # 2. Test safe, large organic candidate (simulated evolved structure)
    # 15 atoms representing a stable organic ring/chain structure
    safe_coords = [
        {"element": "C", "x": 0.0, "y": 0.0, "z": 0.0},
        {"element": "C", "x": 1.4, "y": 0.0, "z": 0.0},
        {"element": "C", "x": 2.1, "y": 1.2, "z": 0.0},
        {"element": "C", "x": 1.4, "y": 2.4, "z": 0.0},
        {"element": "C", "x": 0.0, "y": 2.4, "z": 0.0},
        {"element": "C", "x": -0.7, "y": 1.2, "z": 0.0},
        {"element": "O", "x": -2.1, "y": 1.2, "z": 0.0},
        {"element": "H", "x": -0.5, "y": -0.9, "z": 0.0},
        {"element": "H", "x": 1.9, "y": -0.9, "z": 0.0},
        {"element": "H", "x": 3.2, "y": 1.2, "z": 0.0},
        {"element": "H", "x": 1.9, "y": 3.3, "z": 0.0},
        {"element": "H", "x": -0.5, "y": 3.3, "z": 0.0},
        {"element": "N", "x": 2.1, "y": 3.6, "z": 0.0},
        {"element": "H", "x": 3.1, "y": 3.6, "z": 0.0},
        {"element": "H", "x": 1.7, "y": 4.5, "z": 0.0}
    ]
    props_safe = get_dynamic_molecular_properties(safe_coords)
    print(f"Safe Organic properties: Gap={props_safe['gap_ev']:.2f} eV, Toxicity='{props_safe['toxicity']}', is_toxic={props_safe['is_toxic']}")
    assert props_safe['is_toxic'] == False, "Safe organic candidate should not be flagged as toxic!"
    assert 8.0 <= props_safe['gap_ev'] <= 20.0, "Safe organic candidate gap should be in the stable therapeutic window (8-20 eV)!"
    
    # 3. Test Benzene (Toxic solvent)
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
    props_benzene = get_dynamic_molecular_properties(benzene_coords)
    print(f"Benzene properties: Gap={props_benzene['gap_ev']:.2f} eV, Toxicity='{props_benzene['toxicity']}', is_toxic={props_benzene['is_toxic']}")
    assert props_benzene['is_toxic'] == True, "Benzene should be flagged as toxic!"
    assert props_benzene['gap_ev'] < 8.0, "Benzene gap should be below 8.0 eV!"
    
    # 4. Test Nitrobenzene (Toxic flat aromatic toxicophore)
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
    props_nb = get_dynamic_molecular_properties(nitrobenzene_coords)
    print(f"Nitrobenzene properties: Gap={props_nb['gap_ev']:.2f} eV, Toxicity='{props_nb['toxicity']}', is_toxic={props_nb['is_toxic']}")
    assert props_nb['is_toxic'] == True, "Nitrobenzene should be flagged as toxic!"
    assert props_nb['gap_ev'] < 8.0, "Nitrobenzene gap should be below 8.0 eV!"
    
    print("Toxicity and gap classification tests passed successfully!")

def test_dna_interaction():
    from simulation import analyze_dna_interaction
    print("\nTesting DNA interaction and genotoxicity screening...")
    
    # Test INH-Quantum-01 (Safe)
    res_inh = analyze_dna_interaction('inh-q1')
    print(f"INH-Q1: Compatibility={res_inh['compatibility_score']}%, Mode='{res_inh['binding_mode']}', Ames={res_inh['ames_prediction']}")
    assert res_inh['compatibility_score'] >= 80, "INH-Q1 should have high DNA compatibility"
    assert res_inh['binding_mode'] == 'major_groove', "INH-Q1 should bind in the major groove"
    assert res_inh['ames_prediction'] == 'negative', "INH-Q1 should be Ames negative"

    # Test pyridine (intercalator / toxic)
    res_pyr = analyze_dna_interaction('pyridine')
    print(f"Pyridine: Compatibility={res_pyr['compatibility_score']}%, Mode='{res_pyr['binding_mode']}', Ames={res_pyr['ames_prediction']}")
    assert res_pyr['compatibility_score'] < 30, "Pyridine should have lower DNA compatibility"
    assert res_pyr['binding_mode'] == 'intercalation', "Pyridine should show intercalation risk"
    
    # Test carbon-monoxide (toxic gas)
    res_co = analyze_dna_interaction('carbon-monoxide')
    print(f"CO: Compatibility={res_co['compatibility_score']}%, Mode='{res_co['binding_mode']}', Ames={res_co['ames_prediction']}")
    assert res_co['compatibility_score'] < 40, "Carbon monoxide should have very low DNA compatibility"
    assert res_co['binding_mode'] == 'non_binder', "Carbon monoxide should be a non-binder"
    
    # Test water (non-binder)
    res_h2o = analyze_dna_interaction('water')
    print(f"Water: Compatibility={res_h2o['compatibility_score']}%, Mode='{res_h2o['binding_mode']}', Ames={res_h2o['ames_prediction']}")
    assert res_h2o['binding_mode'] == 'non_binder', "Water should be classified as a non-binder"
    assert res_h2o['compatibility_score'] >= 70, "Water should have high DNA compatibility"
    
    print("DNA interaction backend tests passed successfully!")

def test_qpu_codesign():
    from simulation import calculate_qpu_codesign, run_vqe_simulation
    print("\nTesting QPU Co-Design calculations and constraints...")

    # 1. Test parameter extraction on Silicon substrate
    silicon_qpu = calculate_qpu_codesign(
        topology='heavy-hex',
        qubit_count=6,
        pocket_size=100.0,
        meander_length=5.0,
        dielectric='silicon',
        tunable_couplers=True,
        scaling_resolution='truncation'
    )
    print(f"Silicon QPU: avg_T1={silicon_qpu['global_metrics']['avg_t1_us']} us, avg_T2={silicon_qpu['global_metrics']['avg_t2_us']} us")
    assert 50 <= silicon_qpu['global_metrics']['avg_t1_us'] <= 80, "Silicon T1 should be around ~65 μs"
    assert silicon_qpu['global_metrics']['topology'] == 'heavy-hex'
    assert len(silicon_qpu['nodes']) == 6

    # 2. Test parameter extraction on Sapphire substrate (higher coherence)
    sapphire_qpu = calculate_qpu_codesign(
        topology='star',
        qubit_count=4,
        pocket_size=120.0,
        meander_length=6.0,
        dielectric='sapphire',
        tunable_couplers=False,
        scaling_resolution='cutting'
    )
    print(f"Sapphire QPU: avg_T1={sapphire_qpu['global_metrics']['avg_t1_us']} us, avg_T2={sapphire_qpu['global_metrics']['avg_t2_us']} us")
    assert 100 <= sapphire_qpu['global_metrics']['avg_t1_us'] <= 160, "Sapphire T1 should be around ~140 μs"
    assert len(sapphire_qpu['nodes']) == 4

    # 3. Test VQE with active QPU Co-Design (Line topology: high SWAP factor, Truncation resolution)
    res_trunc = run_vqe_simulation(
        molecule_id='hydrazine',
        active_orbitals=4,  # requires 6 qubits (parity mapper: max(2, 4*2-2) = 6)
        ansatz_type='custom',
        noise_level=10.0,
        error_mitigation=True,
        mapper='parity',
        codesign_active=True,
        qpu_topology='line',
        qpu_qubits=4,      # Less than required 6 qubits -> should trigger truncation
        qpu_pocket_size=100.0,
        qpu_meander_length=5.0,
        qpu_dielectric='silicon',
        qpu_tunable_couplers=True,
        qpu_scaling_resolution='truncation'
    )
    print(f"Line QPU (Truncation): Qubits Warning='{res_trunc['qubits_warning']}', SWAP Factor={res_trunc['swap_factor']}, Qubits used={res_trunc['qubits']}")
    assert res_trunc['swap_factor'] == 2.4, "Line topology should have a 2.4 SWAP penalty factor"
    assert "truncated" in res_trunc['qubits_warning'].lower(), "Should warning about active space truncation"
    assert res_trunc['qubits'] <= 4, "Should truncate active space to fit 4 physical qubits"

    # 4. Test VQE with active QPU Co-Design (Star topology: no SWAP factor, Qubit Cutting resolution)
    res_cutting = run_vqe_simulation(
        molecule_id='hydrazine',
        active_orbitals=4,  # requires 6 qubits
        ansatz_type='custom',
        noise_level=10.0,
        error_mitigation=True,
        mapper='parity',
        codesign_active=True,
        qpu_topology='star',
        qpu_qubits=4,      # Less than required 6 qubits -> should trigger cutting
        qpu_pocket_size=100.0,
        qpu_meander_length=5.0,
        qpu_dielectric='silicon',
        qpu_tunable_couplers=True,
        qpu_scaling_resolution='cutting'
    )
    print(f"Star QPU (Cutting): Qubits Warning='{res_cutting['qubits_warning']}', SWAP Factor={res_cutting['swap_factor']}, Qubits simulated={res_cutting['qubits']}")
    assert res_cutting['swap_factor'] == 1.0, "Star topology should have a 1.0 SWAP factor (direct coupling)"
    assert "circuit knitting" in res_cutting['qubits_warning'].lower() or "cutqc" in res_cutting['qubits_warning'].lower(), "Should flag circuit knitting usage"
    assert res_cutting['qubits'] == 6, "Qubit cutting should simulate all 6 qubits virtualized"

    print("QPU Co-Design backend tests passed successfully!")

if __name__ == '__main__':
    test_vqe_runs()
    test_toxicity_and_gap_classification()
    test_dna_interaction()
    test_qpu_codesign()


