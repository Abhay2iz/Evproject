"""
Battery Degradation Prediction (SOH Regressor).
Compares Random Forest Regressor and XGBoost Regressor.
Evaluates MAE, RMSE, R-squared and persists the champion model.
"""

import sys
import os
sys.path.insert(0, "/workspace")

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from src.features.engineering import build_battery_features

ARTIFACTS_DIR = "/workspace/models_artifacts"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def train_battery_models():
    print("=" * 60)
    print("TRAINING BATTERY DEGRADATION (SOH %) REGRESSION MODELS")
    print("=" * 60)

    # 1. Load feature matrix
    df = build_battery_features()
    target_col = "current_soh_pct"
    battery_ids = df["battery_id"]

    cat_cols = ["chemistry_type", "supplier_tier"]
    num_cols = [c for c in df.columns if c not in cat_cols + [target_col, "battery_id"]]

    X = df[cat_cols + num_cols]
    y = df[target_col]

    print(f"Dataset shape: {X.shape}, Target mean SOH: {y.mean():.2f}% (std: {y.std():.2f}%)")

    # 2. Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
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
        "Random Forest Regressor": RandomForestRegressor(n_estimators=150, max_depth=8, random_state=42),
        "XGBoost Regressor": XGBRegressor(n_estimators=150, max_depth=5, learning_rate=0.05, random_state=42)
    }

    results = {}
    best_model_name = None
    best_rmse = float("inf")
    best_pipeline = None

    for name, reg in models.items():
        pipe = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("regressor", reg)
        ])
        
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        rmse = root_mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        results[name] = {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2_score": round(r2, 4)
        }

        print(f"\n--- {name} ---")
        print(f"MAE: {mae:.4f}% | RMSE: {rmse:.4f}% | R² Score: {r2:.4f}")

        if rmse < best_rmse:
            best_rmse = rmse
            best_model_name = name
            best_pipeline = pipe

    print(f"\nChampion Regressor: {best_model_name} (RMSE = {best_rmse:.4f}%)")

    # Feature importances
    preprocessor_fitted = best_pipeline.named_steps["preprocessor"]
    cat_feature_names = list(preprocessor_fitted.named_transformers_["cat"].get_feature_names_out(cat_cols))
    all_feature_names = num_cols + cat_feature_names

    reg_clf = best_pipeline.named_steps["regressor"]
    importances = reg_clf.feature_importances_ if hasattr(reg_clf, "feature_importances_") else np.ones(len(all_feature_names))

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
        "all_model_benchmarks": results
    }

    save_path = os.path.join(ARTIFACTS_DIR, "battery_model.joblib")
    joblib.dump(model_artifact, save_path)
    print(f"Saved battery model artifact to {save_path}")

    return model_artifact

if __name__ == "__main__":
    train_battery_models()
