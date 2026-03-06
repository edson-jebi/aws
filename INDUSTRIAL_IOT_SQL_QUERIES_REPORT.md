# Industrial IoT Data Analytics - SQL Query Catalog

**Industry:** Mining, Pasteurization, Industrial Equipment Monitoring
**Data Sources:** AWS Timestream (Real-time) & AWS Athena/S3 (Historical)
**Date:** March 4, 2026

---

## Executive Summary

This document provides 15 industry-standard SQL queries for analyzing IoT data from multiple industrial devices including:
- **Delice** (Pasteurization equipment)
- **FESA_C15** (Mining equipment)
- **Shovel** (Mining excavation equipment)
- **HVE** (Heavy vehicle equipment)
- **Chinalco** (Mining operations)

Queries cover both **real-time operational monitoring** (Timestream) and **historical trend analysis** (Athena/S3 Data Lake).

---

## Data Sources Overview

### Real-Time Data (AWS Timestream)
- **Database:** `E2iDB`
- **Tables:**
  - `DeliceTableTimestream` - Pasteurization equipment
  - `FESA_C15` - Mining equipment
  - `Shovel` - Excavation equipment
  - `HVE` - Heavy vehicle equipment
  - `Chinalco` - Mining operations
- **Update Frequency:** Near real-time (seconds)
- **Retention:** Configurable (default: 30 days to 1 year)

### Historical Data (AWS Athena + S3)
- **Database:** `delice_db_v1`
- **Tables:**
  - `delice_table_v1` - Delice historical data (Parquet format)
- **Storage:** S3 Data Lake
- **Format:** Apache Parquet (compressed, columnar)
- **Retention:** Long-term (years)

---

## Query Categories

1. **Real-Time Monitoring** (Queries 1-5) - Timestream
2. **Historical Analysis** (Queries 6-10) - Athena
3. **Cross-Device Comparisons** (Queries 11-12) - Timestream
4. **Raw vs Processed Data** (Queries 13-15) - Both sources

---

# PART 1: REAL-TIME MONITORING (Timestream)

## Query 1: Equipment Uptime - Last 24 Hours

**Business Question:** "What is the current operational status and uptime percentage of all Delice pasteurization units in the last 24 hours?"

**Use Case:** Operations dashboard, real-time SLA monitoring

**SQL Query (Timestream):**
```sql
SELECT
    device_ID,
    COUNT(*) as total_readings,
    SUM(CASE WHEN status_main = 1 THEN 1 ELSE 0 END) as operational_readings,
    ROUND(
        CAST(SUM(CASE WHEN status_main = 1 THEN 1 ELSE 0 END) AS DOUBLE) /
        CAST(COUNT(*) AS DOUBLE) * 100,
        2
    ) as uptime_percentage,
    MAX(time) as last_seen
FROM "E2iDB"."DeliceTableTimestream"
WHERE time > ago(24h)
GROUP BY device_ID
ORDER BY uptime_percentage DESC
```

**Expected Output:**
```
device_ID         | total_readings | operational_readings | uptime_percentage | last_seen
------------------|----------------|---------------------|-------------------|------------------
DELICE_PLANT_01   | 43200         | 42890              | 99.28             | 2026-03-04 23:15:00
DELICE_PLANT_02   | 43200         | 41500              | 96.07             | 2026-03-04 23:14:58
```

---

## Query 2: Critical Temperature Alerts - Real-Time

**Business Question:** "Which pasteurization units currently have temperature readings outside safe operating ranges?"

**Use Case:** Safety monitoring, immediate alerts, quality control

**SQL Query (Timestream):**
```sql
SELECT
    device_ID,
    time,
    temp_process_1,
    temp_process_2,
    temp_process_3,
    heating_set_point,
    CASE
        WHEN temp_process_1 < 65 THEN 'CRITICAL: Below pasteurization threshold'
        WHEN temp_process_1 > 100 THEN 'CRITICAL: Overheating risk'
        WHEN ABS(temp_process_1 - heating_set_point) > 5 THEN 'WARNING: Deviation from setpoint'
        ELSE 'NORMAL'
    END as alert_status
FROM "E2iDB"."DeliceTableTimestream"
WHERE time > ago(15m)
  AND (
      temp_process_1 < 65 OR
      temp_process_1 > 100 OR
      ABS(temp_process_1 - heating_set_point) > 5
  )
ORDER BY time DESC
```

