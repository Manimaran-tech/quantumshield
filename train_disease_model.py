"""
train_disease_model.py — Training Script for Hybrid QML Disease Detection Models

This script trains both quantum (VQC) and classical (SVM/RF) disease detection models
on MedMNIST v2 datasets. It downloads the datasets, extracts features using a pretrained
DenseNet-121 backbone, reduces dimensionality via PCA, and trains both model types.

GPU: Optimized for NVIDIA RTX 3050 (8GB VRAM)

Data Sources:
  - MedMNIST v2 (Yang et al., Nature Scientific Data, 2023)
    https://medmnist.com/ | https://zenodo.org/records/10519652
  - TorchXRayVision (Cohen et al., 2022)
    https://github.com/mlmed/torchxrayvision

Usage:
  python train_disease_model.py --modality chest_xray --epochs 20
  python train_disease_model.py --modality all --epochs 15

Output:
  models/
    disease_vqc_{modality}_params.npy    — Trained VQC parameters
    disease_pca_{modality}.pkl           — Fitted PCA transformer
    disease_classical_{modality}.pkl     — Trained classical baseline (SVM/RF)
    disease_training_log_{modality}.json — Training metrics and history
"""

import os
import sys
import json
import time
import argparse
import numpy as np
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================

MODALITIES = ["chest_xray", "pathology", "dermatoscopy", "retinal_oct"]

MEDMNIST_DATASETS = {
    "chest_xray":   "pneumoniamnist",
    "pathology":    "pathmnist",
    "dermatoscopy": "dermamnist",
    "retinal_oct":  "octmnist"
}

TRAINING_CONFIG = {
    "batch_size": 64,
    "learning_rate": 0.001,
    "pca_components": 4,        # Must match vqc_qubits in disease_detector.py
    "vqc_layers": 3,
    "vqc_shots": 4096,
    "vqc_optimizer": "COBYLA",
    "vqc_max_iter": 1000,       # Increased from 200 for better convergence
    "classical_svm_kernel": "rbf",
    "classical_rf_estimators": 200,  # Increased from 100 for better ensemble
    "test_split": 0.2,
    "random_seed": 42
}

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def ensure_models_dir():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"[Train] Models directory: {MODELS_DIR}")
    print(f"[Train] Data directory: {DATA_DIR}")


# ==========================================
# STEP 1: DOWNLOAD MEDMNIST DATASETS
# ==========================================

def download_dataset(modality: str):
    """
    Downloads and prepares the MedMNIST dataset for the specified modality.
    Uses the official `medmnist` Python package (pip install medmnist).
    
    Reference: Yang et al., "MedMNIST v2 - A large-scale lightweight benchmark
    for 2D and 3D biomedical image classification", Nature Scientific Data, 2023.
    """
    import medmnist
    from medmnist import INFO
    
    dataset_name = MEDMNIST_DATASETS[modality]
    info = INFO[dataset_name]
    
    print(f"\n{'='*60}")
    print(f"[Dataset] Downloading {dataset_name} (MedMNIST v2)")
    print(f"  Source: {info.get('url', 'https://medmnist.com/')}")
    print(f"  Task: {info['task']}")
    print(f"  # Classes: {len(info['label'])}")
    print(f"  # Channels: {info['n_channels']}")
    print(f"{'='*60}")
    
    DataClass = getattr(medmnist, info['python_class'])
    
    # Download train, val, test splits
    ensure_models_dir()
    train_dataset = DataClass(split='train', download=True, root=DATA_DIR, size=28, as_rgb=(info['n_channels'] == 3))
    val_dataset = DataClass(split='val', download=True, root=DATA_DIR, size=28, as_rgb=(info['n_channels'] == 3))
    test_dataset = DataClass(split='test', download=True, root=DATA_DIR, size=28, as_rgb=(info['n_channels'] == 3))
    
    print(f"  Train: {len(train_dataset)} samples")
    print(f"  Val:   {len(val_dataset)} samples")
    print(f"  Test:  {len(test_dataset)} samples")
    print(f"  Total: {len(train_dataset) + len(val_dataset) + len(test_dataset)} samples")
    
    return train_dataset, val_dataset, test_dataset, info


# ==========================================
# STEP 2: FEATURE EXTRACTION (DenseNet-121)
# ==========================================

