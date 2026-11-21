-- ==============================================================================
-- 02: Delivery Success, Failure, and SLA Performance Analysis
-- Uses: Aggregations, Window Functions (PERCENT_RANK, NTILE), CASE statements, Subqueries
-- ==============================================================================

-- 1. Delivery Outcomes and Failure Root-Cause Distribution
SELECT 
    delivery_status,
    COUNT(delivery_id) AS delivery_count,
    ROUND(100.0 * COUNT(delivery_id) / (SELECT COUNT(*) FROM deliveries), 2) AS pct_of_total_deliveries,
    ROUND(AVG(distance_km), 2) AS avg_distance_km,
    ROUND(AVG(order_value), 2) AS avg_order_value,
    ROUND(AVG(actual_duration_min), 1) AS avg_duration_min,
    ROUND(AVG(customer_rating), 2) AS avg_rating
FROM deliveries
GROUP BY delivery_status
ORDER BY delivery_count DESC;

-- 2. Hourly SLA Breach and Failure Rates (Peak Hour vs Off-Peak)
WITH HourlyStats AS (
    SELECT 
        CAST(strftime('%H', start_time) AS INTEGER) AS hour_of_day,
        COUNT(delivery_id) AS total_deliveries,
        SUM(CASE WHEN delivery_status = 'COMPLETED' THEN 1 ELSE 0 END) AS completed_deliveries,
        SUM(CASE WHEN delivery_status != 'COMPLETED' THEN 1 ELSE 0 END) AS failed_deliveries,
        SUM(CASE 
            WHEN delivery_status = 'COMPLETED' AND actual_duration_min <= promised_duration_min 
            THEN 1 ELSE 0 
        END) AS on_time_deliveries
    FROM deliveries
    GROUP BY CAST(strftime('%H', start_time) AS INTEGER)
)
SELECT 
    hour_of_day,
    total_deliveries,
    failed_deliveries,
    ROUND(100.0 * failed_deliveries / total_deliveries, 2) AS failure_rate_pct,
    ROUND(100.0 * on_time_deliveries / completed_deliveries, 2) AS on_time_sla_rate_pct,
    CASE 
        WHEN hour_of_day IN (12, 13, 14, 19, 20, 21) THEN 'PEAK'
        ELSE 'STANDARD'
    END AS operational_period
FROM HourlyStats
ORDER BY hour_of_day;

-- 3. Rider Delivery Success Deciles (Identifying Top and Struggling Riders)
WITH RiderDeliveryAgg AS (
    SELECT 
        r.rider_id,
        r.tier,
        r.city,
        COUNT(d.delivery_id) AS total_orders,
        SUM(CASE WHEN d.delivery_status = 'COMPLETED' THEN 1 ELSE 0 END) AS successful_orders,
        ROUND(100.0 * SUM(CASE WHEN d.delivery_status = 'COMPLETED' THEN 1 ELSE 0 END) / COUNT(d.delivery_id), 2) AS success_rate_pct
    FROM riders r
    JOIN deliveries d ON r.rider_id = d.rider_id
    GROUP BY r.rider_id, r.tier, r.city
    HAVING COUNT(d.delivery_id) >= 20
),
DeciledRiders AS (
    SELECT 
        rider_id,
        tier,
        city,
        total_orders,
        success_rate_pct,
        NTILE(10) OVER(ORDER BY success_rate_pct DESC) AS performance_decile
    FROM RiderDeliveryAgg
)
SELECT 
    performance_decile,
    COUNT(rider_id) AS rider_count,
    ROUND(AVG(total_orders), 1) AS avg_orders_per_rider,
    ROUND(AVG(success_rate_pct), 2) AS avg_decile_success_rate_pct,
    ROUND(MIN(success_rate_pct), 2) AS min_success_rate_pct,
    ROUND(MAX(success_rate_pct), 2) AS max_success_rate_pct
FROM DeciledRiders
GROUP BY performance_decile
ORDER BY performance_decile;