**Industry Standard:** Critical for HACCP compliance in food processing

---

## Query 3: Cross-Equipment Performance Comparison

**Business Question:** "Compare current operational efficiency across different equipment types (Delice, FESA, Shovel) in the last hour"

**Use Case:** Multi-site operations, fleet management

**SQL Query (Timestream):**
```sql
-- Delice Equipment
SELECT
    'Delice' as equipment_type,
    COUNT(DISTINCT device_ID) as active_units,
    AVG(temp_process_1) as avg_process_temp,
    SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as alarm_count,
    MAX(time) as last_update
FROM "E2iDB"."DeliceTableTimestream"
WHERE time > ago(1h)

UNION ALL

-- FESA Mining Equipment
SELECT
    'FESA_C15' as equipment_type,
    COUNT(DISTINCT device_ID) as active_units,
    NULL as avg_process_temp,
    SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as alarm_count,
    MAX(time) as last_update
FROM "E2iDB"."FESA_C15"
WHERE time > ago(1h)

UNION ALL

-- Shovel Equipment
SELECT
    'Shovel' as equipment_type,
    COUNT(DISTINCT device_ID) as active_units,
    NULL as avg_process_temp,
    SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as alarm_count,
    MAX(time) as last_update
FROM "E2iDB"."Shovel"
WHERE time > ago(1h)

ORDER BY equipment_type
```

---

## Query 4: Predictive Maintenance - Sensor Anomaly Detection

**Business Question:** "Identify equipment showing abnormal sensor behavior that may indicate pending failure"

**Use Case:** Predictive maintenance, reduce unplanned downtime

**SQL Query (Timestream):**
```sql
WITH recent_stats AS (
    SELECT
        device_ID,
        AVG(temp_process_1) as avg_temp,
        STDDEV(temp_process_1) as stddev_temp,
        MAX(temp_process_1) as max_temp,
        MIN(temp_process_1) as min_temp,
        COUNT(*) as reading_count
    FROM "E2iDB"."DeliceTableTimestream"
    WHERE time > ago(6h)
    GROUP BY device_ID
)
SELECT
    device_ID,
    avg_temp,
    stddev_temp,
    max_temp - min_temp as temperature_range,
    CASE
        WHEN stddev_temp > 10 THEN 'HIGH VARIANCE - Check sensor calibration'
        WHEN max_temp - min_temp > 30 THEN 'EXCESSIVE FLUCTUATION - Possible control issue'
        WHEN reading_count < 1000 THEN 'LOW DATA FREQUENCY - Connectivity issue'
        ELSE 'NORMAL'
    END as maintenance_flag
FROM recent_stats
WHERE
    stddev_temp > 10 OR
    (max_temp - min_temp) > 30 OR
    reading_count < 1000
ORDER BY stddev_temp DESC
```

**Industry Context:** Reduces unplanned downtime by 30-40% (Gartner)

---

## Query 5: Production Rate - Real-Time Throughput

**Business Question:** "What is the current production throughput and water consumption rate across all active pasteurization lines?"

**Use Case:** Production planning, resource optimization

**SQL Query (Timestream):**
```sql
SELECT
    device_ID,
    bin(time, 5m) as time_window,
    COUNT(*) as cycles_per_5min,
    AVG(water_flow_lph) as avg_water_flow,
    SUM(water_flow_lph) / 12.0 as total_liters_per_5min,
    AVG(temp_process_1) as avg_process_temp,
    SUM(CASE WHEN product_pump_state = 1 THEN 1 ELSE 0 END) as pump_active_count
FROM "E2iDB"."DeliceTableTimestream"
WHERE time > ago(1h)
  AND status_main = 1
GROUP BY device_ID, bin(time, 5m)
ORDER BY time_window DESC, device_ID
```

---

# PART 2: HISTORICAL ANALYSIS (Athena / S3 Data Lake)

## Query 6: Long-Term Temperature Compliance Report

**Business Question:** "Generate a 90-day compliance report showing pasteurization temperature adherence to regulatory standards"

**Use Case:** Regulatory audits, quality assurance, HACCP documentation

