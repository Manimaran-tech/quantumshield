# Copyright 2026 QuantumShield Team
# Licensed under the Apache License, Version 2.0

import os
import sys
import numpy as np

try:
    import torch
except ImportError:
    torch = None

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Lipinski, RDConfig
    from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams
except ImportError:
    Chem = None
    Descriptors = Lipinski = RDConfig = None
    FilterCatalog = FilterCatalogParams = None


def load_from_file(file_path, device):
    """
    Loads a PyTorch model checkpoint.
    """
    if torch is None:
        raise RuntimeError("PyTorch is required to load neural network checkpoints.")
    model = torch.load(file_path, weights_only=False, map_location=device)
    model._device = device
    return model


# ============================================================================
# Peer-Reviewed Synthetic Accessibility (Ertl & Schuffenhauer 2009)
# ============================================================================
_SASCORER = None

def get_sascorer():
    """Lazily loads the official RDKit Contrib SA_Score module."""
    global _SASCORER
    if _SASCORER is not None:
        return _SASCORER
    if RDConfig is None:
        return None
    try:
        sa_dir = os.path.join(RDConfig.RDContribDir, 'SA_Score')
        if sa_dir not in sys.path:
            sys.path.append(sa_dir)
        import sascorer
        _SASCORER = sascorer
        return _SASCORER
    except Exception as ex:
        print(f"[Cheminformatics] Warning: RDKit sascorer unavailable ({ex}), using structural fallback.")
        return None


def calculate_sascore(mol):
    """
    Calculates Synthetic Accessibility (SA) Score (1.0 = easiest to synthesize, 10.0 = hardest).
    Uses the peer-reviewed Ertl & Schuffenhauer (2009) method when available, with an
    analytical fallback based on chiral centers, ring complexity, and molecular weight.
    """
    if mol is None:
        return 5.0

    scorer = get_sascorer()
    if scorer is not None:
        try:
            val = float(scorer.calculateScore(mol))
            return float(round(max(1.0, min(10.0, val)), 2))
        except Exception:
            pass

    # Analytical fallback based on topological and stereochemical complexity
    try:
        n_chiral = len(Chem.FindMolChiralCenters(mol, includeUnassigned=True))
        n_rings = Lipinski.RingCount(mol)
        rotb = Lipinski.NumRotatableBonds(mol)
        mw = Descriptors.ExactMolWt(mol)
        score = 1.0 + (0.005 * mw) + (0.15 * rotb) + (0.5 * n_chiral) + (0.3 * n_rings)
        return float(round(max(1.0, min(10.0, score)), 2))
    except Exception:
        return 3.5


# ============================================================================
# Pan-Assay Interference Compounds (PAINS) FilterCatalog
# ============================================================================
_PAINS_CATALOG = None

def get_pains_catalog():
    """Lazily initializes the RDKit PAINS FilterCatalog (480 validated SMARTS filters)."""
    global _PAINS_CATALOG
    if _PAINS_CATALOG is not None:
        return _PAINS_CATALOG
    if FilterCatalogParams is None or FilterCatalog is None:
        return None
    try:
        params = FilterCatalogParams()
        params.AddCatalog(FilterCatalogParams.FilterCatalogs.PAINS)
        _PAINS_CATALOG = FilterCatalog(params)
        return _PAINS_CATALOG
    except Exception as ex:
        print(f"[Cheminformatics] Warning: PAINS FilterCatalog unavailable: {ex}")
        return None


def check_pains(mol):
    """
    Evaluates whether a molecule contains PAINS alerts.
    Returns: (is_pains: bool, alert_descriptions: list[str])
    """
    if mol is None:
        return False, []
    catalog = get_pains_catalog()
    if catalog is None:
        return False, []
    try:
        matches = catalog.GetMatches(mol)
        if matches:
            reasons = [m.GetDescription() for m in matches]
            return True, reasons
        return False, []
    except Exception:
        return False, []


# ============================================================================
# In-Silico Hill-Langmuir Pharmacodynamic Equilibrium Model
# ============================================================================
def calculate_hill_langmuir_binding(kd_uM, concentrations_uM=None, hill_coefficient=1.0):
    """
    Calculates the theoretical equilibrium fraction of receptor bound (0.0 to 1.0)
    using the classical Hill-Langmuir equation:
        theta = [L]^n / (Kd^n + [L]^n)
    
    Standard physical concentrations default to [0.01, 0.1, 1.0, 10.0, 100.0] uM,
    ensuring that high-affinity vs low-affinity drugs produce distinct, discriminative curves.
    """
    if concentrations_uM is None:
        concentrations_uM = [0.01, 0.1, 1.0, 10.0, 100.0]

    kd = max(1e-6, float(kd_uM))
    curve = []
    for c in concentrations_uM:
        c_val = float(c)
        c_n = c_val ** hill_coefficient
        kd_n = kd ** hill_coefficient
        frac = c_n / (kd_n + c_n)
        curve.append({
            "concentration_uM": c_val,
            "fraction_bound": float(round(frac, 4)),
            "percent_bound": float(round(frac * 100.0, 2))
        })
    return curve

