"""
EV Fleet & Rider Intelligence System - Data Generator
Generates realistic, physically grounded, synthetic EV fleet and logistics datasets
with realistic edge cases, degradation curves, churn behavioral dynamics, and delivery anomalies.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Set reproducible random seed
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

OUTPUT_DIR = "/workspace/data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

START_DATE = datetime(2025, 11, 1)
END_DATE = datetime(2026, 11, 15)
NUM_DAYS = (END_DATE - START_DATE).days

CITIES = ["Bangalore", "Delhi-NCR", "Hyderabad", "Mumbai", "Pune"]
CITY_WEIGHTS = [0.35, 0.25, 0.18, 0.14, 0.08]

def generate_suppliers():
    suppliers = [
        {"supplier_id": "SUP-001", "supplier_name": "VoltCell Innovations", "country": "South Korea", "rating": 4.8, "tier": "Tier-1", "contact_email": "ops@voltcell.kr", "contract_start_date": "2024-01-15"},
        {"supplier_id": "SUP-002", "supplier_name": "ElectroPower Mobility", "country": "Japan", "rating": 4.7, "tier": "Tier-1", "contact_email": "b2b@electropower.jp", "contract_start_date": "2024-03-01"},
        {"supplier_id": "SUP-003", "supplier_name": "AmpereDrive Systems", "country": "India", "rating": 4.2, "tier": "Tier-2", "contact_email": "fleet@amperedrive.in", "contract_start_date": "2024-06-10"},
        {"supplier_id": "SUP-004", "supplier_name": "Zenith Energy Tech", "country": "Taiwan", "rating": 4.1, "tier": "Tier-2", "contact_email": "sales@zenithenergy.tw", "contract_start_date": "2024-08-20"},
        {"supplier_id": "SUP-005", "supplier_name": "GreenCharge Labs", "country": "China", "rating": 3.4, "tier": "Tier-3", "contact_email": "service@greenchargelabs.cn", "contract_start_date": "2024-09-05"},
        {"supplier_id": "SUP-006", "supplier_name": "NexGen Energy Storage", "country": "India", "rating": 3.6, "tier": "Tier-3", "contact_email": "support@nexgenstorage.in", "contract_start_date": "2024-11-15"},
        {"supplier_id": "SUP-007", "supplier_name": "Titan Fleet Motors", "country": "Germany", "rating": 4.6, "tier": "Tier-1", "contact_email": "fleet@titanmotors.de", "contract_start_date": "2024-02-01"},
        {"supplier_id": "SUP-008", "supplier_name": "Apex EV Dynamics", "country": "India", "rating": 4.0, "tier": "Tier-2", "contact_email": "sales@apexev.in", "contract_start_date": "2024-05-18"}
    ]
    df = pd.DataFrame(suppliers)
    df.to_csv(f"{OUTPUT_DIR}/suppliers.csv", index=False)
    print(f"Generated {len(df)} suppliers.")
    return df

def generate_manufacturing_lots(suppliers_df):
    lots = []
    lot_counter = 1
    component_types = ["BATTERY", "VEHICLE_CHASSIS", "MOTOR"]
    
    for _, sup in suppliers_df.iterrows():
        num_lots = np.random.randint(3, 6)
        for _ in range(num_lots):
            lot_id = f"LOT-{lot_counter:04d}"
            comp = np.random.choice(component_types, p=[0.6, 0.25, 0.15])
            p_date = START_DATE - timedelta(days=int(np.random.randint(60, 360)))
            # Lower tier suppliers have higher baseline defect rate
            tier_defect_map = {"Tier-1": 0.012, "Tier-2": 0.035, "Tier-3": 0.082}
            base_defect = tier_defect_map[sup["tier"]]
            defect_rate = max(0.002, round(float(np.random.normal(base_defect, 0.008)), 4))
            
            lots.append({
                "lot_id": lot_id,
                "supplier_id": sup["supplier_id"],
                "component_type": comp,
                "production_date": p_date.strftime("%Y-%m-%d"),
                "defect_rate_estimate": defect_rate,
                "certification_standard": np.random.choice(["ISO-9001", "AIS-156", "UN-38.3", "CE-Cert"])
            })
            lot_counter += 1
            
    df = pd.DataFrame(lots)
    df.to_csv(f"{OUTPUT_DIR}/manufacturing_lots.csv", index=False)
    print(f"Generated {len(df)} manufacturing lots.")
    return df

def generate_batteries(suppliers_df, lots_df, num_batteries=800):
    battery_lots = lots_df[lots_df["component_type"] == "BATTERY"]
    batteries = []
    
    for i in range(1, num_batteries + 1):
        bat_id = f"BAT-{i:05d}"
        lot = battery_lots.sample(n=1, random_state=i).iloc[0]
        sup_id = lot["supplier_id"]
        
        # Chemistry: LFP (Lithium Iron Phosphate) vs NMC (Nickel Manganese Cobalt)
        chemistry = np.random.choice(["LFP", "NMC"], p=[0.65, 0.35])
        capacity = 3.2 if chemistry == "LFP" else 3.8 # kWh
        
        mfg_date = datetime.strptime(lot["production_date"], "%Y-%m-%d") + timedelta(days=int(np.random.randint(5, 30)))
        age_days = (END_DATE - mfg_date).days
        
        # Physical aging & cycling
        cycle_count = int(max(10, np.random.normal(age_days * 1.8, 40)))
        
        # SOH calculation: Degradation physics
        # Base calendar & cyclic degradation + temperature stress + lot defect bias
        temp_stress = float(np.random.uniform(32.0, 52.0)) # max recorded temp
        internal_resistance = round(float(22.0 + (cycle_count * 0.025) + (temp_stress - 30) * 0.4 + (lot["defect_rate_estimate"] * 80)), 2)
        
        # SOH degradation model
        soh_loss = (cycle_count * 0.022) + (max(0, temp_stress - 40) * 0.45) + (lot["defect_rate_estimate"] * 75) + np.random.normal(0, 1.5)
        current_soh = round(float(np.clip(100.0 - soh_loss, 58.0, 99.5)), 2)
        
        if current_soh < 70.0:
            status = np.random.choice(["DEGRADED", "REPLACED", "MAINTENANCE"], p=[0.4, 0.4, 0.2])
        elif current_soh < 82.0:
            status = np.random.choice(["ACTIVE", "CHARGING", "MAINTENANCE"], p=[0.75, 0.2, 0.05])
        else:
            status = np.random.choice(["ACTIVE", "CHARGING"], p=[0.8, 0.2])
            
        last_swap = END_DATE - timedelta(hours=int(np.random.randint(1, 72))) if status in ["ACTIVE", "CHARGING"] else None
        
        batteries.append({
            "battery_id": bat_id,
            "supplier_id": sup_id,
            "lot_id": lot["lot_id"],
            "serial_number": f"SN-{chemistry}-{i:06d}",
            "chemistry_type": chemistry,
            "nominal_capacity_kwh": capacity,
            "cycle_count": cycle_count,
            "current_soh_pct": current_soh,
            "max_temp_celsius_recorded": round(temp_stress, 1),
            "internal_resistance_m_ohm": internal_resistance,
            "status": status,
            "manufactured_date": mfg_date.strftime("%Y-%m-%d"),
            "last_swap_timestamp": last_swap.strftime("%Y-%m-%d %H:%M:%S") if last_swap else None
        })
        
    df = pd.DataFrame(batteries)
    df.to_csv(f"{OUTPUT_DIR}/batteries.csv", index=False)
    print(f"Generated {len(df)} batteries.")
    return df

def generate_vehicles(lots_df, batteries_df, num_vehicles=600):
    vehicle_lots = lots_df[lots_df["component_type"] == "VEHICLE_CHASSIS"]
    active_bats = batteries_df[batteries_df["status"] == "ACTIVE"]["battery_id"].tolist()
    
    vehicles = []
    models = ["VoltCruiser Pro", "VoltCargo Max", "AmpereSprint EV", "EcoRider Delivery"]
    
    for i in range(1, num_vehicles + 1):
        veh_id = f"VEH-{i:05d}"
        lot = vehicle_lots.sample(n=1, random_state=i).iloc[0]
        model = np.random.choice(models, p=[0.4, 0.3, 0.2, 0.1])
        city = np.random.choice(CITIES, p=CITY_WEIGHTS)
        reg_date = START_DATE - timedelta(days=int(np.random.randint(30, 300)))
        
        assigned_battery = active_bats[i % len(active_bats)] if i < len(active_bats) else None
        odometer = round(float(np.random.uniform(3500.0, 38000.0)), 1)
        status = np.random.choice(["ACTIVE", "MAINTENANCE", "RETIRED"], p=[0.90, 0.08, 0.02])
        
        vehicles.append({
            "vehicle_id": veh_id,
            "lot_id": lot["lot_id"],
            "model_name": model,
            "vin": f"EV9X{i:08X}IND",
            "registration_date": reg_date.strftime("%Y-%m-%d"),
            "total_odometer_km": odometer,
            "current_battery_id": assigned_battery,
            "status": status,
            "hub_city": city
        })
        
    df = pd.DataFrame(vehicles)
    df.to_csv(f"{OUTPUT_DIR}/vehicles.csv", index=False)
    print(f"Generated {len(df)} vehicles.")
    return df

def generate_riders(vehicles_df, num_riders=1200):
    first_names = ["Aarav", "Rohit", "Vikram", "Suresh", "Pooja", "Ananya", "Rahul", "Karthik", "Sneha", "Amit", 
                   "Deepak", "Manish", "Priya", "Sunil", "Rakesh", "Neha", "Vikas", "Aditya", "Sanjay", "Kavita"]
    last_names = ["Sharma", "Verma", "Patel", "Reddy", "Nair", "Rao", "Kumar", "Singh", "Joshi", "Das", 
                  "Gupta", "Mehta", "Chopra", "Yadav", "Bose", "Kulkarni", "Deshmukh", "Pillai"]
    
    active_vehicles = vehicles_df[vehicles_df["status"] == "ACTIVE"]["vehicle_id"].tolist()
    riders = []
    
    for i in range(1, num_riders + 1):
        rider_id = f"RDR-{i:05d}"
        fname = np.random.choice(first_names)
        lname = np.random.choice(last_names)
        full_name = f"{fname} {lname}"
        email = f"{fname.lower()}.{lname.lower()}{i}@riderfleet.io"
        phone = f"+91-98{np.random.randint(10000000, 99999999)}"
        city = np.random.choice(CITIES, p=CITY_WEIGHTS)
        
        # Signup spread across the year
        signup_offset = int(np.random.exponential(scale=110))
        signup_date = max(START_DATE, END_DATE - timedelta(days=min(365, signup_offset + 30)))
        
        # Activation logic (85% activate within 1-14 days; 15% never activate)
        will_activate = np.random.rand() < 0.86
        if will_activate:
            act_days = int(np.random.choice([1, 2, 3, 4, 5, 7, 10, 14], p=[0.35, 0.25, 0.15, 0.10, 0.05, 0.05, 0.03, 0.02]))
            activation_date = signup_date + timedelta(days=act_days)
            if activation_date > END_DATE:
                activation_date = None
                status = "ONBOARDING"
                churn_date = None
            else:
                # Churn behavior
                days_since_act = (END_DATE - activation_date).days
                # Churn hazard depends on rider experience, rating, days active
                churn_prob = 0.28 if days_since_act > 60 else 0.12
                is_churned = np.random.rand() < churn_prob
                if is_churned and days_since_act > 20:
                    status = "CHURNED"
                    churn_offset = int(np.random.uniform(15, days_since_act))
                    churn_date = activation_date + timedelta(days=churn_offset)
                else:
                    status = "ACTIVE" if np.random.rand() > 0.04 else "SUSPENDED"
                    churn_date = None
        else:
            activation_date = None
            status = "ONBOARDING"
            churn_date = None
            
        tier = np.random.choice(["STANDARD", "PREMIUM", "PRO"], p=[0.60, 0.28, 0.12])
        assigned_veh = active_vehicles[i % len(active_vehicles)] if status == "ACTIVE" and i < len(active_vehicles) * 1.5 else None
        
        # Synthetic performance stats
        rating_avg = round(float(np.clip(np.random.normal(4.65 if status == "ACTIVE" else 4.10, 0.35), 3.0, 5.0)), 2)
        lifetime_deliv = int(np.random.exponential(250)) if status != "ONBOARDING" else 0
        lifetime_earnings = round(float(lifetime_deliv * np.random.uniform(42.0, 68.0)), 2)
        
        riders.append({
            "rider_id": rider_id,
            "full_name": full_name,
            "phone": phone,
            "email": email,
            "city": city,
            "signup_date": signup_date.strftime("%Y-%m-%d"),
            "activation_date": activation_date.strftime("%Y-%m-%d") if activation_date else None,
            "onboarding_status": status,
            "vehicle_assigned_id": assigned_veh,
            "tier": tier,
            "rating_avg": rating_avg,
            "lifetime_deliveries": lifetime_deliv,
            "lifetime_earnings": lifetime_earnings,
            "churn_date": churn_date.strftime("%Y-%m-%d") if churn_date else None
        })
        
    df = pd.DataFrame(riders)
    df.to_csv(f"{OUTPUT_DIR}/riders.csv", index=False)
    print(f"Generated {len(df)} riders.")
    return df

def generate_operations(riders_df, vehicles_df, batteries_df):
    """
    Simulates operational trips, deliveries, transactions, and daily summaries
    over the 1-year timeline with EV dynamics and churn behavior.
    """
    active_riders = riders_df[riders_df["activation_date"].notna()].copy()
    active_riders["activation_dt"] = pd.to_datetime(active_riders["activation_date"])
    active_riders["churn_dt"] = pd.to_datetime(active_riders["churn_date"])
    
    veh_dict = vehicles_df.set_index("vehicle_id").to_dict("index")
    bat_dict = batteries_df.set_index("battery_id").to_dict("index")
    bat_ids = list(bat_dict.keys())
    
    trips = []
    deliveries = []
    transactions = []
    daily_activities = []
    
    trip_id_cnt = 1
    deliv_id_cnt = 1
    txn_id_cnt = 1
    act_id_cnt = 1
    
    # Pre-select active cohorts
    # To maintain snappy local run while ensuring ample statistical depth,
    # sample across daily timeline
    sample_dates = pd.date_range(START_DATE, END_DATE, freq="D")
    
    for current_dt in sample_dates:
        date_str = current_dt.strftime("%Y-%m-%d")
        # Find active pool for this date
        pool = active_riders[
            (active_riders["activation_dt"] <= current_dt) & 
            (active_riders["churn_dt"].isna() | (active_riders["churn_dt"] > current_dt))
        ]
        
        if len(pool) == 0:
            continue
            
        # Scale active riders per day to keep SQLite database strictly under 3.8 MB
        # and all CSVs under 1 MB for seamless instant workspace preview
        working_fraction = (0.42 + 0.08 * np.sin(current_dt.weekday() * 3.14 / 3.5)) * 0.014
        num_working = max(1, int(len(pool) * working_fraction))
        today_riders = pool.sample(n=min(num_working, len(pool)), random_state=int(current_dt.timestamp()) % 100000)
        
        for _, rider in today_riders.iterrows():
            r_id = rider["rider_id"]
            veh_id = rider["vehicle_assigned_id"]
            if not veh_id or veh_id not in veh_dict:
                veh_id = f"VEH-{(abs(hash(r_id)) % 500) + 1:05d}"
            
            # Select battery assigned or nearby swap
            bat_id = veh_dict.get(veh_id, {}).get("current_battery_id")
            if not bat_id or bat_id not in bat_dict:
                bat_id = bat_ids[abs(hash(r_id) + current_dt.day) % len(bat_ids)]
            bat_info = bat_dict[bat_id]
            
            # Daily activity parameters
            hours_online = round(float(np.clip(np.random.normal(6.5, 2.0), 1.0, 12.0)), 1)
            num_trips = max(1, int(hours_online * np.random.uniform(0.7, 1.4)))
            
            daily_trips_done = 0
            daily_deliv_done = 0
            daily_deliv_failed = 0
            daily_km = 0.0
            daily_earnings = 0.0
            daily_swaps = 1 if hours_online > 5.5 else 0
            
            # Simulate trips for this rider on this date
            hour_cursor = 8.0 + np.random.uniform(0, 2.5)
            for t in range(num_trips):
                if hour_cursor >= 22.0:
                    break
                    
                trip_id = f"TRP-{trip_id_cnt:07d}"
                trip_start = current_dt + timedelta(hours=hour_cursor, minutes=int(np.random.uniform(0, 30)))
                duration_min = np.random.uniform(15.0, 60.0)
                trip_end = trip_start + timedelta(minutes=duration_min)
                hour_cursor += (duration_min / 60.0) + np.random.uniform(0.1, 0.4)
                
                dist_km = round(float(np.clip(np.random.gamma(shape=3.0, scale=3.5), 1.5, 38.0)), 1)
                
                # EV energy physics: ~32 Wh/km base, ambient temp effect
                amb_temp = round(float(26.0 + 8.0 * np.sin((trip_start.hour - 8) / 14 * 3.14) + np.random.normal(0, 2)), 1)
                temp_penalty = 1.0 + max(0, amb_temp - 38) * 0.015 + max(0, 15 - amb_temp) * 0.02
                energy_kwh = round(float(dist_km * 0.033 * temp_penalty), 3)
                
                # SOC mechanics
                start_soc = round(float(np.random.uniform(65.0, 98.0)), 1)
                soc_drop = min(start_soc - 5.0, (energy_kwh / bat_info["nominal_capacity_kwh"]) * 100.0)
                end_soc = round(float(max(4.0, start_soc - soc_drop)), 1)
                avg_speed = round(float(np.random.uniform(18.0, 34.0)), 1)
                max_speed = round(float(avg_speed + np.random.uniform(10.0, 25.0)), 1)
                
                trips.append({
                    "trip_id": trip_id,
                    "rider_id": r_id,
                    "vehicle_id": veh_id,
                    "battery_id": bat_id,
                    "start_time": trip_start.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": trip_end.strftime("%Y-%m-%d %H:%M:%S"),
                    "distance_km": dist_km,
                    "energy_consumed_kwh": energy_kwh,
                    "start_soc_pct": start_soc,
                    "end_soc_pct": end_soc,
                    "avg_speed_kmh": avg_speed,
                    "max_speed_kmh": max_speed,
                    "ambient_temp_c": amb_temp,
                    "city": rider["city"]
                })
                trip_id_cnt += 1
                daily_trips_done += 1
                daily_km += dist_km
                
                # Delivery associated with trip (1 to 2 deliveries per trip)
                num_delivs_in_trip = 1 if np.random.rand() < 0.85 else 2
                for _ in range(num_delivs_in_trip):
                    deliv_id = f"DEL-{deliv_id_cnt:07d}"
                    deliv_dist = round(dist_km / num_delivs_in_trip, 1)
                    order_val = round(float(np.random.uniform(120.0, 1200.0)), 2)
                    promised_min = int(max(15, deliv_dist * 3.2 + np.random.normal(10, 4)))
                    
                    # Failure probability modeling
                    # Battery health + low end_soc + high temp + rider fatigue contribute
                    fail_hazard = 0.04
                    if bat_info["current_soh_pct"] < 72.0:
                        fail_hazard += 0.06
                    if end_soc < 10.0:
                        fail_hazard += 0.08
                    if hours_online > 9.0:
                        fail_hazard += 0.03
                        
                    is_failed = np.random.rand() < fail_hazard
                    if is_failed:
                        reasons = [
                            ("FAILED_BATTERY_DEPLETED", 0.35 if end_soc < 15 else 0.15),
                            ("FAILED_VEHICLE_BREAKDOWN", 0.25),
                            ("FAILED_TRAFFIC_DELAY", 0.20),
                            ("FAILED_CUSTOMER_UNREACHABLE", 0.15),
                            ("CANCELLED", 0.05)
                        ]
                        reasons_names = [r[0] for r in reasons]
                        weights = [r[1] for r in reasons]
                        weights = [w / sum(weights) for w in weights]
                        deliv_status = np.random.choice(reasons_names, p=weights)
                        fail_reason = deliv_status.replace("FAILED_", "").title()
                        actual_min = round(float(promised_min + np.random.uniform(15, 60)), 1)
                        delivered_at = None
                        cust_rating = None
                        daily_deliv_failed += 1
                    else:
                        deliv_status = "COMPLETED"
                        fail_reason = None
                        actual_min = round(float(max(10, promised_min + np.random.normal(-2, 5))), 1)
                        delivered_at = (trip_start + timedelta(minutes=actual_min)).strftime("%Y-%m-%d %H:%M:%S")
                        cust_rating = round(float(np.clip(np.random.choice([5.0, 4.0, 3.0, 2.0, 1.0], p=[0.72, 0.18, 0.05, 0.03, 0.02]), 1.0, 5.0)), 1) if np.random.rand() > 0.15 else None
                        daily_deliv_done += 1
                        
                        # Earning per completed delivery
                        earning_amt = round(float(40.0 + (deliv_dist * 8.5) + (5.0 if actual_min <= promised_min else 0.0)), 2)
                        daily_earnings += earning_amt
                        
                        transactions.append({
                            "transaction_id": f"TXN-{txn_id_cnt:08d}",
                            "rider_id": r_id,
                            "transaction_type": "EARNING",
                            "amount": earning_amt,
                            "transaction_time": delivered_at,
                            "payment_status": "SUCCESS",
                            "notes": f"Delivery payout for {deliv_id}"
                        })
                        txn_id_cnt += 1
                        
                    deliveries.append({
                        "delivery_id": deliv_id,
                        "trip_id": trip_id,
                        "rider_id": r_id,
                        "merchant_id": f"MCH-{(abs(hash(deliv_id)) % 80) + 1:03d}",
                        "customer_id": f"CUST-{(abs(hash(deliv_id)) % 1500) + 1:04d}",
                        "order_value": order_val,
                        "distance_km": deliv_dist,
                        "promised_duration_min": promised_min,
                        "actual_duration_min": actual_min,
                        "delivery_status": deliv_status,
                        "failure_reason": fail_reason,
                        "start_time": trip_start.strftime("%Y-%m-%d %H:%M:%S"),
                        "delivered_at": delivered_at,
                        "customer_rating": cust_rating,
                        "city": rider["city"]
                    })
                    deliv_id_cnt += 1
                    
            # Vehicle rental deduction ($6.00 / day)
            transactions.append({
                "transaction_id": f"TXN-{txn_id_cnt:08d}",
                "rider_id": r_id,
                "transaction_type": "RENTAL_DEDUCTION",
                "amount": -6.50,
                "transaction_time": (current_dt + timedelta(hours=23, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
                "payment_status": "SUCCESS",
                "notes": "Daily vehicle and battery lease charge"
            })
            txn_id_cnt += 1
            
            # Battery swap fee if swapped ($2.50)
            if daily_swaps > 0:
                transactions.append({
                    "transaction_id": f"TXN-{txn_id_cnt:08d}",
                    "rider_id": r_id,
                    "transaction_type": "BATTERY_SWAP_FEE",
                    "amount": -2.50 * daily_swaps,
                    "transaction_time": (current_dt + timedelta(hours=14, minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
                    "payment_status": "SUCCESS",
                    "notes": f"Battery swap fee ({daily_swaps} swap)"
                })
                txn_id_cnt += 1
                
            # Incentive bonus for high delivery count
            if daily_deliv_done >= 8:
                transactions.append({
                    "transaction_id": f"TXN-{txn_id_cnt:08d}",
                    "rider_id": r_id,
                    "transaction_type": "INCENTIVE_BONUS",
                    "amount": 15.00,
                    "transaction_time": (current_dt + timedelta(hours=23, minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
                    "payment_status": "SUCCESS",
                    "notes": "Target volume surge incentive"
                })
                txn_id_cnt += 1
                daily_earnings += 15.00
                
            daily_activities.append({
                "activity_id": f"ACT-{act_id_cnt:07d}",
                "rider_id": r_id,
                "activity_date": date_str,
                "hours_online": hours_online,
                "trips_completed": daily_trips_done,
                "deliveries_completed": daily_deliv_done,
                "deliveries_failed": daily_deliv_failed,
                "distance_km": round(daily_km, 1),
                "battery_swaps_count": daily_swaps,
                "total_earnings": round(daily_earnings, 2),
                "peak_hour_ratio": round(float(np.random.uniform(0.35, 0.75)), 2)
            })
            act_id_cnt += 1

    df_trips = pd.DataFrame(trips)
    df_trips.to_csv(f"{OUTPUT_DIR}/trips.csv", index=False)
    print(f"Generated {len(df_trips)} trips.")
    
    df_deliv = pd.DataFrame(deliveries)
    df_deliv.to_csv(f"{OUTPUT_DIR}/deliveries.csv", index=False)
    print(f"Generated {len(df_deliv)} deliveries.")
    
    df_txn = pd.DataFrame(transactions)
    df_txn.to_csv(f"{OUTPUT_DIR}/transactions.csv", index=False)
    print(f"Generated {len(df_txn)} transactions.")
    
    df_act = pd.DataFrame(daily_activities)
    df_act.to_csv(f"{OUTPUT_DIR}/rider_activity_daily.csv", index=False)
    print(f"Generated {len(df_act)} rider daily activity records.")

def main():
    print("Starting EV Fleet realistic synthetic data generation...")
    suppliers_df = generate_suppliers()
    lots_df = generate_manufacturing_lots(suppliers_df)
    batteries_df = generate_batteries(suppliers_df, lots_df, num_batteries=800)
    vehicles_df = generate_vehicles(lots_df, batteries_df, num_vehicles=600)
    riders_df = generate_riders(vehicles_df, num_riders=1200)
    generate_operations(riders_df, vehicles_df, batteries_df)
    print("Data generation complete! All CSV files saved to /workspace/data/raw/")

if __name__ == "__main__":
    main()
