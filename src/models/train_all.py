"""
Master ML Training and Model Card Metadata Generation Script.
Executes training for:
1. Rider Churn Predictor
2. Battery Degradation (SOH %) Regressor
3. Pre-Delivery Failure Risk Predictor
4. Rider Behavioral Segmentation
Persists all models and emits models_artifacts/model_metadata.json.
"""

import sys
import os
import json
import time
sys.path.insert(0, "/workspace")

from src.models.churn_model import train_churn_models
from src.models.battery_model import train_battery_models
from src.models.delivery_model import train_delivery_models
from src.models.segmentation_model import train_segmentation_model

METADATA_PATH = "/workspace/models_artifacts/model_metadata.json"

def train_and_register_all():
    start_time = time.time()
    print("=" * 70)
    print("BEGINNING COMPREHENSIVE MACHINE LEARNING PIPELINE TRAINING")
    print("=" * 70)

    # 1. Churn
    churn_artifact = train_churn_models()

    # 2. Battery
    battery_artifact = train_battery_models()

    # 3. Delivery Failure
    delivery_artifact = train_delivery_models()

    # 4. Segmentation
    seg_artifact = train_segmentation_model()

    # Consolidate metadata
    metadata = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "training_duration_seconds": round(time.time() - start_time, 2),
        "models": {
            "rider_churn": {
                "task": "binary_classification",
                "champion_model": churn_artifact["model_name"],
                "metrics": churn_artifact["metrics"],
                "benchmarks": churn_artifact["all_model_benchmarks"],
                "top_features": churn_artifact["feature_importance"][:5]
            },
            "battery_degradation": {
                "task": "regression",
                "target": "current_soh_pct",
                "champion_model": battery_artifact["model_name"],
                "metrics": battery_artifact["metrics"],
                "benchmarks": battery_artifact["all_model_benchmarks"],
                "top_features": battery_artifact["feature_importance"][:5]
            },
            "delivery_failure": {
                "task": "binary_classification",
                "champion_model": delivery_artifact["model_name"],
                "metrics": delivery_artifact["metrics"],
                "benchmarks": delivery_artifact["all_model_benchmarks"],
                "temporal_split": delivery_artifact.get("temporal_split_info"),
                "top_features": delivery_artifact["feature_importance"][:5]
            },
            "rider_segmentation": {
                "task": "unsupervised_clustering",
                "algorithm": "KMeans",
                "n_clusters": seg_artifact["n_clusters"],
                "silhouette_score": seg_artifact["silhouette_score"],
                "davies_bouldin_score": seg_artifact["davies_bouldin_score"],
                "personas": seg_artifact["cluster_profiles"]
            }
        }
    }

    with open(METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nModel metadata successfully compiled and saved to {METADATA_PATH}")
    print(f"Total training time: {metadata['training_duration_seconds']} seconds.")

if __name__ == "__main__":
    train_and_register_all()