def extract_features_batch(dataset, modality: str, max_samples: int = 5000):
    """
    Extract features from all images in a dataset using the pretrained DenseNet-121 backbone.
    Processes in batches for GPU efficiency on RTX 3050 (8GB VRAM).
    """
    import torch
    from torchvision import transforms, models
    from torch.utils.data import DataLoader
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Features] Using device: {device}")
    if device.type == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    # Load pretrained backbone
    if modality == "chest_xray":
        try:
            import torchxrayvision as xrv
            model = xrv.models.DenseNet(weights="densenet121-res224-all")
            print("[Features] Using TorchXRayVision DenseNet-121 backbone")
        except:
            model = models.densenet121(weights=models.DenseNet121_Weights.DEFAULT)
            print("[Features] Fallback: Using ImageNet DenseNet-121 backbone")
    else:
        model = models.densenet121(weights=models.DenseNet121_Weights.DEFAULT)
        print("[Features] Using ImageNet DenseNet-121 backbone")
    
    model = model.to(device)
    model.eval()
    
    # Transform pipeline
    transform = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    features_list = []
    labels_list = []
    
    n_samples = min(len(dataset), max_samples)
    batch_size = TRAINING_CONFIG["batch_size"]
    
    print(f"[Features] Extracting features from {n_samples} samples (batch_size={batch_size})...")
    
    with torch.no_grad():
        for i in range(0, n_samples, batch_size):
            batch_end = min(i + batch_size, n_samples)
            batch_tensors = []
            batch_labels = []
            
            for j in range(i, batch_end):
                img, label = dataset[j]
                if not isinstance(img, torch.Tensor):
                    import torchvision.transforms.functional as F
                    img = F.to_tensor(img)
                if img.dim() == 2:
                    img = img.unsqueeze(0)
                if img.shape[0] == 1 and modality != "chest_xray":
                    img = img.repeat(3, 1, 1)  # Convert grayscale to RGB for ImageNet DenseNet
                elif img.shape[0] == 3 and modality == "chest_xray":
                    img = img.mean(dim=0, keepdim=True) # Convert RGB to grayscale for TorchXRayVision
                # Resize to 224x224
                img = torch.nn.functional.interpolate(img.unsqueeze(0), size=(224, 224), mode='bilinear').squeeze(0)
                batch_tensors.append(img)
                batch_labels.append(label)
            
            batch = torch.stack(batch_tensors).to(device)
            
            # Extract features from DenseNet backbone (before classifier)
            if hasattr(model, 'features'):
                feat = model.features(batch)
                feat = torch.nn.functional.relu(feat, inplace=True)
                feat = torch.nn.functional.adaptive_avg_pool2d(feat, (1, 1))
                feat = feat.view(feat.size(0), -1)
            else:
                feat = model(batch)
            
            features_list.append(feat.cpu().numpy())
            labels_list.extend(batch_labels)
            
            if (i // batch_size) % 10 == 0:
                print(f"  Processed {batch_end}/{n_samples} samples ({batch_end/n_samples*100:.0f}%)")
    
    features = np.concatenate(features_list, axis=0)
    labels = np.array(labels_list).flatten()
    
    # Ensure binary labels are strictly 0 and 1
    if len(np.unique(labels)) == 2:
        labels = np.where(labels > 0, 1, 0)
    
    print(f"[Features] Extracted features shape: {features.shape}, Labels shape: {labels.shape}")
    return features, labels


# ==========================================
# STEP 3: PCA DIMENSIONALITY REDUCTION
# ==========================================

def fit_pca(features: np.ndarray, n_components: int = 4):
    """Fit PCA to reduce feature dimensionality for quantum encoding."""
    from sklearn.decomposition import PCA
    import pickle
    
    print(f"\n[PCA] Fitting PCA: {features.shape[1]} -> {n_components} dimensions")
    
    pca = PCA(n_components=n_components, random_state=TRAINING_CONFIG["random_seed"])
    reduced = pca.fit_transform(features)
    
    variance_explained = np.sum(pca.explained_variance_ratio_)
    print(f"  Variance explained: {variance_explained:.4f} ({variance_explained*100:.1f}%)")
    print(f"  Component variances: {pca.explained_variance_ratio_}")
    
    return pca, reduced


# ==========================================
# STEP 4: TRAIN QUANTUM MODEL (VQC)
# ==========================================

def train_vqc(train_features: np.ndarray, train_labels: np.ndarray, 
              test_features: np.ndarray, test_labels: np.ndarray,
              num_qubits: int = 4, num_layers: int = 3):
    """
    Train a Variational Quantum Classifier using Qiskit.
    
    Architecture:
      - Feature Map: ZZFeatureMap (angle encoding with entanglement)
      - Ansatz: RealAmplitudes (RY rotations + CNOT entangling layers)
      - Optimizer: COBYLA
      - Backend: Qiskit Aer Simulator (GPU-accelerated if available)
    """
    from qiskit.circuit.library import ZZFeatureMap, RealAmplitudes
    from qiskit_algorithms.optimizers import COBYLA
    
    print(f"\n{'='*60}")
    print(f"[VQC] Training Variational Quantum Classifier")
    print(f"  Qubits: {num_qubits}")
    print(f"  Layers: {num_layers}")
    print(f"  Optimizer: COBYLA (maxiter={TRAINING_CONFIG['vqc_max_iter']})")
    print(f"  Shots: {TRAINING_CONFIG['vqc_shots']}")
    print(f"  Train samples: {len(train_labels)}")
    print(f"  Test samples: {len(test_labels)}")
    print(f"{'='*60}")
    
    # Normalize features to [0, π]
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, np.pi))
    train_scaled = scaler.fit_transform(train_features)
    test_scaled = scaler.transform(test_features)
    
    # Build VQC components
    feature_map = ZZFeatureMap(feature_dimension=num_qubits, reps=2, entanglement='linear')
    ansatz = RealAmplitudes(num_qubits=num_qubits, reps=num_layers, entanglement='linear')
    optimizer = COBYLA(maxiter=TRAINING_CONFIG['vqc_max_iter'])
    
    # For large datasets, subsample for VQC training
    max_vqc_samples = 1500
    if len(train_scaled) > max_vqc_samples:
        indices = np.random.choice(len(train_scaled), max_vqc_samples, replace=False)
        train_scaled = train_scaled[indices]
        train_labels_sub = train_labels[indices]
    else:
        train_labels_sub = train_labels
    
    try:
        from qiskit_machine_learning.algorithms import VQC as QiskitVQC
        from qiskit.primitives import StatevectorSampler
        
        # Use StatevectorSampler for reliable local VQC simulation (4 qubits)
        sampler = StatevectorSampler()
        
        vqc = QiskitVQC(
            feature_map=feature_map,
            ansatz=ansatz,
            optimizer=optimizer,
            sampler=sampler
        )
        
        start = time.time()
        print("[VQC] Training started...")
        vqc.fit(train_scaled, train_labels_sub)
        train_time = time.time() - start
        
        # Evaluate
        train_acc = vqc.score(train_scaled, train_labels_sub)
        
        test_sub = test_scaled[:min(500, len(test_scaled))]
        test_labels_sub = test_labels[:min(500, len(test_labels))]
        test_acc = vqc.score(test_sub, test_labels_sub)
        
        # Get optimized parameters
        optimal_params = vqc.weights if hasattr(vqc, 'weights') else np.random.randn(ansatz.num_parameters)
        
        print(f"\n[VQC] Training completed in {train_time:.1f}s")
        print(f"  Train accuracy: {train_acc:.4f}")
        print(f"  Test accuracy:  {test_acc:.4f}")
        
        return {
            "params": optimal_params,
            "train_accuracy": float(train_acc),
            "test_accuracy": float(test_acc),
            "training_time_s": round(train_time, 1),
            "num_qubits": num_qubits,
            "num_layers": num_layers,
            "num_params": ansatz.num_parameters,
            "optimizer": "COBYLA",
            "shots": TRAINING_CONFIG["vqc_shots"]
        }
    except Exception as e:
        print(f"[VQC] Training failed: {e}")
        print("[VQC] Saving random initialization as fallback parameters")
        
        fallback_params = np.random.uniform(-np.pi, np.pi, ansatz.num_parameters)
        return {
            "params": fallback_params,
            "train_accuracy": 0.0,
            "test_accuracy": 0.0,
            "training_time_s": 0.0,
            "num_qubits": num_qubits,
            "num_layers": num_layers,
            "num_params": ansatz.num_parameters,
            "optimizer": "COBYLA",
            "shots": TRAINING_CONFIG["vqc_shots"],
            "note": f"Training failed: {str(e)}. Using random initialization."
        }