**SQL Query (Athena):**
```sql
SELECT
    DATE(from_unixtime(timestamp)) as date,
    COUNT(*) as total_records,

    -- Temperature compliance metrics
    SUM(CASE WHEN temp_process_1 >= 72 AND temp_process_1 <= 95 THEN 1 ELSE 0 END) as compliant_records,
    SUM(CASE WHEN temp_process_1 < 72 THEN 1 ELSE 0 END) as below_threshold,
    SUM(CASE WHEN temp_process_1 > 95 THEN 1 ELSE 0 END) as above_threshold,

    -- Percentage calculations
    ROUND(
        CAST(SUM(CASE WHEN temp_process_1 >= 72 AND temp_process_1 <= 95 THEN 1 ELSE 0 END) AS DOUBLE) /
        CAST(COUNT(*) AS DOUBLE) * 100,
        2
    ) as compliance_percentage,

    -- Temperature statistics
    ROUND(AVG(temp_process_1), 2) as avg_temp,
    ROUND(MIN(temp_process_1), 2) as min_temp,
    ROUND(MAX(temp_process_1), 2) as max_temp,
    ROUND(STDDEV(temp_process_1), 2) as temp_std_dev,

    -- Regulatory status
    CASE
        WHEN CAST(SUM(CASE WHEN temp_process_1 >= 72 THEN 1 ELSE 0 END) AS DOUBLE) / CAST(COUNT(*) AS DOUBLE) >= 0.99
        THEN 'PASS - 99%+ Compliance'
        WHEN CAST(SUM(CASE WHEN temp_process_1 >= 72 THEN 1 ELSE 0 END) AS DOUBLE) / CAST(COUNT(*) AS DOUBLE) >= 0.95
        THEN 'MARGINAL - 95-99% Compliance'
        ELSE 'FAIL - Below 95% Compliance'
    END as regulatory_status

FROM delice_db_v1.delice_table_v1
WHERE from_unixtime(timestamp) >= CURRENT_DATE - INTERVAL '90' DAY
GROUP BY DATE(from_unixtime(timestamp))
ORDER BY date DESC
```

**Compliance Standard:** FDA requires 72°C for 15 seconds (HTST pasteurization)

---

## Query 7: Equipment Lifecycle Analysis - Historical Degradation

**Business Question:** "Analyze equipment performance degradation over time to plan maintenance windows and replacements"

**Use Case:** Capital planning, maintenance scheduling

**SQL Query (Athena):**
```sql
WITH monthly_performance AS (
    SELECT
        device_id,
        DATE_TRUNC('month', from_unixtime(timestamp)) as month,

        -- Operational metrics
        COUNT(*) as total_operations,
        AVG(temp_process_1) as avg_temp,
        STDDEV(temp_process_1) as temp_variance,

        -- Efficiency indicators
        AVG(CAST(temp_process_1 - heating_set_point AS DOUBLE)) as avg_temp_error,
        AVG(steam_valve_opening) as avg_steam_usage,
        AVG(pump_frequency) as avg_pump_frequency,

        -- Failure indicators
        SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as alarm_count,
        SUM(CASE WHEN emergency_stop = 1 THEN 1 ELSE 0 END) as emergency_stops

    FROM delice_db_v1.delice_table_v1
    WHERE from_unixtime(timestamp) >= DATE_TRUNC('year', CURRENT_DATE)
    GROUP BY device_id, DATE_TRUNC('month', from_unixtime(timestamp))
)
SELECT
    device_id,
    month,
    avg_temp,
    temp_variance,
    avg_temp_error,
    avg_steam_usage,
    alarm_count,

    -- Degradation indicators
    avg_steam_usage - LAG(avg_steam_usage) OVER (PARTITION BY device_id ORDER BY month) as steam_usage_increase,
    temp_variance - LAG(temp_variance) OVER (PARTITION BY device_id ORDER BY month) as variance_increase,

    -- Health score (0-100)
    ROUND(
        100 -
        (temp_variance * 2) -
        (alarm_count * 0.5) -
        (ABS(avg_temp_error) * 3),
        2
    ) as equipment_health_score

FROM monthly_performance
ORDER BY device_id, month DESC
```

---

## Query 8: Water Consumption and Cost Analysis

**Business Question:** "Calculate total water consumption and estimated costs per production batch over the last quarter"

**Use Case:** Cost optimization, sustainability reporting

