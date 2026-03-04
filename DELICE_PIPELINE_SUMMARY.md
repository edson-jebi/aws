# Delice Data Lake Pipeline - Complete Configuration Summary

**Date:** March 4, 2026
**Device:** Delice Pasteurization Equipment
**Region:** us-west-2
**Account:** 760135066147

---

## Overview

This document summarizes the complete AWS IoT to Data Lake pipeline for the Delice pasteurization device. Data flows from the device through IoT Core, Kinesis Firehose, and is stored as Parquet files in S3, queryable via Athena.

---

## Architecture Components

```
Delice Device → IoT Core → Kinesis Firehose → S3 (Parquet) → Athena
                    ↓
                Timestream (parallel)
```

---

## 1. IoT Core Configuration

### **Topic Format**
- **Device publishes to:** `/E2i/Delice_topic` (with leading slash)

### **IoT Rule: `delice_rule_test`**

**SQL Statement:**
```sql
SELECT * FROM '#'
```
*Note: The `#` wildcard is required to match topics with leading slashes*

**Actions:**
1. **Timestream Action:**
   - Database: `E2iDB`
   - Table: `DeliceTableTimestream`
   - Role: `arn:aws:iam::760135066147:role/iot-timestream-rol`

2. **Firehose Action:**
   - Stream: `FIREHOSE_DELICE_V1`
   - Role: `arn:aws:iam::760135066147:role/service-role/iot-firehose-delice-role`
   - Batch Mode: Enabled

**Error Action:**
- Republish to: `/E2i/Delice_topic/error`
- Role: `arn:aws:iam::760135066147:role/service-role/e2i_iot_timestream`

---

## 2. IAM Roles and Permissions

### **Role 1: `iot-firehose-delice-role`**
*Allows IoT Rule to send data to Firehose*

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "iot.amazonaws.com",
          "firehose.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Permissions:**
- `firehose:PutRecord` on `FIREHOSE_DELICE_V1`
- `firehose:PutRecordBatch` on `FIREHOSE_DELICE_V1`

---

### **Role 2: `KinesisFirehoseServiceRole-DELICE-us-west-2-1709915890`**
*Allows Firehose to read Glue schema, convert data, and write to S3*

**Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "firehose.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Permissions:**

1. **Glue Access:**
   - `glue:GetTable`, `glue:GetTableVersion`, `glue:GetTableVersions`, `glue:GetDatabase`
   - Resources: `delice_db_v1` database and `delice_table_v1` table

2. **S3 Access:**
   - `s3:PutObject`, `s3:GetObject`, `s3:ListBucket`, `s3:AbortMultipartUpload`, etc.
   - Bucket: `delice-datalake-parquet`

3. **CloudWatch Logs:**
   - `logs:PutLogEvents`, `logs:CreateLogStream`, `logs:CreateLogGroup`
   - Log group: `/aws/kinesisfirehose/FIREHOSE_DELICE_V1`

---

## 3. Kinesis Firehose Configuration

### **Delivery Stream: `FIREHOSE_DELICE_V1`**

**Source:** Direct PUT (from IoT Rule)

**Destination:** Amazon S3

**S3 Configuration:**
- **Bucket:** `s3://delice-datalake-parquet/`
- **Prefix:** Dynamic partitioning by date: `YYYY/MM/DD/HH/`
- **Compression:** Snappy (via Parquet)

**Data Format Conversion:**
- **Enabled:** Yes
- **Input Format:** JSON
- **Output Format:** Apache Parquet
- **Glue Database:** `delice_db_v1`
- **Glue Table:** `delice_table_v1`
- **Schema Version:** LATEST

**Buffer Configuration:**
- **Buffer Size:** 128 MB (or default)
- **Buffer Interval:** 300 seconds (5 minutes)
- *Data appears in S3 after buffer conditions are met*

**Role:** `KinesisFirehoseServiceRole-DELICE-us-west-2-1709915890`

---

## 4. AWS Glue Configuration

### **Database: `delice_db_v1`**
- **Type:** External
- **Location:** `s3://delice-datalake-parquet/`

### **Table: `delice_table_v1`**

**Storage:**
- **Format:** Parquet
- **Compression:** Snappy
- **Location:** `s3://delice-datalake-parquet/`
- **Classification:** parquet

**Schema (30 columns):**

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `device_id` | string | Device identifier |
| `timestamp` | bigint | Unix timestamp (seconds) |
| `temp_process_1` | double | Process temperature sensor 1 (°C) |
| `temp_process_2` | double | Process temperature sensor 2 (°C) |
| `temp_process_3` | double | Process temperature sensor 3 (°C) |
| `temp_water_1` | double | Water temperature sensor 1 (°C) |
| `temp_water_2` | double | Water temperature sensor 2 (°C) |
| `heating_set_point` | double | Target heating temperature (°C) |
| `cooling_set_point` | double | Target cooling temperature (°C) |
| `water_temp_set_point` | double | Target water temperature (°C) |
| `grid_valve_opening` | double | Grid valve position (%) |
| `steam_valve_opening` | double | Steam valve position (%) |
| `pump_frequency` | double | Pump frequency (Hz) |
| `product_pump_state` | int | Product pump status (0=off, 1=on) |
| `water_pump_state` | int | Water pump status (0=off, 1=on) |
| `product_state` | int | Product processing state |
| `status_main` | int | Main system status |
| `status_product` | int | Product status |
| `water_flow_lph` | double | Water flow rate (liters/hour) |
| `tank_level` | double | Tank level (%) |
| `tank_return` | double | Tank return level (%) |
| `detergent_concentration` | double | Detergent concentration (%) |
| `cleaning_mode` | int | Cleaning mode status |
| `heating_mode` | int | Heating mode status |
| `cooling_mode` | int | Cooling mode status |
| `water_mode` | int | Water circulation mode |
| `alarm_active` | int | Alarm status (0=no alarm, 1=alarm) |
| `emergency_stop` | int | Emergency stop (0=normal, 1=stopped) |
| `mqtt_topic` | string | MQTT topic path |
| `ingestion_time` | timestamp | Data ingestion timestamp |