# ==========================================
# STEP 5: TRAIN CLASSICAL BASELINES
# ==========================================

def train_classical(train_features: np.ndarray, train_labels: np.ndarray,
                     test_features: np.ndarray, test_labels: np.ndarray):
    """
    Train classical SVM and Random Forest baselines for benchmarking.
    """
    from sklearn.svm import SVC
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, f1_score, classification_report
    from sklearn.preprocessing import StandardScaler
    
    print(f"\n{'='*60}")
    print(f"[Classical] Training classical baselines")
    print(f"  Train: {len(train_labels)}, Test: {len(test_labels)}")
    print(f"{'='*60}")
    
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_features)
    test_scaled = scaler.transform(test_features)
    
    results = {}
    
    # SVM
    print("\n[Classical] Training SVM (RBF kernel)...")
    start = time.time()
    svm = SVC(kernel=TRAINING_CONFIG["classical_svm_kernel"], probability=True, random_state=42)
    svm.fit(train_scaled, train_labels)
    svm_time = time.time() - start
    
    svm_preds = svm.predict(test_scaled)
    svm_acc = accuracy_score(test_labels, svm_preds)
    svm_f1 = f1_score(test_labels, svm_preds, average='weighted')
    
    print(f"  SVM accuracy:  {svm_acc:.4f}")
    print(f"  SVM F1 score:  {svm_f1:.4f}")
    print(f"  Training time: {svm_time:.1f}s")
    
    results["svm"] = {
        "accuracy": float(svm_acc),
        "f1_score": float(svm_f1),
        "training_time_s": round(svm_time, 1),
        "kernel": TRAINING_CONFIG["classical_svm_kernel"]
    }
    
    # Random Forest
    print("\n[Classical] Training Random Forest...")
    start = time.time()
    rf = RandomForestClassifier(
        n_estimators=TRAINING_CONFIG["classical_rf_estimators"],
        random_state=42, n_jobs=-1
    )
    rf.fit(train_scaled, train_labels)
    rf_time = time.time() - start
    
    rf_preds = rf.predict(test_scaled)
    rf_acc = accuracy_score(test_labels, rf_preds)
    rf_f1 = f1_score(test_labels, rf_preds, average='weighted')
    
    print(f"  RF accuracy:  {rf_acc:.4f}")
    print(f"  RF F1 score:  {rf_f1:.4f}")
    print(f"  Training time: {rf_time:.1f}s")
    
    results["random_forest"] = {
        "accuracy": float(rf_acc),
        "f1_score": float(rf_f1),
        "training_time_s": round(rf_time, 1),
        "n_estimators": TRAINING_CONFIG["classical_rf_estimators"]
    }
    
    # Return the best classical model
    best_model = svm if svm_acc >= rf_acc else rf
    best_name = "SVM" if svm_acc >= rf_acc else "Random Forest"
    results["best_model"] = best_name
    results["scaler"] = scaler
    results["model"] = best_model
    
    return results


