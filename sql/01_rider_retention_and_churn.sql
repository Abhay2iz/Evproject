-- ==============================================================================
-- 01: Rider Activation, Retention, and Churn Analytics
-- Uses: CTEs, Window Functions (ROW_NUMBER, DENSE_RANK, LAG, LEAD), CASE statements
-- ==============================================================================

-- 1. Monthly Signup Cohort Activation Rates
WITH MonthlyCohorts AS (
    SELECT 
        strftime('%Y-%m', signup_date) AS cohort_month,
        COUNT(rider_id) AS total_signups,
        SUM(CASE WHEN activation_date IS NOT NULL THEN 1 ELSE 0 END) AS activated_riders,
        AVG(CASE 
            WHEN activation_date IS NOT NULL 
            THEN (julianday(activation_date) - julianday(signup_date)) 
            ELSE NULL 
        END) AS avg_days_to_activate,
        SUM(CASE WHEN onboarding_status = 'CHURNED' THEN 1 ELSE 0 END) AS churned_riders
    FROM riders
    GROUP BY strftime('%Y-%m', signup_date)
)
SELECT 
    cohort_month,
    total_signups,
    activated_riders,
    ROUND(100.0 * activated_riders / total_signups, 2) AS activation_rate_pct,
    ROUND(avg_days_to_activate, 1) AS avg_activation_lag_days,
    churned_riders,
    ROUND(100.0 * churned_riders / NULLIF(activated_riders, 0), 2) AS churn_rate_of_activated_pct
FROM MonthlyCohorts
ORDER BY cohort_month;

-- 2. 7-Day and 30-Day Rider Retention Analysis
WITH RiderFirstActivity AS (
    SELECT 
        r.rider_id,
        r.signup_date,
        r.activation_date,
        r.city,
        r.tier,
        MIN(a.activity_date) AS first_active_date
    FROM riders r
    JOIN rider_activity_daily a ON r.rider_id = a.rider_id
    GROUP BY r.rider_id
),
ActivitySpans AS (
    SELECT 
        fa.rider_id,
        fa.tier,
        fa.city,
        fa.first_active_date,
        a.activity_date,
        (julianday(a.activity_date) - julianday(fa.first_active_date)) AS day_offset
    FROM RiderFirstActivity fa
    JOIN rider_activity_daily a ON fa.rider_id = a.rider_id
),
RetentionFlags AS (
    SELECT 
        rider_id,
        tier,
        city,
        MAX(CASE WHEN day_offset BETWEEN 1 AND 7 THEN 1 ELSE 0 END) AS retained_d7,
        MAX(CASE WHEN day_offset BETWEEN 8 AND 14 THEN 1 ELSE 0 END) AS retained_d14,
        MAX(CASE WHEN day_offset BETWEEN 15 AND 30 THEN 1 ELSE 0 END) AS retained_d30
    FROM ActivitySpans
    GROUP BY rider_id, tier, city
)
SELECT 
    tier,
    COUNT(rider_id) AS total_active_cohort_size,
    SUM(retained_d7) AS retained_day_7,
    ROUND(100.0 * SUM(retained_d7) / COUNT(rider_id), 2) AS d7_retention_pct,
    SUM(retained_d14) AS retained_day_14,
    ROUND(100.0 * SUM(retained_d14) / COUNT(rider_id), 2) AS d14_retention_pct,
    SUM(retained_d30) AS retained_day_30,
    ROUND(100.0 * SUM(retained_d30) / COUNT(rider_id), 2) AS d30_retention_pct
FROM RetentionFlags
GROUP BY tier
ORDER BY d30_retention_pct DESC;

-- 3. Inactivity Analysis and Churn Lead Indicator (Rolling 7-day hours trend)
WITH DailyHoursLagged AS (
    SELECT 
        rider_id,
        activity_date,
        hours_online,
        total_earnings,
        AVG(hours_online) OVER(
            PARTITION BY rider_id 
            ORDER BY activity_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS rolling_7d_avg_hours,
        LAG(hours_online, 1) OVER(
            PARTITION BY rider_id 
            ORDER BY activity_date
        ) AS prev_day_hours
    FROM rider_activity_daily
)
SELECT 
    rider_id,
    activity_date,
    hours_online,
    ROUND(rolling_7d_avg_hours, 2) AS rolling_7d_avg_hours,
    ROUND(hours_online - prev_day_hours, 2) AS day_over_day_hours_delta
FROM DailyHoursLagged
WHERE rolling_7d_avg_hours < 2.5
LIMIT 20;
