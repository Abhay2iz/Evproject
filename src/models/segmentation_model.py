"""
Rider Segmentation Model Pipeline.
Performs K-Means clustering with StandardScaler and evaluates Silhouette Score,
Davies-Bouldin Index, and derives business personas.
"""

import sys
import os
sys.path.insert(0, "/workspace")

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
from src.features.engineering import build_segmentation_features

ARTIFACTS_DIR = "/workspace/models_artifacts"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def train_segmentation_model(n_clusters=4):
    print("=" * 60)
    print("TRAINING RIDER BEHAVIORAL SEGMENTATION (K-MEANS)")
    print("=" * 60)

    # 1. Load feature matrix
    df = build_segmentation_features()
    feature_cols = [
        "days_active", "avg_daily_hours", "total_deliveries", "total_earnings",
        "rating_avg", "avg_swaps_daily", "avg_peak_ratio", "failure_rate", "deliveries_per_hour"
    ]

    X = df[feature_cols].copy()
    print(f"Rider cohort size: {len(X)} active riders across {len(feature_cols)} behavioral dimensions.")

    # 2. Scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 3. Cluster evaluation across candidate k (k=2 to 6)
    k_evals = {}
    for k in range(2, 7):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_scaled)
        sil = silhouette_score(X_scaled, labels)
        db = davies_bouldin_score(X_scaled, labels)
        k_evals[k] = {"inertia": float(km.inertia_), "silhouette": round(float(sil), 4), "davies_bouldin": round(float(db), 4)}
        print(f"k={k}: Silhouette={sil:.4f} | Davies-Bouldin={db:.4f} | Inertia={km.inertia_:.1f}")

    # 4. Fit champion K-Means with chosen k=4
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=15)
    cluster_labels = kmeans.fit_predict(X_scaled)
    df["cluster"] = cluster_labels

    # 5. Profile each cluster and assign meaningful persona
    cluster_profiles = []
    # Names based on profile characteristics:
    # 0: Peak Hustlers, 1: Steady Core, 2: Casual Part-Timers, 3: Struggling / High Churn Risk
    persona_mapping = {
        0: "Peak Hustlers (High Earnings & Peak Hour Focus)",
        1: "Steady Full-Timers (High Daily Hours & High Reliability)",
        2: "Casual Flexible Riders (Low Hours, Supplementary Income)",
        3: "At-Risk Low Earners (High Failure Rate & Low Satisfaction)"
    }

    for c in range(n_clusters):
        c_df = df[df["cluster"] == c]
        profile = {
            "cluster_id": c,
            "persona_name": persona_mapping.get(c, f"Cluster {c}"),
            "rider_count": int(len(c_df)),
            "share_pct": round(float(len(c_df) / len(df) * 100.0), 1),
            "mean_daily_hours": round(float(c_df["avg_daily_hours"].mean()), 2),
            "mean_deliveries": round(float(c_df["total_deliveries"].mean()), 1),
            "mean_earnings": round(float(c_df["total_earnings"].mean()), 2),
            "mean_rating": round(float(c_df["rating_avg"].mean()), 2),
            "mean_failure_rate": round(float(c_df["failure_rate"].mean()), 3),
            "mean_peak_ratio": round(float(c_df["avg_peak_ratio"].mean()), 2)
        }
        cluster_profiles.append(profile)
        print(f"\nPersona [{c}]: {profile['persona_name']} ({profile['rider_count']} riders, {profile['share_pct']}%)")
        print(f"  Hours/day: {profile['mean_daily_hours']} | Earnings: ${profile['mean_earnings']} | Failure Rate: {profile['mean_failure_rate']*100:.1f}%")

    model_artifact = {
        "model_name": "KMeans Clustering",
        "scaler": scaler,
        "kmeans": kmeans,
        "feature_cols": feature_cols,
        "n_clusters": n_clusters,
        "k_evaluations": k_evals,
        "silhouette_score": round(float(silhouette_score(X_scaled, cluster_labels)), 4),
        "davies_bouldin_score": round(float(davies_bouldin_score(X_scaled, cluster_labels)), 4),
        "cluster_profiles": cluster_profiles,
        "persona_mapping": persona_mapping
    }

    save_path = os.path.join(ARTIFACTS_DIR, "segmentation_model.joblib")
    joblib.dump(model_artifact, save_path)
    print(f"\nSaved segmentation artifact to {save_path}")

    return model_artifact

if __name__ == "__main__":
    train_segmentation_model()