# ==========================================
# STEP 6: SAVE MODELS
# ==========================================

def save_models(modality: str, pca, vqc_result: dict, classical_result: dict, training_log: dict):
    """Save all trained models and metadata to the models/ directory."""
    import pickle
    
    ensure_models_dir()
    
    # Save VQC parameters
    vqc_path = os.path.join(MODELS_DIR, f"disease_vqc_{modality}_params.npy")
    np.save(vqc_path, vqc_result["params"])
    print(f"[Save] VQC params -> {vqc_path}")
    
    # Save PCA transformer
    pca_path = os.path.join(MODELS_DIR, f"disease_pca_{modality}.pkl")
    with open(pca_path, 'wb') as f:
        pickle.dump(pca, f)
    print(f"[Save] PCA -> {pca_path}")
    
    # Save classical model
    classical_path = os.path.join(MODELS_DIR, f"disease_classical_{modality}.pkl")
    with open(classical_path, 'wb') as f:
        pickle.dump({
            "model": classical_result["model"],
            "scaler": classical_result["scaler"],
            "best_model_name": classical_result["best_model"]
        }, f)
    print(f"[Save] Classical -> {classical_path}")
    
    # Save training log
    log_path = os.path.join(MODELS_DIR, f"disease_training_log_{modality}.json")
    with open(log_path, 'w') as f:
        json.dump(training_log, f, indent=2, default=str)
    print(f"[Save] Training log -> {log_path}")


# ==========================================
# MAIN TRAINING PIPELINE
# ==========================================

