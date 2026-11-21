-- ==============================================================================
-- 05: Regional Fleet Density, Vehicle Utilization, and Operational Efficiency
-- Uses: CTEs, Window Aggregations, Joins, Group By with Rollups/Averages
-- ==============================================================================

WITH CityVehicles AS (
    SELECT 
        hub_city AS city,
        COUNT(vehicle_id) AS total_vehicles,
        SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) AS active_vehicles,
        SUM(CASE WHEN status = 'MAINTENANCE' THEN 1 ELSE 0 END) AS maintenance_vehicles,
        ROUND(AVG(total_odometer_km), 1) AS avg_odometer_km
    FROM vehicles
    GROUP BY hub_city
),
CityDeliveries AS (
    SELECT 
        city,
        COUNT(delivery_id) AS total_deliveries,
        SUM(CASE WHEN delivery_status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_deliveries,
        ROUND(100.0 * SUM(CASE WHEN delivery_status = 'COMPLETED' THEN 1 ELSE 0 END) / COUNT(delivery_id), 2) AS completion_rate_pct,
        ROUND(SUM(order_value), 2) AS total_gross_merchandise_val,
        ROUND(AVG(actual_duration_min), 1) AS avg_delivery_duration_min
    FROM deliveries
    GROUP BY city
),
CityRiders AS (
    SELECT 
        city,
        COUNT(rider_id) AS total_registered_riders,
        SUM(CASE WHEN onboarding_status = 'ACTIVE' THEN 1 ELSE 0 END) AS active_riders,
        SUM(CASE WHEN onboarding_status = 'CHURNED' THEN 1 ELSE 0 END) AS churned_riders
    FROM riders
    GROUP BY city
)
SELECT 
    cv.city,
    cv.total_vehicles,
    cv.active_vehicles,
    ROUND(100.0 * cv.active_vehicles / cv.total_vehicles, 2) AS vehicle_uptime_pct,
    cr.active_riders,
    ROUND(CAST(cr.active_riders AS REAL) / NULLIF(cv.active_vehicles, 0), 2) AS rider_to_vehicle_ratio,
    cd.total_deliveries,
    cd.completion_rate_pct,
    cd.total_gross_merchandise_val,
    ROUND(cd.total_deliveries / NULLIF(cv.active_vehicles, 0), 1) AS deliveries_per_active_vehicle
FROM CityVehicles cv
LEFT JOIN CityDeliveries cd ON cv.city = cd.city
LEFT JOIN CityRiders cr ON cv.city = cr.city
ORDER BY cd.total_deliveries DESC;