**SQL Query (Athena):**
```sql
SELECT
    DATE_TRUNC('week', from_unixtime(timestamp)) as week,
    device_id,

    -- Water consumption
    SUM(water_flow_lph) / 60.0 as total_liters,
    SUM(water_flow_lph) / 60.0 / 1000.0 as total_cubic_meters,

    -- Production metrics
    COUNT(*) as operating_hours,
    SUM(CASE WHEN heating_mode = 1 THEN 1 ELSE 0 END) as heating_hours,
    SUM(CASE WHEN cooling_mode = 1 THEN 1 ELSE 0 END) as cooling_hours,
    SUM(CASE WHEN cleaning_mode = 1 THEN 1 ELSE 0 END) as cleaning_hours,

    -- Cost calculations (example rate: $2 per cubic meter)
    ROUND(SUM(water_flow_lph) / 60.0 / 1000.0 * 2.0, 2) as estimated_water_cost_usd,

    -- Efficiency metrics
    ROUND(
        SUM(water_flow_lph) / 60.0 /
        NULLIF(SUM(CASE WHEN heating_mode = 1 THEN 1 ELSE 0 END), 0),
        2
    ) as liters_per_production_hour

FROM delice_db_v1.delice_table_v1
WHERE from_unixtime(timestamp) >= CURRENT_DATE - INTERVAL '90' DAY
  AND water_flow_lph > 0
GROUP BY DATE_TRUNC('week', from_unixtime(timestamp)), device_id
ORDER BY week DESC, device_id
```

**Industry Benchmark:** Food processing uses 2-10 liters per kg product

---

## Query 9: Cleaning Cycle Effectiveness - Historical Trends

**Business Question:** "Analyze cleaning cycle frequency, duration, and effectiveness over time to optimize CIP (Clean-In-Place) schedules"

**Use Case:** Sanitation compliance, operational efficiency

**SQL Query (Athena):**
```sql
WITH cleaning_cycles AS (
    SELECT
        device_id,
        from_unixtime(timestamp) as event_time,
        DATE(from_unixtime(timestamp)) as date,
        cleaning_mode,
        detergent_concentration,
        temp_water_1 as cleaning_temp,
        water_flow_lph,

        -- Detect cycle starts
        CASE
            WHEN cleaning_mode = 1 AND
                 LAG(cleaning_mode, 1, 0) OVER (PARTITION BY device_id ORDER BY timestamp) = 0
            THEN 1
            ELSE 0
        END as cycle_start

    FROM delice_db_v1.delice_table_v1
    WHERE from_unixtime(timestamp) >= CURRENT_DATE - INTERVAL '30' DAY
),
cycle_summary AS (
    SELECT
        device_id,
        date,
        SUM(cycle_start) as cleaning_cycles,
        AVG(CASE WHEN cleaning_mode = 1 THEN detergent_concentration END) as avg_detergent_pct,
        AVG(CASE WHEN cleaning_mode = 1 THEN cleaning_temp END) as avg_cleaning_temp,
        SUM(CASE WHEN cleaning_mode = 1 THEN 1 ELSE 0 END) as cleaning_duration_readings
    FROM cleaning_cycles
    GROUP BY device_id, date
)
SELECT
    device_id,
    date,
    cleaning_cycles,
    cleaning_duration_readings / 60 as estimated_duration_hours,
    avg_detergent_pct,
    avg_cleaning_temp,

    -- Effectiveness score (0-100)
    ROUND(
        (CASE
            WHEN avg_cleaning_temp >= 75 THEN 40
            WHEN avg_cleaning_temp >= 65 THEN 30
            ELSE 15
        END) +
        (CASE
            WHEN avg_detergent_pct BETWEEN 2.0 AND 3.0 THEN 40
            WHEN avg_detergent_pct BETWEEN 1.5 AND 3.5 THEN 30
            ELSE 15
        END) +
        (CASE
            WHEN cleaning_cycles >= 1 THEN 20
            ELSE 0
        END),
        2
    ) as cleaning_effectiveness_score,

    -- Compliance status
    CASE
        WHEN cleaning_cycles = 0 THEN 'NON-COMPLIANT: No cleaning'
        WHEN avg_cleaning_temp < 65 THEN 'NON-COMPLIANT: Low temperature'
        WHEN avg_detergent_pct < 1.5 THEN 'NON-COMPLIANT: Low detergent'
        ELSE 'COMPLIANT'
    END as sanitation_compliance

FROM cycle_summary
ORDER BY date DESC, device_id
```

**FDA Requirement:** Daily cleaning for food contact surfaces

---

## Query 10: Energy Consumption Pattern Analysis

