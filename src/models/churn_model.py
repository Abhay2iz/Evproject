"""
Rider Churn Prediction Model Pipeline.
Compares Logistic Regression, Random Forest, and XGBoost Classifier.
Evaluates Precision, Recall, F1, ROC-AUC, PR-AUC and persists the champion model.
"""

import sys
import os
sys.path.insert(0, "/workspace")

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, classification_report, confusion_matrix
)
from src.features.engineering import build_churn_features

ARTIFACTS_DIR = "/workspace/models_artifacts"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def train_churn_models():
    print("=" * 60)
    print("TRAINING RIDER CHURN PREDICTION MODELS")
    print("=" * 60)

    # 1. Load feature matrix
    df = build_churn_features()
    target_col = "churn_label"
    rider_ids = df["rider_id"]
    
    cat_cols = ["tier", "city"]
    num_cols = [c for c in df.columns if c not in cat_cols + [target_col, "rider_id"]]

    X = df[cat_cols + num_cols]
    y = df[target_col]

    print(f"Dataset shape: {X.shape}, Class distribution: Churned={y.sum()} ({y.mean()*100:.1f}%), Retained={len(y)-y.sum()}")

    # 2. Stratified train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # 3. Preprocessor pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)
        ]
    )

    # 4. Model candidates
    models = {
        "Logistic Regression": LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=150, max_depth=6, class_weight="balanced", random_state=42),
        "XGBoost": XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, eval_metric="logloss", random_state=42)
    }

    results = {}
    best_model_name = None
    best_f1 = -1.0
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

        if f1 > best_f1:
            best_f1 = f1
            best_model_name = name
            best_pipeline = pipe

    print(f"\nChampion Model: {best_model_name} (F1 = {best_f1:.4f})")

    # Extract feature names & importances
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

    # Persist champion pipeline
    model_artifact = {
        "model_name": best_model_name,
        "pipeline": best_pipeline,
        "num_cols": num_cols,
        "cat_cols": cat_cols,
        "feature_names": all_feature_names,
        "feature_importance": feature_importance_df.to_dict(orient="records"),
        "metrics": results[best_model_name],
        "all_model_benchmarks": results
    }

    save_path = os.path.join(ARTIFACTS_DIR, "churn_model.joblib")
    joblib.dump(model_artifact, save_path)
    print(f"Saved churn model artifact to {save_path}")

    return model_artifact

if __name__ == "__main__":
    train_churn_models()
