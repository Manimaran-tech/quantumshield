import sys
import numpy as np
import os
sys.path.append("D:/Quantum/quantumshield")
from train_disease_model import (
    download_dataset, extract_features_batch, fit_pca, train_classical, save_models, TRAINING_CONFIG, MEDMNIST_DATASETS
)

def recover():
    modality = "chest_xray"
    os.chdir("D:/Quantum/quantumshield")
    train_ds, val_ds, test_ds, info = download_dataset(modality)
    
    print("Extracting training features...")
    train_features, train_labels = extract_features_batch(train_ds, modality, max_samples=5000)
    
    print("Extracting test features...")
    test_features, test_labels = extract_features_batch(test_ds, modality, max_samples=1000)
    
    pca, train_reduced = fit_pca(train_features, n_components=TRAINING_CONFIG["pca_components"])
    test_reduced = pca.transform(test_features)
    
    classical_result = train_classical(train_reduced, train_labels, test_reduced, test_labels)
    
    # Mock VQC result with actual numbers from the log
    vqc_result = {
        "params": np.load(f"models/disease_vqc_{modality}_params.npy"),
        "train_accuracy": 0.7733,
        "test_accuracy": 0.7240,
        "training_time_s": 3622.5,
        "num_qubits": 4,
        "num_layers": 3,
        "num_params": 16,
        "optimizer": "COBYLA",
        "shots": 4096
    }
    
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
        "total_training_time_s": 3623.5,
        "timestamp": "2026-09-08T19:27:36",
        "gpu": "CPU"
    }
    
    save_models(modality, pca, vqc_result, classical_result, training_log)
    print("Recovery complete!")

if __name__ == "__main__":
    recover()