**Business Question:** "Identify peak energy consumption periods and opportunities for load shifting to reduce electricity costs"

**Use Case:** Energy management, cost reduction

**SQL Query (Athena):**
```sql
SELECT
    HOUR(from_unixtime(timestamp)) as hour_of_day,
    DATE_TRUNC('day', from_unixtime(timestamp)) as date,

    -- Energy proxy metrics (higher values = more energy)
    COUNT(*) as operations_count,
    SUM(CASE WHEN heating_mode = 1 THEN 1 ELSE 0 END) as heating_operations,
    SUM(CASE WHEN cooling_mode = 1 THEN 1 ELSE 0 END) as cooling_operations,

    AVG(steam_valve_opening) as avg_steam_valve,
    AVG(pump_frequency) as avg_pump_frequency,

    -- Energy intensity index (0-100)
    ROUND(
        (AVG(steam_valve_opening) * 0.5) +
        (AVG(pump_frequency) * 0.3) +
        (CAST(SUM(CASE WHEN heating_mode = 1 THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*) * 20),
        2
    ) as energy_intensity_index,

    -- Cost implications (example: $0.15/kWh peak, $0.08/kWh off-peak)
    CASE
        WHEN HOUR(from_unixtime(timestamp)) BETWEEN 7 AND 22 THEN 'PEAK RATE ($0.15/kWh)'
        ELSE 'OFF-PEAK RATE ($0.08/kWh)'
    END as electricity_rate_period

FROM delice_db_v1.delice_table_v1
WHERE from_unixtime(timestamp) >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY HOUR(from_unixtime(timestamp)), DATE_TRUNC('day', from_unixtime(timestamp))
ORDER BY date DESC, hour_of_day
```

**Optimization Opportunity:** Load shifting can reduce energy costs by 20-40%

---

# PART 3: CROSS-DEVICE & FLEET ANALYSIS

## Query 11: Multi-Equipment Operational Dashboard

**Business Question:** "Create a unified operational dashboard showing current status of all equipment types across the facility"

**Use Case:** Central operations monitoring, executive dashboard

**SQL Query (Timestream - Multi-table):**
```sql
-- Delice Pasteurization Units
SELECT
    'DELICE' as equipment_category,
    device_ID as equipment_id,
    time as last_update,
    'temp_process_1' as primary_metric_name,
    temp_process_1 as primary_metric_value,
    status_main as operational_status,
    alarm_active as has_alarm
FROM "E2iDB"."DeliceTableTimestream"
WHERE time > ago(5m)
  AND time = (SELECT MAX(time) FROM "E2iDB"."DeliceTableTimestream" WHERE device_ID = device_ID)

UNION ALL

-- FESA Mining Equipment
SELECT
    'FESA_MINING' as equipment_category,
    device_ID as equipment_id,
    time as last_update,
    'engine_temp' as primary_metric_name,
    engine_temp as primary_metric_value,
    operational_status,
    alarm_active as has_alarm
FROM "E2iDB"."FESA_C15"
WHERE time > ago(5m)
  AND time = (SELECT MAX(time) FROM "E2iDB"."FESA_C15" WHERE device_ID = device_ID)

UNION ALL

-- Shovel Equipment
SELECT
    'SHOVEL' as equipment_category,
    device_ID as equipment_id,
    time as last_update,
    'hydraulic_pressure' as primary_metric_name,
    hydraulic_pressure as primary_metric_value,
    operational_status,
    alarm_active as has_alarm
FROM "E2iDB"."Shovel"
WHERE time > ago(5m)
  AND time = (SELECT MAX(time) FROM "E2iDB"."Shovel" WHERE device_ID = device_ID)

ORDER BY equipment_category, equipment_id
```

---

## Query 12: Cross-Equipment Failure Correlation

**Business Question:** "Identify if failures in one equipment type correlate with issues in other equipment (e.g., power grid issues affecting multiple systems)"

**Use Case:** Root cause analysis, infrastructure monitoring

