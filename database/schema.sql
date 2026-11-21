-- ==============================================================================
-- EV Fleet & Rider Intelligence System - Relational Database Schema
-- Dialect: SQLite / ANSI SQL (Compatible with PostgreSQL / SQL Server with minimal adjustments)
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- 1. Suppliers
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id VARCHAR(32) PRIMARY KEY,
    supplier_name VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL,
    rating REAL CHECK (rating >= 1.0 AND rating <= 5.0),
    tier VARCHAR(20) NOT NULL, -- Tier-1, Tier-2, Tier-3
    contact_email VARCHAR(100),
    contract_start_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Manufacturing Lots
CREATE TABLE IF NOT EXISTS manufacturing_lots (
    lot_id VARCHAR(32) PRIMARY KEY,
    supplier_id VARCHAR(32) NOT NULL,
    component_type VARCHAR(50) NOT NULL, -- BATTERY, VEHICLE_CHASSIS, MOTOR
    production_date DATE NOT NULL,
    defect_rate_estimate REAL DEFAULT 0.0,
    certification_standard VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- 3. Batteries
CREATE TABLE IF NOT EXISTS batteries (
    battery_id VARCHAR(32) PRIMARY KEY,
    supplier_id VARCHAR(32) NOT NULL,
    lot_id VARCHAR(32) NOT NULL,
    serial_number VARCHAR(64) UNIQUE NOT NULL,
    chemistry_type VARCHAR(20) NOT NULL, -- LFP, NMC
    nominal_capacity_kwh REAL NOT NULL,
    cycle_count INTEGER DEFAULT 0,
    current_soh_pct REAL NOT NULL CHECK (current_soh_pct >= 0.0 AND current_soh_pct <= 100.0),
    max_temp_celsius_recorded REAL,
    internal_resistance_m_ohm REAL,
    status VARCHAR(20) NOT NULL, -- ACTIVE, CHARGING, DEGRADED, REPLACED, MAINTENANCE
    manufactured_date DATE NOT NULL,
    last_swap_timestamp TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
    FOREIGN KEY (lot_id) REFERENCES manufacturing_lots(lot_id)
);

-- 4. Vehicles
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id VARCHAR(32) PRIMARY KEY,
    lot_id VARCHAR(32) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    vin VARCHAR(64) UNIQUE NOT NULL,
    registration_date DATE NOT NULL,
    total_odometer_km REAL DEFAULT 0.0,
    current_battery_id VARCHAR(32),
    status VARCHAR(20) NOT NULL, -- ACTIVE, MAINTENANCE, RETIRED
    hub_city VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lot_id) REFERENCES manufacturing_lots(lot_id),
    FOREIGN KEY (current_battery_id) REFERENCES batteries(battery_id)
);

-- 5. Riders
CREATE TABLE IF NOT EXISTS riders (
    rider_id VARCHAR(32) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100) UNIQUE NOT NULL,
    city VARCHAR(50) NOT NULL,
    signup_date DATE NOT NULL,
    activation_date DATE,
    onboarding_status VARCHAR(20) NOT NULL, -- ACTIVE, CHURNED, SUSPENDED, ONBOARDING
    vehicle_assigned_id VARCHAR(32),
    tier VARCHAR(20) NOT NULL, -- STANDARD, PREMIUM, PRO
    rating_avg REAL DEFAULT 5.0,
    lifetime_deliveries INTEGER DEFAULT 0,
    lifetime_earnings REAL DEFAULT 0.0,
    churn_date DATE,
    FOREIGN KEY (vehicle_assigned_id) REFERENCES vehicles(vehicle_id)
);

