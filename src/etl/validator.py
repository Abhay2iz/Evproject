"""
Data Quality Validation Suite for EV Fleet & Rider System.
Implements validation rules, boundary constraints, and anomaly detection.
"""

from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

class DataValidator:
    def __init__(self):
        self.validation_results = []
        self.errors = []
        self.warnings = []

    def validate_all(self, data: Dict[str, pd.DataFrame]) -> Dict:
        """Run all data quality validations."""
        self.validation_results = []
        self.errors = []
        self.warnings = []

        self._validate_nulls(data)
        self._validate_ranges(data)
        self._validate_referential_integrity(data)
        self._validate_temporal_logic(data)

        passed = len(self.errors) == 0
        return {
            "passed": passed,
            "total_checks": len(self.validation_results),
            "errors": self.errors,
            "warnings": self.warnings,
            "details": self.validation_results
        }

    def _validate_nulls(self, data: Dict[str, pd.DataFrame]):
        # Required non-null primary keys
        required_pk = {
            "suppliers": ["supplier_id", "supplier_name"],
            "manufacturing_lots": ["lot_id", "supplier_id"],
            "batteries": ["battery_id", "supplier_id", "chemistry_type", "current_soh_pct"],
            "vehicles": ["vehicle_id", "vin", "model_name"],
            "riders": ["rider_id", "email", "signup_date", "onboarding_status"],
            "trips": ["trip_id", "rider_id", "vehicle_id", "battery_id", "start_time", "distance_km"],
            "deliveries": ["delivery_id", "rider_id", "delivery_status", "start_time"],
            "transactions": ["transaction_id", "rider_id", "amount", "transaction_time"]
        }

        for tbl, cols in required_pk.items():
            if tbl in data:
                df = data[tbl]
                for col in cols:
                    null_count = int(df[col].isna().sum())
                    status = "PASS" if null_count == 0 else "FAIL"
                    msg = f"Table {tbl}.{col} has {null_count} nulls"
                    self.validation_results.append({"check": "null_check", "table": tbl, "column": col, "status": status, "message": msg})
                    if null_count > 0:
                        self.errors.append(msg)

    def _validate_ranges(self, data: Dict[str, pd.DataFrame]):
        # SOH must be between 0 and 100
        if "batteries" in data:
            df = data["batteries"]
            invalid_soh = df[(df["current_soh_pct"] < 0) | (df["current_soh_pct"] > 100)]
            if len(invalid_soh) > 0:
                err = f"Batteries: {len(invalid_soh)} rows with SOH outside [0, 100]"
                self.errors.append(err)
                self.validation_results.append({"check": "range_check", "table": "batteries", "status": "FAIL", "message": err})
            else:
                self.validation_results.append({"check": "range_check", "table": "batteries", "status": "PASS", "message": "All SOH within [0, 100]"})

        # Trips distance > 0, energy >= 0, SOC between 0 and 100
        if "trips" in data:
            df = data["trips"]
            invalid_dist = df[df["distance_km"] <= 0]
            invalid_soc = df[(df["start_soc_pct"] < 0) | (df["start_soc_pct"] > 100) | (df["end_soc_pct"] < 0) | (df["end_soc_pct"] > 100)]
            
            status = "PASS" if len(invalid_dist) == 0 else "FAIL"
            self.validation_results.append({"check": "range_check", "table": "trips.distance_km", "status": status, "message": f"{len(invalid_dist)} negative/zero distances"})
            if len(invalid_dist) > 0:
                self.errors.append(f"Trips: {len(invalid_dist)} invalid distance rows")

            status_soc = "PASS" if len(invalid_soc) == 0 else "FAIL"
            self.validation_results.append({"check": "range_check", "table": "trips.soc", "status": status_soc, "message": f"{len(invalid_soc)} invalid SOC rows"})
            if len(invalid_soc) > 0:
                self.errors.append(f"Trips: {len(invalid_soc)} invalid SOC rows")

    def _validate_referential_integrity(self, data: Dict[str, pd.DataFrame]):
        # Check that rider_ids in trips exist in riders
        if "trips" in data and "riders" in data:
            trip_riders = set(data["trips"]["rider_id"].unique())
            valid_riders = set(data["riders"]["rider_id"].unique())
            orphan_riders = trip_riders - valid_riders
            status = "PASS" if len(orphan_riders) == 0 else "FAIL"
            msg = f"{len(orphan_riders)} orphan rider_ids found in trips table"
            self.validation_results.append({"check": "foreign_key", "table": "trips -> riders", "status": status, "message": msg})
            if len(orphan_riders) > 0:
                self.errors.append(msg)

        # Check battery_id in trips exist in batteries
        if "trips" in data and "batteries" in data:
            trip_bats = set(data["trips"]["battery_id"].unique())
            valid_bats = set(data["batteries"]["battery_id"].unique())
            orphan_bats = trip_bats - valid_bats
            status = "PASS" if len(orphan_bats) == 0 else "FAIL"
            msg = f"{len(orphan_bats)} orphan battery_ids found in trips table"
            self.validation_results.append({"check": "foreign_key", "table": "trips -> batteries", "status": status, "message": msg})
            if len(orphan_bats) > 0:
                self.errors.append(msg)

    def _validate_temporal_logic(self, data: Dict[str, pd.DataFrame]):
        # Trip end_time must be >= start_time
        if "trips" in data:
            df = data["trips"]
            # Fast check on sample or vector
            t_start = pd.to_datetime(df["start_time"])
            t_end = pd.to_datetime(df["end_time"])
            invalids = (t_end < t_start).sum()
            status = "PASS" if invalids == 0 else "FAIL"
            msg = f"{invalids} trips have end_time before start_time"
            self.validation_results.append({"check": "temporal_logic", "table": "trips", "status": status, "message": msg})
            if invalids > 0:
                self.errors.append(msg)
