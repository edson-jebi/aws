# Delice Data Lake - Athena Query Guide for Pasteurization Analysis

**Date:** March 4, 2026
**Industry:** Pasteurization & Food Processing
**Device:** Delice Pasteurization Equipment

---

## Table of Contents

1. [Athena Setup](#1-athena-setup)
2. [Basic Queries](#2-basic-queries)
3. [Pasteurization Process Monitoring](#3-pasteurization-process-monitoring)
4. [Temperature Analysis](#4-temperature-analysis)
5. [Equipment Performance](#5-equipment-performance)
6. [Cleaning & Maintenance](#6-cleaning--maintenance)
7. [Alarm & Safety Analysis](#7-alarm--safety-analysis)
8. [Efficiency & Optimization](#8-efficiency--optimization)
9. [Compliance & Reporting](#9-compliance--reporting)
10. [Advanced Analytics](#10-advanced-analytics)

---

## 1. Athena Setup

### **Step 1: Configure Athena Query Result Location**

1. Go to **AWS Console** → **Athena**
2. Click **Settings** (or **Manage** in new console)
3. Set **Query result location** to:
   ```
   s3://delice-datalake-parquet/athena-results/
   ```
4. Click **Save**

### **Step 2: Verify Glue Database and Table**

Run this query to verify your setup:

```sql
SHOW DATABASES;
```

Expected output: You should see `delice_db_v1` in the list.

```sql
SHOW TABLES IN delice_db_v1;
```

Expected output: You should see `delice_table_v1`.

### **Step 3: Test Basic Query**

```sql
SELECT COUNT(*) as total_records
FROM delice_db_v1.delice_table_v1;
```

This should return the total number of records in your data lake.

### **Step 4: Create Views for Easy Access**

```sql
-- Set the working database
USE delice_db_v1;

-- Create a view with human-readable timestamps
CREATE OR REPLACE VIEW delice_readable AS
SELECT
    device_id,
    from_unixtime(timestamp) AS datetime,
    DATE(from_unixtime(timestamp)) AS date,
    HOUR(from_unixtime(timestamp)) AS hour,
    temp_process_1,
    temp_process_2,
    temp_process_3,
    temp_water_1,
    temp_water_2,
    heating_set_point,
    cooling_set_point,
    water_temp_set_point,
    grid_valve_opening,
    steam_valve_opening,
    pump_frequency,
    product_pump_state,
    water_pump_state,
    product_state,
    status_main,
    status_product,
    water_flow_lph,
    tank_level,
    tank_return,
    detergent_concentration,
    cleaning_mode,
    heating_mode,
    cooling_mode,
    water_mode,
    alarm_active,
    emergency_stop
FROM delice_table_v1;
```

---

## 2. Basic Queries

### **2.1 View Recent Data**

```sql
-- Last 100 records
SELECT *
FROM delice_readable
ORDER BY datetime DESC
LIMIT 100;
```

### **2.2 Data for Specific Date**

```sql
-- Data for March 4, 2026
SELECT *
FROM delice_readable
WHERE date = DATE '2026-03-04'
ORDER BY datetime;
```

### **2.3 Data for Date Range**

```sql
-- Last 7 days
SELECT *
FROM delice_readable
WHERE datetime >= CURRENT_TIMESTAMP - INTERVAL '7' DAY
ORDER BY datetime DESC;
```

### **2.4 Data Summary by Hour**

```sql
-- Hourly record counts
SELECT
    date,
    hour,
    COUNT(*) as record_count
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY date, hour
ORDER BY date DESC, hour DESC;
```

---

## 3. Pasteurization Process Monitoring

### **3.1 Process Temperature Compliance**

Check if pasteurization temperatures meet regulatory requirements (typically 72°C for 15 seconds for milk):

```sql
-- Check if process temperatures meet minimum pasteurization threshold
SELECT
    datetime,
    device_id,
    temp_process_1,
    temp_process_2,
    temp_process_3,
    CASE
        WHEN temp_process_1 >= 72 AND temp_process_2 >= 72 AND temp_process_3 >= 72
        THEN 'COMPLIANT'
        ELSE 'NON-COMPLIANT'
    END AS compliance_status
FROM delice_readable
WHERE date = CURRENT_DATE
ORDER BY datetime DESC;
```

### **3.2 Temperature Deviation Analysis**

```sql
-- Find records where process temp deviates from set point by more than 2°C
SELECT
    datetime,
    temp_process_1,
    temp_process_2,
    temp_process_3,
    heating_set_point,
    ABS(temp_process_1 - heating_set_point) AS deviation_1,
    ABS(temp_process_2 - heating_set_point) AS deviation_2,
    ABS(temp_process_3 - heating_set_point) AS deviation_3
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '1' DAY
  AND (
    ABS(temp_process_1 - heating_set_point) > 2 OR
    ABS(temp_process_2 - heating_set_point) > 2 OR
    ABS(temp_process_3 - heating_set_point) > 2
  )
ORDER BY datetime DESC;
```

### **3.3 Process Cycle Duration**

```sql
-- Calculate duration of heating cycles
WITH process_states AS (
    SELECT
        datetime,
        heating_mode,
        cooling_mode,
        LAG(heating_mode) OVER (ORDER BY datetime) as prev_heating_mode
    FROM delice_readable
    WHERE date = CURRENT_DATE
)
SELECT
    datetime AS cycle_start,
    LEAD(datetime) OVER (ORDER BY datetime) AS cycle_end,
    date_diff('minute',
        datetime,
        LEAD(datetime) OVER (ORDER BY datetime)
    ) AS duration_minutes
FROM process_states
WHERE heating_mode = 1 AND prev_heating_mode = 0
ORDER BY datetime DESC;
```

### **3.4 Daily Process Summary**

```sql
-- Daily pasteurization process summary
SELECT
    date,
    COUNT(*) as total_readings,
    AVG(temp_process_1) as avg_temp_1,
    AVG(temp_process_2) as avg_temp_2,
    AVG(temp_process_3) as avg_temp_3,
    MIN(temp_process_1) as min_temp,
    MAX(temp_process_1) as max_temp,
    SUM(CASE WHEN heating_mode = 1 THEN 1 ELSE 0 END) as heating_readings,
    SUM(CASE WHEN cooling_mode = 1 THEN 1 ELSE 0 END) as cooling_readings
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date
ORDER BY date DESC;
```

---

## 4. Temperature Analysis

### **4.1 Temperature Trends Over Time**

```sql
-- 5-minute average temperatures for plotting
SELECT
    date_trunc('minute', datetime) -
        INTERVAL '0' MINUTE * (minute(datetime) % 5) AS time_bucket,
    AVG(temp_process_1) as avg_temp_process_1,
    AVG(temp_process_2) as avg_temp_process_2,
    AVG(temp_process_3) as avg_temp_process_3,
    AVG(temp_water_1) as avg_temp_water_1,
    AVG(heating_set_point) as avg_set_point
FROM delice_readable
WHERE datetime >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
GROUP BY 1
ORDER BY 1;
```

### **4.2 Temperature Sensor Correlation**

```sql
-- Check if all process sensors are reading similarly
SELECT
    date,
    AVG(temp_process_1) as avg_temp_1,
    AVG(temp_process_2) as avg_temp_2,
    AVG(temp_process_3) as avg_temp_3,
    ABS(AVG(temp_process_1) - AVG(temp_process_2)) as diff_1_2,
    ABS(AVG(temp_process_2) - AVG(temp_process_3)) as diff_2_3,
    ABS(AVG(temp_process_1) - AVG(temp_process_3)) as diff_1_3,
    CASE
        WHEN ABS(AVG(temp_process_1) - AVG(temp_process_2)) > 5
          OR ABS(AVG(temp_process_2) - AVG(temp_process_3)) > 5
          OR ABS(AVG(temp_process_1) - AVG(temp_process_3)) > 5
        THEN 'SENSOR DRIFT DETECTED'
        ELSE 'NORMAL'
    END as sensor_health
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY date
ORDER BY date DESC;
```

### **4.3 Heat-Up and Cool-Down Performance**

```sql
-- Analyze how quickly the system heats up
WITH temp_changes AS (
    SELECT
        datetime,
        temp_process_1,
        LAG(temp_process_1) OVER (ORDER BY datetime) as prev_temp,
        temp_process_1 - LAG(temp_process_1) OVER (ORDER BY datetime) as temp_change,
        heating_mode
    FROM delice_readable
    WHERE date = CURRENT_DATE
      AND heating_mode = 1
)
SELECT
    AVG(temp_change) as avg_temp_increase_per_reading,
    MAX(temp_change) as max_temp_increase,
    MIN(temp_change) as min_temp_increase
FROM temp_changes
WHERE temp_change > 0;
```

### **4.4 Temperature Stability Index**

```sql
-- Calculate temperature stability (lower is better)
SELECT
    date,
    STDDEV(temp_process_1) as temp_std_dev,
    AVG(temp_process_1) as temp_avg,
    (STDDEV(temp_process_1) / NULLIF(AVG(temp_process_1), 0)) * 100 as coefficient_of_variation,
    CASE
        WHEN STDDEV(temp_process_1) < 1 THEN 'VERY STABLE'
        WHEN STDDEV(temp_process_1) < 2 THEN 'STABLE'
        WHEN STDDEV(temp_process_1) < 5 THEN 'MODERATE'
        ELSE 'UNSTABLE'
    END as stability_rating
FROM delice_readable
WHERE heating_mode = 1
  AND date >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY date
ORDER BY date DESC;
```

---

## 5. Equipment Performance

### **5.1 Pump Operation Analysis**

```sql
-- Pump runtime and cycles
SELECT
    date,
    SUM(CASE WHEN product_pump_state = 1 THEN 1 ELSE 0 END) as product_pump_on_count,
    SUM(CASE WHEN water_pump_state = 1 THEN 1 ELSE 0 END) as water_pump_on_count,
    ROUND(SUM(CASE WHEN product_pump_state = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as product_pump_duty_cycle_pct,
    ROUND(SUM(CASE WHEN water_pump_state = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as water_pump_duty_cycle_pct,
    AVG(pump_frequency) as avg_pump_frequency
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date
ORDER BY date DESC;
```

### **5.2 Valve Position Analysis**

```sql
-- Analyze valve operation patterns
SELECT
    date,
    hour,
    AVG(grid_valve_opening) as avg_grid_valve,
    AVG(steam_valve_opening) as avg_steam_valve,
    MAX(grid_valve_opening) as max_grid_valve,
    MAX(steam_valve_opening) as max_steam_valve,
    MIN(grid_valve_opening) as min_grid_valve,
    MIN(steam_valve_opening) as min_steam_valve
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY date, hour
ORDER BY date DESC, hour DESC;
```

### **5.3 Water Flow Rate Analysis**

```sql
-- Water consumption and flow patterns
SELECT
    date,
    SUM(water_flow_lph) / 60.0 as total_liters_per_day,
    AVG(water_flow_lph) as avg_flow_rate_lph,
    MAX(water_flow_lph) as peak_flow_rate_lph,
    COUNT(CASE WHEN water_flow_lph > 0 THEN 1 END) as readings_with_flow
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date
ORDER BY date DESC;
```

### **5.4 Tank Level Monitoring**

```sql
-- Track tank levels and return flows
SELECT
    datetime,
    tank_level,
    tank_return,
    CASE
        WHEN tank_level < 20 THEN 'LOW LEVEL ALERT'
        WHEN tank_level > 90 THEN 'HIGH LEVEL ALERT'
        ELSE 'NORMAL'
    END as level_status
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '1' DAY
  AND (tank_level < 20 OR tank_level > 90)
ORDER BY datetime DESC;
```

---

## 6. Cleaning & Maintenance

### **6.1 Cleaning Cycle Analysis**

```sql
-- Track cleaning operations
SELECT
    date,
    SUM(CASE WHEN cleaning_mode = 1 THEN 1 ELSE 0 END) as cleaning_readings,
    AVG(CASE WHEN cleaning_mode = 1 THEN detergent_concentration END) as avg_detergent_pct,
    AVG(CASE WHEN cleaning_mode = 1 THEN temp_water_1 END) as avg_cleaning_temp,
    COUNT(DISTINCT CASE
        WHEN cleaning_mode = 1 AND LAG(cleaning_mode) OVER (ORDER BY datetime) = 0
        THEN datetime
    END) as cleaning_cycles
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date
ORDER BY date DESC;
```

### **6.2 Detergent Usage**

```sql
-- Monitor detergent concentration during cleaning
SELECT
    datetime,
    detergent_concentration,
    temp_water_1,
    cleaning_mode,
    CASE
        WHEN detergent_concentration < 1.5 THEN 'LOW CONCENTRATION'
        WHEN detergent_concentration > 3.5 THEN 'HIGH CONCENTRATION'
        ELSE 'OPTIMAL'
    END as concentration_status
FROM delice_readable
WHERE cleaning_mode = 1
  AND date >= CURRENT_DATE - INTERVAL '7' DAY
ORDER BY datetime DESC;
```

### **6.3 Cleaning Effectiveness Score**

```sql
-- Calculate cleaning cycle effectiveness
WITH cleaning_cycles AS (
    SELECT
        datetime,
        cleaning_mode,
        temp_water_1,
        detergent_concentration,
        water_flow_lph,
        CASE
            WHEN temp_water_1 >= 70 THEN 25
            WHEN temp_water_1 >= 60 THEN 20
            WHEN temp_water_1 >= 50 THEN 15
            ELSE 5
        END +
        CASE
            WHEN detergent_concentration >= 2.0 AND detergent_concentration <= 3.0 THEN 25
            WHEN detergent_concentration >= 1.5 THEN 15
            ELSE 5
        END +
        CASE
            WHEN water_flow_lph >= 100 THEN 25
            WHEN water_flow_lph >= 80 THEN 20
            ELSE 10
        END as effectiveness_score
    FROM delice_readable
    WHERE cleaning_mode = 1
)
SELECT
    DATE(datetime) as date,
    AVG(effectiveness_score) as avg_effectiveness,
    CASE
        WHEN AVG(effectiveness_score) >= 70 THEN 'EXCELLENT'
        WHEN AVG(effectiveness_score) >= 50 THEN 'GOOD'
        WHEN AVG(effectiveness_score) >= 30 THEN 'FAIR'
        ELSE 'POOR'
    END as cleaning_quality
FROM cleaning_cycles
GROUP BY DATE(datetime)
ORDER BY date DESC;
```

### **6.4 Maintenance Schedule Compliance**

```sql
-- Check if cleaning happens regularly
WITH daily_cleaning AS (
    SELECT
        date,
        MAX(CASE WHEN cleaning_mode = 1 THEN 1 ELSE 0 END) as had_cleaning
    FROM delice_readable
    WHERE date >= CURRENT_DATE - INTERVAL '30' DAY
    GROUP BY date
)
SELECT
    date,
    had_cleaning,
    CASE
        WHEN had_cleaning = 1 THEN 'COMPLIANT'
        ELSE 'MISSING CLEANING'
    END as maintenance_status
FROM daily_cleaning
ORDER BY date DESC;
```

---

## 7. Alarm & Safety Analysis

### **7.1 Alarm History**

```sql
-- Track all alarms
SELECT
    datetime,
    device_id,
    alarm_active,
    emergency_stop,
    temp_process_1,
    temp_process_2,
    temp_process_3,
    heating_mode,
    cooling_mode,
    product_state
FROM delice_readable
WHERE alarm_active = 1 OR emergency_stop = 1
ORDER BY datetime DESC;
```

### **7.2 Alarm Frequency Report**

```sql
-- Count alarms by day
SELECT
    date,
    SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as alarm_count,
    SUM(CASE WHEN emergency_stop = 1 THEN 1 ELSE 0 END) as emergency_stop_count,
    COUNT(*) as total_readings,
    ROUND(SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as alarm_percentage
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '90' DAY
GROUP BY date
ORDER BY date DESC;
```

### **7.3 Emergency Stop Analysis**

```sql
-- Find emergency stop events and context
SELECT
    datetime,
    temp_process_1,
    temp_process_2,
    temp_process_3,
    tank_level,
    product_pump_state,
    water_pump_state,
    heating_mode,
    alarm_active
FROM delice_readable
WHERE emergency_stop = 1
  AND datetime >= CURRENT_TIMESTAMP - INTERVAL '30' DAY
ORDER BY datetime DESC;
```

### **7.4 Safety Compliance Dashboard**

```sql
-- Daily safety metrics
SELECT
    date,
    COUNT(*) as total_readings,
    SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as alarms,
    SUM(CASE WHEN emergency_stop = 1 THEN 1 ELSE 0 END) as emergency_stops,
    SUM(CASE WHEN temp_process_1 > 100 THEN 1 ELSE 0 END) as over_temp_events,
    SUM(CASE WHEN tank_level < 10 THEN 1 ELSE 0 END) as low_tank_events,
    CASE
        WHEN SUM(CASE WHEN alarm_active = 1 OR emergency_stop = 1 THEN 1 ELSE 0 END) = 0
        THEN 'SAFE'
        ELSE 'INCIDENTS DETECTED'
    END as daily_safety_status
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date
ORDER BY date DESC;
```

---

## 8. Efficiency & Optimization

### **8.1 Energy Efficiency Analysis**

```sql
-- Estimate energy usage based on heating and pump operation
SELECT
    date,
    SUM(CASE WHEN heating_mode = 1 THEN 1 ELSE 0 END) as heating_readings,
    AVG(CASE WHEN heating_mode = 1 THEN steam_valve_opening END) as avg_steam_valve,
    AVG(pump_frequency) as avg_pump_freq,
    -- Rough energy index (higher = more energy used)
    (SUM(CASE WHEN heating_mode = 1 THEN steam_valve_opening ELSE 0 END) / COUNT(*)) *
    AVG(pump_frequency) as energy_usage_index
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date
ORDER BY date DESC;
```

### **8.2 Process Optimization Opportunities**

```sql
-- Find periods where equipment ran inefficiently
SELECT
    datetime,
    temp_process_1,
    heating_set_point,
    steam_valve_opening,
    ABS(temp_process_1 - heating_set_point) as temp_deviation,
    CASE
        WHEN temp_process_1 > heating_set_point + 5 AND steam_valve_opening > 50
        THEN 'OVERSHOOT - REDUCE STEAM'
        WHEN temp_process_1 < heating_set_point - 5 AND steam_valve_opening < 30
        THEN 'UNDERHEAT - INCREASE STEAM'
        ELSE 'OPTIMAL'
    END as optimization_suggestion
FROM delice_readable
WHERE heating_mode = 1
  AND date = CURRENT_DATE
  AND ABS(temp_process_1 - heating_set_point) > 3
ORDER BY datetime DESC;
```

### **8.3 Uptime and Availability**

```sql
-- Calculate system uptime
SELECT
    date,
    COUNT(*) as total_readings,
    SUM(CASE WHEN status_main = 1 THEN 1 ELSE 0 END) as operational_readings,
    ROUND(SUM(CASE WHEN status_main = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as uptime_percentage,
    CASE
        WHEN ROUND(SUM(CASE WHEN status_main = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) >= 95
        THEN 'EXCELLENT'
        WHEN ROUND(SUM(CASE WHEN status_main = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) >= 85
        THEN 'GOOD'
        ELSE 'NEEDS ATTENTION'
    END as availability_rating
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date
ORDER BY date DESC;
```

### **8.4 Batch Processing Efficiency**

```sql
-- Analyze product processing cycles
SELECT
    date,
    COUNT(DISTINCT CASE
        WHEN product_state != LAG(product_state) OVER (ORDER BY datetime)
        THEN datetime
    END) as state_changes,
    AVG(CASE WHEN product_state = 2 THEN 1 ELSE 0 END) * 100 as pct_time_processing,
    SUM(CASE WHEN product_pump_state = 1 THEN 1 ELSE 0 END) as pump_active_readings
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY date
ORDER BY date DESC;
```

---

## 9. Compliance & Reporting

### **9.1 Daily Production Report**

```sql
-- Comprehensive daily report for regulatory compliance
SELECT
    date,
    COUNT(*) as total_data_points,

    -- Temperature compliance
    AVG(temp_process_1) as avg_process_temp,
    MIN(temp_process_1) as min_process_temp,
    MAX(temp_process_1) as max_process_temp,
    SUM(CASE WHEN temp_process_1 >= 72 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
        as pct_above_pasteurization_temp,

    -- Equipment status
    SUM(CASE WHEN heating_mode = 1 THEN 1 ELSE 0 END) as heating_cycles,
    SUM(CASE WHEN cooling_mode = 1 THEN 1 ELSE 0 END) as cooling_cycles,
    SUM(CASE WHEN cleaning_mode = 1 THEN 1 ELSE 0 END) as cleaning_cycles,

    -- Safety events
    SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as alarm_events,
    SUM(CASE WHEN emergency_stop = 1 THEN 1 ELSE 0 END) as emergency_stops,

    -- Water usage
    SUM(water_flow_lph) / 60.0 as total_water_liters,

    -- Overall status
    CASE
        WHEN SUM(CASE WHEN alarm_active = 1 OR emergency_stop = 1 THEN 1 ELSE 0 END) = 0
         AND AVG(temp_process_1) >= 70
        THEN 'COMPLIANT'
        ELSE 'REVIEW REQUIRED'
    END as compliance_status

FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY date
ORDER BY date DESC;
```

### **9.2 Weekly Summary Report**

```sql
-- Weekly aggregated metrics
SELECT
    date_trunc('week', date) as week_start,
    COUNT(DISTINCT date) as days_in_operation,
    COUNT(*) as total_readings,
    AVG(temp_process_1) as avg_temp,
    SUM(CASE WHEN cleaning_mode = 1 THEN 1 ELSE 0 END) as cleaning_sessions,
    SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as total_alarms,
    SUM(water_flow_lph) / 60.0 as weekly_water_consumption_liters
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '12' WEEK
GROUP BY date_trunc('week', date)
ORDER BY week_start DESC;
```

### **9.3 Regulatory Audit Trail**

```sql
-- Critical events requiring documentation
SELECT
    datetime,
    'TEMPERATURE EXCURSION' as event_type,
    CONCAT('Process temp dropped to ', CAST(temp_process_1 AS VARCHAR), '°C') as description
FROM delice_readable
WHERE temp_process_1 < 65
  AND heating_mode = 1
  AND date >= CURRENT_DATE - INTERVAL '90' DAY

UNION ALL

SELECT
    datetime,
    'EMERGENCY STOP' as event_type,
    'Emergency stop activated' as description
FROM delice_readable
WHERE emergency_stop = 1
  AND date >= CURRENT_DATE - INTERVAL '90' DAY

UNION ALL

SELECT
    datetime,
    'CLEANING CYCLE' as event_type,
    CONCAT('Cleaning performed, detergent: ', CAST(detergent_concentration AS VARCHAR), '%') as description
FROM delice_readable
WHERE cleaning_mode = 1
  AND LAG(cleaning_mode, 1, 0) OVER (ORDER BY datetime) = 0
  AND date >= CURRENT_DATE - INTERVAL '90' DAY

ORDER BY datetime DESC;
```

### **9.4 HACCP Critical Control Point (CCP) Report**

```sql
-- Monitor Critical Control Points for HACCP compliance
SELECT
    date,
    -- CCP1: Pasteurization Temperature
    MIN(CASE WHEN heating_mode = 1 THEN temp_process_1 END) as min_pasteurization_temp,
    AVG(CASE WHEN heating_mode = 1 THEN temp_process_1 END) as avg_pasteurization_temp,
    SUM(CASE
        WHEN heating_mode = 1 AND temp_process_1 < 72 THEN 1
        ELSE 0
    END) as ccp1_violations,

    -- CCP2: Cooling Temperature
    MAX(CASE WHEN cooling_mode = 1 THEN temp_process_1 END) as max_cooling_temp,
    SUM(CASE
        WHEN cooling_mode = 1 AND temp_process_1 > 10 THEN 1
        ELSE 0
    END) as ccp2_violations,

    -- Overall CCP Status
    CASE
        WHEN SUM(CASE WHEN heating_mode = 1 AND temp_process_1 < 72 THEN 1 ELSE 0 END) = 0
         AND SUM(CASE WHEN cooling_mode = 1 AND temp_process_1 > 10 THEN 1 ELSE 0 END) = 0
        THEN 'PASS'
        ELSE 'FAIL - CORRECTIVE ACTION REQUIRED'
    END as ccp_compliance_status

FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY date
ORDER BY date DESC;
```

---

## 10. Advanced Analytics

### **10.1 Predictive Maintenance - Sensor Degradation**

```sql
-- Detect potential sensor failures by analyzing variance
WITH sensor_stats AS (
    SELECT
        date,
        STDDEV(temp_process_1) as std_1,
        STDDEV(temp_process_2) as std_2,
        STDDEV(temp_process_3) as std_3,
        AVG(temp_process_1) as avg_1,
        AVG(temp_process_2) as avg_2,
        AVG(temp_process_3) as avg_3
    FROM delice_readable
    WHERE date >= CURRENT_DATE - INTERVAL '30' DAY
    GROUP BY date
)
SELECT
    date,
    std_1,
    std_2,
    std_3,
    CASE
        WHEN std_1 > 10 THEN 'Sensor 1: High variance - check calibration'
        WHEN std_2 > 10 THEN 'Sensor 2: High variance - check calibration'
        WHEN std_3 > 10 THEN 'Sensor 3: High variance - check calibration'
        WHEN ABS(avg_1 - avg_2) > 5 THEN 'Sensor drift detected between 1 and 2'
        WHEN ABS(avg_2 - avg_3) > 5 THEN 'Sensor drift detected between 2 and 3'
        ELSE 'All sensors normal'
    END as maintenance_alert
FROM sensor_stats
ORDER BY date DESC;
```

### **10.2 Machine Learning Feature Extraction**

```sql
-- Extract features for ML model training
SELECT
    datetime,
    date,
    hour,

    -- Temperature features
    temp_process_1,
    temp_process_2,
    temp_process_3,
    (temp_process_1 + temp_process_2 + temp_process_3) / 3 as avg_process_temp,
    GREATEST(temp_process_1, temp_process_2, temp_process_3) -
        LEAST(temp_process_1, temp_process_2, temp_process_3) as temp_range,

    -- Set point tracking
    heating_set_point,
    temp_process_1 - heating_set_point as temp_error,

    -- Equipment state features
    heating_mode,
    cooling_mode,
    cleaning_mode,
    product_pump_state,
    water_pump_state,

    -- Control features
    steam_valve_opening,
    grid_valve_opening,
    pump_frequency,

    -- Flow and level features
    water_flow_lph,
    tank_level,

    -- Target variable (for anomaly detection)
    alarm_active as is_anomaly

FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '90' DAY
ORDER BY datetime;
```

### **10.3 Correlation Analysis**

```sql
-- Analyze correlations between variables
SELECT
    CORR(temp_process_1, steam_valve_opening) as temp_steam_correlation,
    CORR(temp_process_1, heating_set_point) as temp_setpoint_correlation,
    CORR(water_flow_lph, cooling_mode) as waterflow_cooling_correlation,
    CORR(pump_frequency, water_flow_lph) as pump_waterflow_correlation
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '7' DAY;
```

### **10.4 Anomaly Detection Query**

```sql
-- Detect anomalies using statistical methods
WITH stats AS (
    SELECT
        AVG(temp_process_1) as mean_temp,
        STDDEV(temp_process_1) as stddev_temp,
        AVG(water_flow_lph) as mean_flow,
        STDDEV(water_flow_lph) as stddev_flow
    FROM delice_readable
    WHERE date >= CURRENT_DATE - INTERVAL '7' DAY
)
SELECT
    d.datetime,
    d.temp_process_1,
    d.water_flow_lph,
    ABS(d.temp_process_1 - s.mean_temp) / s.stddev_temp as temp_z_score,
    ABS(d.water_flow_lph - s.mean_flow) / s.stddev_flow as flow_z_score,
    CASE
        WHEN ABS(d.temp_process_1 - s.mean_temp) / s.stddev_temp > 3 THEN 'TEMP ANOMALY'
        WHEN ABS(d.water_flow_lph - s.mean_flow) / s.stddev_flow > 3 THEN 'FLOW ANOMALY'
        ELSE 'NORMAL'
    END as anomaly_status
FROM delice_readable d
CROSS JOIN stats s
WHERE d.date = CURRENT_DATE
  AND (
    ABS(d.temp_process_1 - s.mean_temp) / s.stddev_temp > 3 OR
    ABS(d.water_flow_lph - s.mean_flow) / s.stddev_flow > 3
  )
ORDER BY d.datetime DESC;
```

---

## Quick Reference: Common Query Templates

### **Get Data for Last N Hours**
```sql
SELECT * FROM delice_readable
WHERE datetime >= CURRENT_TIMESTAMP - INTERVAL '{N}' HOUR
ORDER BY datetime DESC;
```

### **Get Data for Specific Date**
```sql
SELECT * FROM delice_readable
WHERE date = DATE '{YYYY-MM-DD}'
ORDER BY datetime;
```

### **Count Records by Day**
```sql
SELECT date, COUNT(*) as records
FROM delice_readable
GROUP BY date
ORDER BY date DESC;
```

### **Average Temperature by Hour**
```sql
SELECT date, hour, AVG(temp_process_1) as avg_temp
FROM delice_readable
WHERE date >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY date, hour
ORDER BY date DESC, hour DESC;
```

---

## Performance Optimization Tips

1. **Use Partitioning**: Queries filter by date for optimal Parquet partition pruning
2. **Limit Time Ranges**: Always use date/datetime filters to reduce data scanned
3. **Create Views**: Save complex queries as views for reuse
4. **Use CTAS**: Create Table As Select for frequently accessed aggregations
5. **Optimize WHERE clauses**: Put partition columns (date) first in WHERE clauses

---

## Next Steps

1. **Create Dashboards**: Use QuickSight or Grafana to visualize these queries
2. **Set Up Alerts**: Configure CloudWatch alarms based on query results
3. **Schedule Reports**: Use AWS Glue or Lambda to run reports automatically
4. **Export Data**: Save query results to S3 for archival or further processing
5. **Train ML Models**: Use feature extraction queries for predictive analytics

---

**Document Version:** 1.0
**Last Updated:** March 4, 2026
**Industry:** Pasteurization & Food Processing