-- 6. Trips
CREATE TABLE IF NOT EXISTS trips (
    trip_id VARCHAR(32) PRIMARY KEY,
    rider_id VARCHAR(32) NOT NULL,
    vehicle_id VARCHAR(32) NOT NULL,
    battery_id VARCHAR(32) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    distance_km REAL NOT NULL,
    energy_consumed_kwh REAL NOT NULL,
    start_soc_pct REAL NOT NULL,
    end_soc_pct REAL NOT NULL,
    avg_speed_kmh REAL NOT NULL,
    max_speed_kmh REAL NOT NULL,
    ambient_temp_c REAL NOT NULL,
    city VARCHAR(50) NOT NULL,
    FOREIGN KEY (rider_id) REFERENCES riders(rider_id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY (battery_id) REFERENCES batteries(battery_id)
);

-- 7. Deliveries
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id VARCHAR(32) PRIMARY KEY,
    trip_id VARCHAR(32),
    rider_id VARCHAR(32) NOT NULL,
    merchant_id VARCHAR(32) NOT NULL,
    customer_id VARCHAR(32) NOT NULL,
    order_value REAL NOT NULL,
    distance_km REAL NOT NULL,
    promised_duration_min INTEGER NOT NULL,
    actual_duration_min REAL,
    delivery_status VARCHAR(40) NOT NULL, -- COMPLETED, FAILED_CUSTOMER_UNREACHABLE, FAILED_VEHICLE_BREAKDOWN, FAILED_BATTERY_DEPLETED, FAILED_TRAFFIC_DELAY, CANCELLED
    failure_reason VARCHAR(100),
    start_time TIMESTAMP NOT NULL,
    delivered_at TIMESTAMP,
    customer_rating REAL,
    city VARCHAR(50) NOT NULL,
    FOREIGN KEY (trip_id) REFERENCES trips(trip_id),
    FOREIGN KEY (rider_id) REFERENCES riders(rider_id)
);

-- 8. Transactions
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(32) PRIMARY KEY,
    rider_id VARCHAR(32) NOT NULL,
    transaction_type VARCHAR(30) NOT NULL, -- EARNING, RENTAL_DEDUCTION, BATTERY_SWAP_FEE, INCENTIVE_BONUS, PENALTY
    amount REAL NOT NULL,
    transaction_time TIMESTAMP NOT NULL,
    payment_status VARCHAR(20) NOT NULL, -- SUCCESS, PENDING, FAILED
    notes TEXT,
    FOREIGN KEY (rider_id) REFERENCES riders(rider_id)
);

-- 9. Rider Daily Activity
CREATE TABLE IF NOT EXISTS rider_activity_daily (
    activity_id VARCHAR(32) PRIMARY KEY,
    rider_id VARCHAR(32) NOT NULL,
    activity_date DATE NOT NULL,
    hours_online REAL NOT NULL,
    trips_completed INTEGER DEFAULT 0,
    deliveries_completed INTEGER DEFAULT 0,
    deliveries_failed INTEGER DEFAULT 0,
    distance_km REAL DEFAULT 0.0,
    battery_swaps_count INTEGER DEFAULT 0,
    total_earnings REAL DEFAULT 0.0,
    peak_hour_ratio REAL DEFAULT 0.0,
    FOREIGN KEY (rider_id) REFERENCES riders(rider_id)
);

-- Indices for analytical query optimization
CREATE INDEX IF NOT EXISTS idx_trips_rider_time ON trips(rider_id, start_time);
CREATE INDEX IF NOT EXISTS idx_trips_battery_time ON trips(battery_id, start_time);
CREATE INDEX IF NOT EXISTS idx_deliveries_rider_time ON deliveries(rider_id, start_time);
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(delivery_status);
CREATE INDEX IF NOT EXISTS idx_activity_rider_date ON rider_activity_daily(rider_id, activity_date);
CREATE INDEX IF NOT EXISTS idx_transactions_rider_time ON transactions(rider_id, transaction_time);
CREATE INDEX IF NOT EXISTS idx_batteries_supplier ON batteries(supplier_id);
CREATE INDEX IF NOT EXISTS idx_riders_signup_status ON riders(signup_date, onboarding_status);