def train_modality(modality: str, epochs: int = 15, max_samples: int = 5000):
    """Run the full training pipeline for a single modality."""
    print(f"\n{'#'*70}")
    print(f"# TRAINING: {modality.upper()}")
    print(f"# Epochs: {epochs}, Max samples: {max_samples}")
    print(f"# Time: {datetime.now().isoformat()}")
    print(f"{'#'*70}")
    
    overall_start = time.time()
    
    # Step 1: Download dataset
    train_ds, val_ds, test_ds, info = download_dataset(modality)
    
    # Step 2: Extract features
    print("\n[Pipeline] Extracting training features...")
    train_features, train_labels = extract_features_batch(train_ds, modality, max_samples=max_samples)
    
    print("\n[Pipeline] Extracting test features...")
    test_features, test_labels = extract_features_batch(test_ds, modality, max_samples=max_samples // 5)
    
    # Step 3: PCA reduction
    pca, train_reduced = fit_pca(train_features, n_components=TRAINING_CONFIG["pca_components"])
    test_reduced = pca.transform(test_features)
    
    # Step 4: Train VQC
    vqc_result = train_vqc(
        train_reduced, train_labels,
        test_reduced, test_labels,
        num_qubits=TRAINING_CONFIG["pca_components"],
        num_layers=TRAINING_CONFIG["vqc_layers"]
    )
    
    # Step 5: Train classical baselines
    classical_result = train_classical(train_reduced, train_labels, test_reduced, test_labels)
    
    # Step 6: Save everything
    total_time = time.time() - overall_start
    
    training_log = {
        "modality": modality,
        "dataset": MEDMNIST_DATASETS[modality],
        "dataset_info": {
            "task": info["task"],
            "n_classes": len(info["label"]),
            "n_channels": info["n_channels"],
            "train_samples": len(train_ds),
            "test_samples": len(test_ds)
        },
        "config": TRAINING_CONFIG,
        "vqc_results": {k: v for k, v in vqc_result.items() if k != "params"},
        "classical_results": {k: v for k, v in classical_result.items() if k not in ["scaler", "model"]},
        "total_training_time_s": round(total_time, 1),
        "timestamp": datetime.now().isoformat(),
        "gpu": "NVIDIA RTX 3050 (8GB VRAM)" if __import__('torch').cuda.is_available() else "CPU"
    }
    
    save_models(modality, pca, vqc_result, classical_result, training_log)
    
    print(f"\n{'='*60}")
    print(f"[DONE] {modality} training completed in {total_time:.1f}s")
    print(f"  VQC accuracy:       {vqc_result['test_accuracy']:.4f}")
    print(f"  Classical accuracy:  {classical_result[classical_result['best_model'].lower().replace(' ', '_')]['accuracy']:.4f}")
    print(f"  Best classical:     {classical_result['best_model']}")
    print(f"{'='*60}")
    
    return training_log


def main():
    parser = argparse.ArgumentParser(description="Train QML Disease Detection Models on MedMNIST v2")
    parser.add_argument("--modality", type=str, default="all",
                       choices=["all"] + MODALITIES,
                       help="Which modality to train (default: all)")
    parser.add_argument("--epochs", type=int, default=15,
                       help="Number of training epochs (default: 15)")
    parser.add_argument("--max-samples", type=int, default=5000,
                       help="Maximum training samples per modality (default: 5000)")
    
    args = parser.parse_args()
    
    print(f"{'='*70}")
    print(f" QuantumShield — Hybrid QML Disease Detection Model Training")
    print(f" MedMNIST v2 (Yang et al., Nature Scientific Data, 2023)")
    print(f" GPU: RTX 3050 8GB | Framework: PyTorch + Qiskit + scikit-learn")
    print(f"{'='*70}")
    
    modalities = MODALITIES if args.modality == "all" else [args.modality]
    
    all_logs = {}
    for mod in modalities:
        log = train_modality(mod, epochs=args.epochs, max_samples=args.max_samples)
        all_logs[mod] = log
    
    # Save combined log
    ensure_models_dir()
    combined_path = os.path.join(MODELS_DIR, "training_summary.json")
    with open(combined_path, 'w') as f:
        json.dump(all_logs, f, indent=2, default=str)
    
    print(f"\n{'#'*70}")
    print(f"# ALL TRAINING COMPLETE")
    print(f"# Summary saved to: {combined_path}")
    print(f"{'#'*70}")


if __name__ == "__main__":
    main()