**SQL Query (Timestream - Time-based correlation):**
```sql
WITH delice_alarms AS (
    SELECT
        bin(time, 1m) as time_bucket,
        COUNT(*) as delice_alarm_count
    FROM "E2iDB"."DeliceTableTimestream"
    WHERE time > ago(24h)
      AND alarm_active = 1
    GROUP BY bin(time, 1m)
),
fesa_alarms AS (
    SELECT
        bin(time, 1m) as time_bucket,
        COUNT(*) as fesa_alarm_count
    FROM "E2iDB"."FESA_C15"
    WHERE time > ago(24h)
      AND alarm_active = 1
    GROUP BY bin(time, 1m)
),
shovel_alarms AS (
    SELECT
        bin(time, 1m) as time_bucket,
        COUNT(*) as shovel_alarm_count
    FROM "E2iDB"."Shovel"
    WHERE time > ago(24h)
      AND alarm_active = 1
    GROUP BY bin(time, 1m)
)
SELECT
    COALESCE(d.time_bucket, f.time_bucket, s.time_bucket) as time_bucket,
    COALESCE(d.delice_alarm_count, 0) as delice_alarms,
    COALESCE(f.fesa_alarm_count, 0) as fesa_alarms,
    COALESCE(s.shovel_alarm_count, 0) as shovel_alarms,

    -- Correlation flag
    CASE
        WHEN COALESCE(d.delice_alarm_count, 0) > 0 AND
             COALESCE(f.fesa_alarm_count, 0) > 0 AND
             COALESCE(s.shovel_alarm_count, 0) > 0
        THEN 'FACILITY-WIDE ISSUE'
        WHEN (COALESCE(d.delice_alarm_count, 0) > 0 AND COALESCE(f.fesa_alarm_count, 0) > 0) OR
             (COALESCE(f.fesa_alarm_count, 0) > 0 AND COALESCE(s.shovel_alarm_count, 0) > 0) OR
             (COALESCE(d.delice_alarm_count, 0) > 0 AND COALESCE(s.shovel_alarm_count, 0) > 0)
        THEN 'CORRELATED ALARMS'
        ELSE 'ISOLATED ALARM'
    END as correlation_status

FROM delice_alarms d
FULL OUTER JOIN fesa_alarms f ON d.time_bucket = f.time_bucket
FULL OUTER JOIN shovel_alarms s ON d.time_bucket = s.time_bucket
WHERE COALESCE(d.delice_alarm_count, 0) > 0 OR
      COALESCE(f.fesa_alarm_count, 0) > 0 OR
      COALESCE(s.shovel_alarm_count, 0) > 0
ORDER BY time_bucket DESC
```

**Use Case:** Detects power outages, network issues, environmental factors

---

# PART 4: RAW vs PROCESSED DATA ANALYSIS

## Query 13: Data Quality Comparison - Raw Timestream vs Processed S3

**Business Question:** "Compare data completeness and quality between raw real-time data and processed historical data lake"

**Use Case:** Data pipeline validation, ETL monitoring

**SQL Query (Timestream):**
```sql
-- Raw Data Quality - Last 24h
SELECT
    'TIMESTREAM_RAW' as data_source,
    COUNT(*) as total_records,
    COUNT(DISTINCT device_ID) as unique_devices,

    -- Completeness metrics
    ROUND(COUNT(temp_process_1) * 100.0 / COUNT(*), 2) as temp_completeness_pct,
    ROUND(COUNT(water_flow_lph) * 100.0 / COUNT(*), 2) as flow_completeness_pct,
    ROUND(COUNT(mqtt_topic) * 100.0 / COUNT(*), 2) as topic_completeness_pct,

    -- Data freshness
    MAX(time) as latest_record,
    date_diff('second', MAX(time), current_time) as seconds_since_last_update,

    -- Anomaly detection
    SUM(CASE WHEN temp_process_1 IS NULL THEN 1 ELSE 0 END) as missing_temp_records,
    SUM(CASE WHEN temp_process_1 < 0 OR temp_process_1 > 150 THEN 1 ELSE 0 END) as out_of_range_temps

FROM "E2iDB"."DeliceTableTimestream"
WHERE time > ago(24h)
```

