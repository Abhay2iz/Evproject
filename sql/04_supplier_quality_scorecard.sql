-- ==============================================================================
-- 04: Supplier Quality Scorecard and Component Reliability
-- Uses: Multi-table Joins, Aggregations, CTEs, CASE statements, Window Ranking
-- ==============================================================================

WITH LotStats AS (
    SELECT 
        supplier_id,
        COUNT(lot_id) AS total_lots_produced,
        ROUND(AVG(defect_rate_estimate) * 100.0, 3) AS avg_lot_defect_rate_pct
    FROM manufacturing_lots
    GROUP BY supplier_id
),
BatteryPerformance AS (
    SELECT 
        supplier_id,
        COUNT(battery_id) AS total_batteries_supplied,
        ROUND(AVG(current_soh_pct), 2) AS avg_battery_soh,
        ROUND(AVG(internal_resistance_m_ohm), 2) AS avg_internal_resistance,
        ROUND(AVG(max_temp_celsius_recorded), 1) AS avg_thermal_stress,
        SUM(CASE WHEN current_soh_pct < 75.0 THEN 1 ELSE 0 END) AS early_degraded_count,
        ROUND(100.0 * SUM(CASE WHEN current_soh_pct < 75.0 THEN 1 ELSE 0 END) / COUNT(battery_id), 2) AS degraded_rate_pct
    FROM batteries
    GROUP BY supplier_id
)
SELECT 
    s.supplier_id,
    s.supplier_name,
    s.country,
    s.tier,
    s.rating AS supplier_audit_rating,
    ls.total_lots_produced,
    ls.avg_lot_defect_rate_pct,
    bp.total_batteries_supplied,
    bp.avg_battery_soh,
    bp.avg_internal_resistance,
    bp.degraded_rate_pct,
    CASE 
        WHEN bp.degraded_rate_pct > 15.0 OR ls.avg_lot_defect_rate_pct > 5.0 THEN 'HIGH_RISK_WARRANTY_REVIEW'
        WHEN bp.degraded_rate_pct BETWEEN 5.0 AND 15.0 THEN 'MONITOR_CLOSELY'
        ELSE 'PREFERRED_PARTNER'
    END AS supplier_procurement_action,
    RANK() OVER(ORDER BY bp.avg_battery_soh DESC, bp.degraded_rate_pct ASC) AS quality_rank
FROM suppliers s
LEFT JOIN LotStats ls ON s.supplier_id = ls.supplier_id
LEFT JOIN BatteryPerformance bp ON s.supplier_id = bp.supplier_id
ORDER BY quality_rank ASC;
