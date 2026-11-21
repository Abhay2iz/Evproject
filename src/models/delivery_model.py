"""
Delivery Failure Prediction Pipeline.
Predicts delivery failure risk prior to dispatch using strict temporal train-test splits.
Compares Logistic Regression, Random Forest, and XGBoost Classifier.
"""

import sys
import os
sys.path.insert(0, "/workspace")

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix
)
from src.features.engineering import build_delivery_features

ARTIFACTS_DIR = "/workspace/models_artifacts"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def train_delivery_models():
    print("=" * 60)
    print("TRAINING PRE-DELIVERY FAILURE RISK CLASSIFIERS")
    print("=" * 60)

    # 1. Load feature matrix
    df = build_delivery_features(sample_size=80000)
    target_col = "target_failure"
    time_col = "start_time"

    # Sort strictly by dispatch timestamp to prevent temporal leakage
    df = df.sort_values(by=time_col).reset_index(drop=True)

    cat_cols = ["chemistry_type", "city"]
    num_cols = [c for c in df.columns if c not in cat_cols + [target_col, time_col]]

    X = df[cat_cols + num_cols]
    y = df[target_col]

    print(f"Dataset size: {len(df):,}, Failed deliveries: {y.sum():,} ({y.mean()*100:.2f}%)")

    # 2. Strict Temporal Train-Test Split (Chronological 80/20 split)
    split_idx = int(len(df) * 0.80)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    train_dates = (df[time_col].iloc[0], df[time_col].iloc[split_idx-1])
    test_dates = (df[time_col].iloc[split_idx], df[time_col].iloc[-1])
    print(f"Train window: {train_dates[0]} to {train_dates[1]} ({len(X_train):,} samples)")
    print(f"Test window:  {test_dates[0]} to {test_dates[1]} ({len(X_test):,} samples)")

    # 3. Preprocessor pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)
        ]
    )

    # 4. Model candidates
    scale_pos = (len(y_train) - y_train.sum()) / (y_train.sum() + 1e-5)
    models = {
        "Logistic Regression": LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=120, max_depth=7, class_weight="balanced", random_state=42),
        "XGBoost": XGBClassifier(n_estimators=120, max_depth=5, scale_pos_weight=scale_pos, learning_rate=0.08, eval_metric="logloss", random_state=42)
    }

    results = {}
    best_model_name = None
    best_pr_auc = -1.0
    best_pipeline = None

    for name, clf in models.items():
        pipe = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("classifier", clf)
        ])
        
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        y_prob = pipe.predict_proba(X_test)[:, 1]

        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc = roc_auc_score(y_test, y_prob)
        pr_auc = average_precision_score(y_test, y_prob)

        results[name] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc, 4),
            "pr_auc": round(pr_auc, 4),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist()
        }

        print(f"\n--- {name} ---")
        print(f"Precision: {prec:.4f} | Recall: {rec:.4f} | F1: {f1:.4f} | ROC-AUC: {roc:.4f} | PR-AUC: {pr_auc:.4f}")

        if pr_auc > best_pr_auc:
            best_pr_auc = pr_auc
            best_model_name = name
            best_pipeline = pipe

    print(f"\nChampion Failure Predictor: {best_model_name} (PR-AUC = {best_pr_auc:.4f})")

    # Feature importances
    preprocessor_fitted = best_pipeline.named_steps["preprocessor"]
    cat_feature_names = list(preprocessor_fitted.named_transformers_["cat"].get_feature_names_out(cat_cols))
    all_feature_names = num_cols + cat_feature_names

    clf = best_pipeline.named_steps["classifier"]
    if hasattr(clf, "feature_importances_"):
        importances = clf.feature_importances_
    elif hasattr(clf, "coef_"):
        importances = np.abs(clf.coef_[0])
    else:
        importances = np.ones(len(all_feature_names))

    feature_importance_df = pd.DataFrame({
        "feature": all_feature_names,
        "importance": importances
    }).sort_values(by="importance", ascending=False)

    model_artifact = {
        "model_name": best_model_name,
        "pipeline": best_pipeline,
        "num_cols": num_cols,
        "cat_cols": cat_cols,
        "feature_names": all_feature_names,
        "feature_importance": feature_importance_df.to_dict(orient="records"),
        "metrics": results[best_model_name],
        "all_model_benchmarks": results,
        "temporal_split_info": {
            "train_start": str(train_dates[0]),
            "train_end": str(train_dates[1]),
            "test_start": str(test_dates[0]),
            "test_end": str(test_dates[1])
        }
    }

    save_path = os.path.join(ARTIFACTS_DIR, "delivery_model.joblib")
    joblib.dump(model_artifact, save_path)
    print(f"Saved delivery failure model artifact to {save_path}")

    return model_artifact

if __name__ == "__main__":
    train_delivery_models()
