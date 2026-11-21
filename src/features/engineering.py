"""
Feature Engineering Module for EV Fleet Intelligence.
Implements leak-free feature creation for:
- Rider Churn Prediction
- Battery Degradation (SOH) Prediction
- Delivery Failure Risk Prediction
- Rider Behavioral Segmentation
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DATA_DIR = "/workspace/data/processed"

def build_churn_features(cutoff_date_str="2026-07-01", horizon_days=45):
    """
    Constructs leak-free feature matrix for Rider Churn Prediction.
    Features: calculated strictly on or before cutoff_date.
    Target: 1 if rider is inactive (0 deliveries) in the subsequent horizon_days, else 0.
    """
    cutoff_dt = pd.to_datetime(cutoff_date_str)
    horizon_dt = cutoff_dt + timedelta(days=horizon_days)

    riders = pd.read_csv(f"{DATA_DIR}/riders.csv")
    riders["signup_date"] = pd.to_datetime(riders["signup_date"])
    riders["activation_date"] = pd.to_datetime(riders["activation_date"])
    riders["churn_date"] = pd.to_datetime(riders["churn_date"])

    # Consider riders activated before the cutoff date
    active_cohort = riders[riders["activation_date"] <= cutoff_dt].copy()

    activity = pd.read_csv(f"{DATA_DIR}/rider_activity_daily.csv")
    activity["activity_date"] = pd.to_datetime(activity["activity_date"])

    # Historical window (last 60 days before cutoff)
    hist_start_dt = cutoff_dt - timedelta(days=60)
    pre_cutoff_act = activity[(activity["activity_date"] <= cutoff_dt) & (activity["activity_date"] >= hist_start_dt)]

    # Future window (target evaluation window)
    post_cutoff_act = activity[(activity["activity_date"] > cutoff_dt) & (activity["activity_date"] <= horizon_dt)]

    # Compute targets: Rider is churned if they have <= 1 delivery in the post-cutoff horizon
    future_deliv = post_cutoff_act.groupby("rider_id")["deliveries_completed"].sum()
    active_cohort["future_deliveries"] = active_cohort["rider_id"].map(future_deliv).fillna(0)
    active_cohort["churn_label"] = (active_cohort["future_deliveries"] <= 1).astype(int)

    # Historical aggregations (last 30 days and last 7 days for momentum)
    act_30d = pre_cutoff_act[pre_cutoff_act["activity_date"] >= (cutoff_dt - timedelta(days=30))]
    act_7d = pre_cutoff_act[pre_cutoff_act["activity_date"] >= (cutoff_dt - timedelta(days=7))]
    act_prev_7d = pre_cutoff_act[(pre_cutoff_act["activity_date"] < (cutoff_dt - timedelta(days=7))) & (pre_cutoff_act["activity_date"] >= (cutoff_dt - timedelta(days=14)))]

    agg_30d = act_30d.groupby("rider_id").agg(
        active_days_30d=("activity_date", "count"),
        total_hours_30d=("hours_online", "sum"),
        avg_hours_daily=("hours_online", "mean"),
        total_deliveries_30d=("deliveries_completed", "sum"),
        failed_deliveries_30d=("deliveries_failed", "sum"),
        total_earnings_30d=("total_earnings", "sum"),
        avg_daily_earnings=("total_earnings", "mean"),
        battery_swaps_30d=("battery_swaps_count", "sum")
    ).reset_index()

    agg_7d = act_7d.groupby("rider_id").agg(
        hours_7d=("hours_online", "sum"),
        earnings_7d=("total_earnings", "sum"),
        deliveries_7d=("deliveries_completed", "sum")
    ).reset_index()

    agg_prev_7d = act_prev_7d.groupby("rider_id").agg(
        hours_prev_7d=("hours_online", "sum"),
        earnings_prev_7d=("total_earnings", "sum")
    ).reset_index()

    # Merge features
    df = active_cohort.merge(agg_30d, on="rider_id", how="left").fillna(0)
    df = df.merge(agg_7d, on="rider_id", how="left").fillna(0)
    df = df.merge(agg_prev_7d, on="rider_id", how="left").fillna(0)

    # Derived momentum & operational ratio features
    df["tenure_days_at_cutoff"] = (cutoff_dt - df["activation_date"]).dt.days
    df["earnings_momentum_ratio"] = (df["earnings_7d"] + 1.0) / (df["earnings_prev_7d"] + 1.0)
    df["hours_momentum_ratio"] = (df["hours_7d"] + 0.5) / (df["hours_prev_7d"] + 0.5)
    df["failure_rate_30d"] = np.round(df["failed_deliveries_30d"] / (df["total_deliveries_30d"] + df["failed_deliveries_30d"] + 0.001), 3)
    df["hourly_earnings_rate"] = np.round(df["total_earnings_30d"] / (df["total_hours_30d"] + 0.1), 2)
    df["swaps_per_delivery"] = np.round(df["battery_swaps_30d"] / (df["total_deliveries_30d"] + 1.0), 3)

    feature_cols = [
        "tenure_days_at_cutoff", "active_days_30d", "avg_hours_daily", "total_deliveries_30d",
        "avg_daily_earnings", "battery_swaps_30d", "earnings_momentum_ratio", "hours_momentum_ratio",
        "failure_rate_30d", "hourly_earnings_rate", "rating_avg", "swaps_per_delivery",
        "tier", "city"
    ]
    return df[feature_cols + ["churn_label", "rider_id"]]

def build_battery_features():
    """
    Constructs feature matrix for Battery Degradation (SOH Regressor).
    Predicts State of Health (SOH %) using hardware and operational metrics.
    """
    batteries = pd.read_csv(f"{DATA_DIR}/batteries.csv")
    suppliers = pd.read_csv(f"{DATA_DIR}/suppliers.csv")[["supplier_id", "tier", "rating"]].rename(
        columns={"tier": "supplier_tier", "rating": "supplier_rating"}
    )
    lots = pd.read_csv(f"{DATA_DIR}/manufacturing_lots.csv")[["lot_id", "defect_rate_estimate"]]

    df = batteries.merge(suppliers, on="supplier_id", how="left")
    df = df.merge(lots, on="lot_id", how="left")

    df["manufactured_date"] = pd.to_datetime(df["manufactured_date"])
    ref_date = pd.to_datetime("2026-11-15")
    df["battery_age_days"] = (ref_date - df["manufactured_date"]).dt.days

    feature_cols = [
        "cycle_count", "battery_age_days", "nominal_capacity_kwh", "chemistry_type",
        "max_temp_celsius_recorded", "internal_resistance_m_ohm", "supplier_tier",
        "supplier_rating", "defect_rate_estimate"
    ]
    return df[feature_cols + ["current_soh_pct", "battery_id"]]

def build_delivery_features(sample_size=100000):
    """
    Constructs feature matrix for Pre-Delivery Failure Prediction.
    Strictly uses pre-dispatch features (distance, promised duration, order value, time, ambient conditions).
    """
    deliveries = pd.read_csv(f"{DATA_DIR}/deliveries.csv")
    trips = pd.read_csv(f"{DATA_DIR}/trips.csv")[["trip_id", "start_soc_pct", "ambient_temp_c", "battery_id"]]
    batteries = pd.read_csv(f"{DATA_DIR}/batteries.csv")[["battery_id", "chemistry_type", "current_soh_pct", "internal_resistance_m_ohm"]]

    # Sample for snappy model training while preserving representative distribution
    df = deliveries.sample(n=min(sample_size, len(deliveries)), random_state=42).copy()
    df = df.merge(trips, on="trip_id", how="left")
    df = df.merge(batteries, on="battery_id", how="left")

    df["start_time"] = pd.to_datetime(df["start_time"])
    df["hour_of_day"] = df["start_time"].dt.hour
    df["day_of_week"] = df["start_time"].dt.dayofweek
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_peak_hour"] = df["hour_of_day"].isin([12, 13, 14, 19, 20, 21]).astype(int)

    # Impute missing values if any
    df["start_soc_pct"] = df["start_soc_pct"].fillna(75.0)
    df["ambient_temp_c"] = df["ambient_temp_c"].fillna(28.0)
    df["current_soh_pct"] = df["current_soh_pct"].fillna(88.0)
    df["internal_resistance_m_ohm"] = df["internal_resistance_m_ohm"].fillna(26.0)
    df["chemistry_type"] = df["chemistry_type"].fillna("LFP")

    df["target_failure"] = (df["delivery_status"] != "COMPLETED").astype(int)

    feature_cols = [
        "distance_km", "promised_duration_min", "order_value", "hour_of_day",
        "day_of_week", "is_weekend", "is_peak_hour", "start_soc_pct", "ambient_temp_c",
        "current_soh_pct", "internal_resistance_m_ohm", "chemistry_type", "city"
    ]
    return df[feature_cols + ["target_failure", "start_time"]]

def build_segmentation_features():
    """
    Constructs feature matrix for Rider Behavioral Clustering (K-Means).
    """
    activity = pd.read_csv(f"{DATA_DIR}/rider_activity_daily.csv")
    riders = pd.read_csv(f"{DATA_DIR}/riders.csv")[["rider_id", "tier", "city", "rating_avg", "onboarding_status"]]

    active_riders = riders[riders["onboarding_status"].isin(["ACTIVE", "CHURNED"])].copy()

    agg = activity.groupby("rider_id").agg(
        days_active=("activity_date", "count"),
        total_hours=("hours_online", "sum"),
        avg_daily_hours=("hours_online", "mean"),
        total_deliveries=("deliveries_completed", "sum"),
        total_failed=("deliveries_failed", "sum"),
        total_earnings=("total_earnings", "mean"),
        avg_swaps_daily=("battery_swaps_count", "mean"),
        avg_peak_ratio=("peak_hour_ratio", "mean")
    ).reset_index()

    df = active_riders.merge(agg, on="rider_id", how="inner")
    df["failure_rate"] = df["total_failed"] / (df["total_deliveries"] + df["total_failed"] + 1e-4)
    df["deliveries_per_hour"] = df["total_deliveries"] / (df["total_hours"] + 1e-4)

    feature_cols = [
        "days_active", "avg_daily_hours", "total_deliveries", "total_earnings",
        "rating_avg", "avg_swaps_daily", "avg_peak_ratio", "failure_rate", "deliveries_per_hour"
    ]
    return df[feature_cols + ["rider_id", "tier", "city"]]