**SQL Query (Athena):**
```sql
-- Processed Data Quality - Last 24h
SELECT
    'S3_PROCESSED' as data_source,
    COUNT(*) as total_records,
    COUNT(DISTINCT device_id) as unique_devices,

    -- Completeness metrics
    ROUND(CAST(COUNT(temp_process_1) AS DOUBLE) * 100.0 / COUNT(*), 2) as temp_completeness_pct,
    ROUND(CAST(COUNT(water_flow_lph) AS DOUBLE) * 100.0 / COUNT(*), 2) as flow_completeness_pct,
    ROUND(CAST(COUNT(mqtt_topic) AS DOUBLE) * 100.0 / COUNT(*), 2) as topic_completeness_pct,

    -- Data freshness
    MAX(from_unixtime(timestamp)) as latest_record,
    date_diff('second', MAX(from_unixtime(timestamp)), CURRENT_TIMESTAMP) as seconds_since_last_update,

    -- Anomaly detection
    SUM(CASE WHEN temp_process_1 IS NULL THEN 1 ELSE 0 END) as missing_temp_records,
    SUM(CASE WHEN temp_process_1 < 0 OR temp_process_1 > 150 THEN 1 ELSE 0 END) as out_of_range_temps

FROM delice_db_v1.delice_table_v1
WHERE from_unixtime(timestamp) >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
```

**Expected Result:** Both should show >99% completeness; identify data loss in pipeline

---

## Query 14: Aggregate Performance - Raw vs Pre-Aggregated

**Business Question:** "Compare query performance between querying raw data vs pre-aggregated tables for reporting"

**Use Case:** Query optimization, materialized view evaluation

**Option A: Query Raw Data (Slower but flexible)**
```sql
-- Athena on raw Parquet
SELECT
    DATE(from_unixtime(timestamp)) as date,
    device_id,
    COUNT(*) as records,
    AVG(temp_process_1) as avg_temp,
    MAX(temp_process_1) as max_temp,
    MIN(temp_process_1) as min_temp,
    STDDEV(temp_process_1) as temp_stddev,
    SUM(water_flow_lph) / 60.0 as total_liters
FROM delice_db_v1.delice_table_v1
WHERE from_unixtime(timestamp) >= DATE '2026-01-01'
GROUP BY DATE(from_unixtime(timestamp)), device_id
ORDER BY date DESC, device_id
```

**Option B: Create Pre-Aggregated Table (Recommended for frequent queries)**
```sql
-- CTAS (Create Table As Select) - Run once per day
CREATE TABLE delice_db_v1.delice_daily_summary
WITH (
    format = 'PARQUET',
    external_location = 's3://delice-datalake-parquet/aggregated/daily/',
    partitioned_by = ARRAY['year', 'month']
) AS
SELECT
    YEAR(from_unixtime(timestamp)) as year,
    MONTH(from_unixtime(timestamp)) as month,
    DATE(from_unixtime(timestamp)) as date,
    device_id,

    -- Pre-calculated metrics
    COUNT(*) as record_count,
    AVG(temp_process_1) as avg_temp,
    MAX(temp_process_1) as max_temp,
    MIN(temp_process_1) as min_temp,
    STDDEV(temp_process_1) as temp_stddev,
    SUM(water_flow_lph) / 60.0 as total_water_liters,
    SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as alarm_count,
    SUM(CASE WHEN cleaning_mode = 1 THEN 1 ELSE 0 END) as cleaning_hours

FROM delice_db_v1.delice_table_v1
GROUP BY
    YEAR(from_unixtime(timestamp)),
    MONTH(from_unixtime(timestamp)),
    DATE(from_unixtime(timestamp)),
    device_id
```

**Then query aggregated table (10-100x faster):**
```sql
SELECT * FROM delice_db_v1.delice_daily_summary
WHERE year = 2026 AND month = 3
ORDER BY date DESC
```

**Performance Gain:** Aggregated queries are 10-100x faster for large datasets

---

## Query 15: End-to-End Data Pipeline Validation

**Business Question:** "Validate data consistency across the entire pipeline from device to data lake"

**Use Case:** Data governance, audit trail, pipeline health check

**Step 1: Check Raw Timestream Data**
```sql
-- Timestream: Raw ingestion from devices
SELECT
    'STEP_1_DEVICE_TO_TIMESTREAM' as pipeline_stage,
    DATE(time) as date,
    COUNT(*) as record_count,
    COUNT(DISTINCT device_ID) as device_count,
    MIN(time) as earliest_record,
    MAX(time) as latest_record
FROM "E2iDB"."DeliceTableTimestream"
WHERE time >= current_date - INTERVAL '7' DAY
GROUP BY DATE(time)
ORDER BY date DESC
```

**Step 2: Check Firehose S3 Landing (Raw JSON)**
```bash
# Check S3 raw landing zone (if enabled)
aws s3 ls s3://delice-datalake-raw/2026/03/ --recursive --human-readable --summarize
```

