-- ==============================================================================
-- 03: Battery Degradation, Thermal Stress, and Swap Analytics
-- Uses: CTEs, Window Functions (RANK, DENSE_RANK), Statistical Aggregations
-- ==============================================================================

-- 1. Degradation Rate Comparison: LFP vs NMC Chemistry
SELECT 
    b.chemistry_type,
    COUNT(b.battery_id) AS battery_count,
    ROUND(AVG(b.cycle_count), 1) AS avg_cycle_count,
    ROUND(AVG(b.current_soh_pct), 2) AS avg_current_soh_pct,
    ROUND(AVG((100.0 - b.current_soh_pct) / NULLIF(b.cycle_count, 0) * 100.0), 3) AS soh_loss_per_100_cycles,
    ROUND(AVG(b.internal_resistance_m_ohm), 2) AS avg_internal_resistance_mohm,
    ROUND(AVG(b.max_temp_celsius_recorded), 1) AS avg_peak_temp_celsius,
    SUM(CASE WHEN b.current_soh_pct < 75.0 THEN 1 ELSE 0 END) AS degraded_pack_count,
    ROUND(100.0 * SUM(CASE WHEN b.current_soh_pct < 75.0 THEN 1 ELSE 0 END) / COUNT(b.battery_id), 2) AS degraded_rate_pct
FROM batteries b
GROUP BY b.chemistry_type;

-- 2. Thermal Stress Deciles and Internal Resistance Correlation
WITH ThermalDeciles AS (
    SELECT 
        battery_id,
        chemistry_type,
        cycle_count,
        current_soh_pct,
        internal_resistance_m_ohm,
        max_temp_celsius_recorded,
        NTILE(5) OVER(ORDER BY max_temp_celsius_recorded ASC) AS thermal_stress_tier
    FROM batteries
)
SELECT 
    thermal_stress_tier,
    COUNT(battery_id) AS battery_count,
    ROUND(MIN(max_temp_celsius_recorded), 1) AS min_temp_c,
    ROUND(MAX(max_temp_celsius_recorded), 1) AS max_temp_c,
    ROUND(AVG(current_soh_pct), 2) AS avg_soh_pct,
    ROUND(AVG(internal_resistance_m_ohm), 2) AS avg_resistance_mohm,
    ROUND(AVG((100.0 - current_soh_pct) / NULLIF(cycle_count, 0) * 100.0), 3) AS avg_soh_loss_per_100_cycles
FROM ThermalDeciles
GROUP BY thermal_stress_tier
ORDER BY thermal_stress_tier;

-- 3. High-Risk Battery Packs Requiring Immediate Preventive Maintenance
SELECT 
    b.battery_id,
    s.supplier_name,
    s.tier AS supplier_tier,
    b.chemistry_type,
    b.cycle_count,
    b.current_soh_pct,
    b.internal_resistance_m_ohm,
    b.max_temp_celsius_recorded,
    b.status,
    DENSE_RANK() OVER(ORDER BY b.current_soh_pct ASC, b.internal_resistance_m_ohm DESC) AS replacement_priority_rank
FROM batteries b
JOIN suppliers s ON b.supplier_id = s.supplier_id
WHERE b.current_soh_pct < 75.0 OR b.internal_resistance_m_ohm > 40.0
ORDER BY b.current_soh_pct ASC, b.internal_resistance_m_ohm DESC
LIMIT 25;