---

## 5. S3 Storage

### **Bucket: `delice-datalake-parquet`**

**Structure:**
```
s3://delice-datalake-parquet/
├── 2026/
│   ├── 03/
│   │   ├── 04/
│   │   │   ├── 16/
│   │   │   │   ├── FIREHOSE_DELICE_V1-1-2026-03-04-16-20-00-xxxxx.parquet
│   │   │   │   └── FIREHOSE_DELICE_V1-1-2026-03-04-16-25-00-xxxxx.parquet
│   │   │   └── 17/
│   │   │       └── ...
│   │   └── 05/
│   └── 04/
```

**File Format:** Apache Parquet with Snappy compression
**Partitioning:** Automatic by year/month/day/hour

---

## 6. Data Flow Summary

1. **Device** publishes JSON data to `/E2i/Delice_topic`
2. **IoT Rule** (`delice_rule_test`) matches with SQL `SELECT * FROM '#'`
3. **Parallel Actions:**
   - Timestream: Real-time time-series database
   - Firehose: Data lake pipeline
4. **Firehose** buffers data (up to 5 minutes or 128 MB)
5. **Format Conversion:** JSON → Parquet using Glue schema
6. **S3 Storage:** Parquet files written to partitioned structure
7. **Athena Ready:** Data queryable via SQL

---

## 7. Troubleshooting Guide

### **No Data in S3?**

**Check 1: IoT Rule Metrics**
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/IoT \
  --metric-name RuleMessageMatched \
  --dimensions Name=RuleName,Value=delice_rule_test \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 --statistics Sum \
  --region us-west-2 --profile E2i-dairel-760135066147
```

**Check 2: Firehose Metrics**
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name IncomingRecords \
  --dimensions Name=DeliveryStreamName,Value=FIREHOSE_DELICE_V1 \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 --statistics Sum \
  --region us-west-2 --profile E2i-dairel-760135066147
```

**Check 3: S3 Contents**
```bash
aws s3 ls s3://delice-datalake-parquet/ \
  --profile E2i-dairel-760135066147 \
  --recursive --human-readable
```

### **Common Issues**

| Issue | Cause | Solution |
|-------|-------|----------|
| Rule not matching | SQL doesn't match topic with `/` | Use `SELECT * FROM '#'` |
| IAM permission denied | Missing trust or permissions | Verify IAM roles (see section 2) |
| Glue table not found | Table doesn't exist | Create table with 30 columns |
| S3 empty after 10+ min | Firehose buffering or errors | Check CloudWatch logs |

---

## 8. Verification Checklist

✅ **IoT Core:**
- [ ] Device publishing to `/E2i/Delice_topic`
- [ ] Rule SQL: `SELECT * FROM '#'`
- [ ] Rule enabled (not disabled)

✅ **IAM:**
- [ ] `iot-firehose-delice-role` trusts IoT and Firehose
- [ ] `iot-firehose-delice-role` can PutRecord to Firehose
- [ ] Firehose service role can read Glue and write to S3

✅ **Glue:**
- [ ] Database `delice_db_v1` exists
- [ ] Table `delice_table_v1` exists with 30 columns
- [ ] Table format is Parquet

✅ **Firehose:**
- [ ] Stream status: ACTIVE
- [ ] Format conversion enabled with Glue table
- [ ] Destination bucket: `delice-datalake-parquet`

✅ **S3:**
- [ ] Bucket exists and is accessible
- [ ] After 5+ minutes, Parquet files appear

---

## 9. Monitoring

### **CloudWatch Metrics to Monitor**

1. **IoT Core:**
   - `RuleMessageMatched` - Messages matched by rule
   - `RuleNotFound` - Rule configuration errors

2. **Firehose:**
   - `IncomingRecords` - Records received
   - `DeliveryToS3.Success` - Successful S3 writes
   - `DeliveryToS3.DataFreshness` - Age of oldest record

3. **S3:**
   - Object count and size growth

### **CloudWatch Logs**

- **Firehose Logs:** `/aws/kinesisfirehose/FIREHOSE_DELICE_V1`
  - DestinationDelivery stream
  - BackupDelivery stream (if enabled)

---

## 10. Key Configuration Values

| Component | Name/Value |
|-----------|------------|
| **Region** | us-west-2 |
| **Account** | 760135066147 |
| **Device Topic** | `/E2i/Delice_topic` |
| **IoT Rule** | `delice_rule_test` |
| **Firehose Stream** | `FIREHOSE_DELICE_V1` |
| **S3 Bucket** | `delice-datalake-parquet` |
| **Glue Database** | `delice_db_v1` |
| **Glue Table** | `delice_table_v1` |
| **IoT Role** | `iot-firehose-delice-role` |
| **Firehose Role** | `KinesisFirehoseServiceRole-DELICE-us-west-2-1709915890` |

---

## Next Steps

1. **Verify Data Flow:** Wait 5-10 minutes after device starts publishing, then check S3
2. **Set Up Athena:** See companion document for Athena queries
3. **Create Dashboards:** Use QuickSight or Grafana for visualization
4. **Set Alerts:** Configure CloudWatch alarms for system health
5. **Optimize Costs:** Implement S3 lifecycle policies for old data

---

**Document Version:** 1.0
**Last Updated:** March 4, 2026
**Maintained By:** E2i Team