**Step 3: Check Processed Parquet Data Lake**
```sql
-- Athena: Processed data in S3 Data Lake
SELECT
    'STEP_3_PROCESSED_DATA_LAKE' as pipeline_stage,
    DATE(from_unixtime(timestamp)) as date,
    COUNT(*) as record_count,
    COUNT(DISTINCT device_id) as device_count,
    MIN(from_unixtime(timestamp)) as earliest_record,
    MAX(from_unixtime(timestamp)) as latest_record,

    -- File metadata
    COUNT(DISTINCT "$path") as parquet_file_count

FROM delice_db_v1.delice_table_v1
WHERE from_unixtime(timestamp) >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY DATE(from_unixtime(timestamp))
ORDER BY date DESC
```

**Step 4: Compare Record Counts (Data Loss Detection)**
```sql
-- Expected: Timestream records ≈ S3 records (within 1-2%)
WITH timestream_counts AS (
    SELECT DATE(time) as date, COUNT(*) as ts_count
    FROM "E2iDB"."DeliceTableTimestream"
    WHERE time >= current_date - INTERVAL '7' DAY
    GROUP BY DATE(time)
),
s3_counts AS (
    SELECT DATE(from_unixtime(timestamp)) as date, COUNT(*) as s3_count
    FROM delice_db_v1.delice_table_v1
    WHERE from_unixtime(timestamp) >= CURRENT_DATE - INTERVAL '7' DAY
    GROUP BY DATE(from_unixtime(timestamp))
)
SELECT
    COALESCE(ts.date, s3.date) as date,
    COALESCE(ts.ts_count, 0) as timestream_records,
    COALESCE(s3.s3_count, 0) as s3_datalake_records,
    COALESCE(ts.ts_count, 0) - COALESCE(s3.s3_count, 0) as record_difference,
    ROUND(
        ABS(COALESCE(ts.ts_count, 0) - COALESCE(s3.s3_count, 0)) * 100.0 /
        NULLIF(COALESCE(ts.ts_count, 1), 0),
        2
    ) as difference_percentage,

    CASE
        WHEN ABS(COALESCE(ts.ts_count, 0) - COALESCE(s3.s3_count, 0)) * 100.0 /
             NULLIF(COALESCE(ts.ts_count, 1), 0) < 2.0
        THEN 'HEALTHY - <2% difference'
        WHEN ABS(COALESCE(ts.ts_count, 0) - COALESCE(s3.s3_count, 0)) * 100.0 /
             NULLIF(COALESCE(ts.ts_count, 1), 0) < 5.0
        THEN 'WARNING - 2-5% data loss'
        ELSE 'CRITICAL - >5% data loss'
    END as pipeline_health

FROM timestream_counts ts
FULL OUTER JOIN s3_counts s3 ON ts.date = s3.date
ORDER BY date DESC
```

**SLA:** Data loss should be <1% for production pipelines

---

# APPENDIX: Query Performance Tips

## Timestream Optimization

1. **Use time filters aggressively** - Always filter with `WHERE time > ago(Xh)`
2. **Bin aggregations** - Use `bin(time, 5m)` for time-series grouping
3. **Limit results** - Add `LIMIT` clause for exploratory queries
4. **Measure filter** - Filter on specific measures early in query

## Athena/S3 Optimization

1. **Partition pruning** - Always filter on partition columns (date/hour)
2. **Use Parquet** - Columnar format reduces scan by 80-90%
3. **CTAS for aggregations** - Pre-aggregate frequently queried data
4. **Limit projections** - Only SELECT columns you need
5. **Avoid wildcards** - Specify explicit column names

---

# Summary

This document provides **15 production-ready SQL queries** covering:

✅ **Real-time monitoring** (Timestream) - Queries 1-5
✅ **Historical analysis** (Athena) - Queries 6-10
✅ **Cross-device insights** - Queries 11-12
✅ **Data quality validation** - Queries 13-15

**Industries Covered:**
- Food & Beverage (Pasteurization)
- Mining & Excavation
- Heavy Equipment Manufacturing
- General Industrial IoT

**Compliance Standards:**
- FDA Food Safety Modernization Act (FSMA)
- HACCP Critical Control Points
- ISO 22000 Food Safety Management
- Mining safety regulations

---

**Document Version:** 1.0
**Last Updated:** March 4, 2026
**Author:** E2i Data Analytics Team
**For:** Multi-industry IoT operations monitoring
