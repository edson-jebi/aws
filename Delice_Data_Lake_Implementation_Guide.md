# Complete Manual Guide: Delice Data Lake Pipeline with AWS IoT Integration

**Document Version:** 1.0
**Last Updated:** March 2, 2024
**AWS Account:** 760135066147
**Region:** us-west-2

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current State Analysis](#current-state-analysis)
3. [Target Architecture](#target-architecture)
4. [Implementation Guide](#implementation-guide)
   - [Step 1: Create AWS Glue Database](#step-1-create-aws-glue-database)
   - [Step 2: Create AWS Glue Table Schema](#step-2-create-aws-glue-table-schema)
   - [Step 3: Create S3 Bucket](#step-3-create-s3-bucket)
   - [Step 4: Create IAM Role for Firehose](#step-4-create-iam-role-for-firehose)
   - [Step 5: Create Kinesis Data Firehose Delivery Stream](#step-5-create-kinesis-data-firehose-delivery-stream)
   - [Step 6: Add Firehose Action to IoT Rule](#step-6-add-firehose-action-to-iot-rule)
   - [Step 7: Testing the Pipeline](#step-7-testing-the-pipeline)
   - [Step 8: Query Data with Amazon Athena](#step-8-query-data-with-amazon-athena)
5. [Architecture Comparison](#architecture-comparison)
6. [Configuration Checklist](#configuration-checklist)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Cost Estimation](#cost-estimation)
9. [Troubleshooting Guide](#troubleshooting-guide)
10. [Next Steps](#next-steps)

---

## Executive Summary

This guide will help you create a complete data lake pipeline for the **Delice device**, integrating the existing AWS IoT rule (`delice_rule_test`) with Amazon Kinesis Data Firehose to automatically convert JSON data to Parquet format and store it in S3 for analytics.

### What You'll Build

- **Data Lake Storage**: Long-term Parquet storage in S3
- **Format Conversion**: Automatic JSON to Parquet conversion
- **Dual Architecture**: Maintains existing Timestream + adds S3 data lake
- **Analytics Ready**: Query historical data with Amazon Athena
- **Cost Optimized**: 90% query cost reduction vs JSON storage

---

## Current State Analysis

### Existing Infrastructure

✅ **AWS IoT Rule**: `delice_rule_test`
- **Topic**: `/E2i/Delice_topic`
- **SQL**: `SELECT * FROM '/E2i/Delice_topic'`
- **Current Action**: Writes to Timestream (`E2iDB.DeliceTableTimestream`)
- **Status**: Active
- **Region**: us-west-2

✅ **Timestream Table**: `DeliceTableTimestream`
- **Database**: E2iDB
- **Retention**: 7 days (memory) / 360 days (magnetic)
- **Status**: Active
- **Data**: Industrial process control data (28 metrics)

### Delice Device Data Structure

**Device Type**: Industrial food processing equipment (pasteurization/heating system)

**Sample Metrics** (28 total measurements):

| Category | Metrics |
|----------|---------|
| **Temperature** | `temp_process_1`, `temp_process_2`, `temp_process_3`, `temp_water_1`, `temp_water_2` |
| **Control Setpoints** | `heating_set_point`, `cooling_set_point`, `water_temp_set_point`, `tank_level_set_point` |
| **Valves** | `grid_valve_opening`, `steam_valve_opening` |
| **Pumps** | `pump_frequency`, `product_pump_state`, `water_pump_state`, `product_pump_mode`, `water_pump_mode` |
| **System Status** | `product_state`, `status_main`, `status_product` |
| **Flow & Tank** | `water_flow_lph`, `tank_level`, `tank_return` |
| **Other** | `detergent_concentration`, `heater_mode_or_thermistor`, `termizing_or_heating` |

**Sample Data Format**:
```json
{
  "device_ID": "Andino_X1_P01",
  "timestamp": 1709915890,
  "temp_process_1": 65.5,
  "temp_process_2": 68.2,
  "temp_process_3": 58.9,
  "pump_frequency": 35.37,
  "product_state": 0,
  "heating_set_point": 74.5,
  "tank_level": 82.5,
  "water_flow_lph": 1500.0
}
```

---

## Target Architecture

```
IoT Devices (Delice)
        ↓
  MQTT Topic: /E2i/Delice_topic
        ↓
AWS IoT Rule: delice_rule_test
        ├─→ [Existing] Timestream (E2iDB.DeliceTableTimestream)
        └─→ [NEW] Kinesis Firehose (FIREHOSE_DELICE_V1)
                   ↓
              [Format Conversion: JSON → Parquet]
                   ↓
              S3: delice-datalake-parquet
                   ↓
              AWS Glue Catalog (delice_db_v1)
                   ↓
              Amazon Athena (SQL Analytics)
```

### Key Components

| Component | Name | Purpose |
|-----------|------|---------|
| **Glue Database** | `delice_db_v1` | Schema catalog |
| **Glue Table** | `delice_table_v1` | Column definitions (30 columns) |
| **S3 Bucket** | `delice-datalake-parquet` | Parquet file storage |
| **Firehose Stream** | `FIREHOSE_DELICE_V1` | JSON→Parquet converter |
| **IAM Role** | `KinesisFirehoseServiceRole-DELICE-*` | Permissions |

---

## Implementation Guide

---

## STEP 1: Create AWS Glue Database

### 1.1 Open AWS Glue Console

1. Open AWS Console → Search **"Glue"**
2. Click **"AWS Glue"** service
3. In left sidebar, click **"Databases"** under Data Catalog
4. Click **"Add database"** button

### 1.2 Database Configuration

| Field | Value |
|-------|-------|
| **Database name** | `delice_db_v1` |
| **Description** | `Data lake for Delice industrial process control telemetry` |
| **Location** | (leave empty) |

**Action**: Click **"Create database"**

---

## STEP 2: Create AWS Glue Table Schema

### 2.1 Navigate to Tables

1. AWS Glue Console → **"Tables"** (left sidebar)
2. Click **"Add table"** button
3. Select **"Add table manually"**

### 2.2 Table Properties

| Field | Value |
|-------|-------|
| **Table name** | `delice_table_v1` |
| **Database** | `delice_db_v1` |
| **Description** | `Delice pasteurization and heating system telemetry data` |

### 2.3 Data Store Configuration

**Important:** When creating the Glue table, you'll see options for data source configuration.

#### Select Data Source Type

| Field | Value | Notes |
|-------|-------|-------|
| **Data store type** | S3 | Select S3 as the source |
| **Data location** | **Leave empty** or enter: `s3://delice-datalake-parquet/` | ⭐ **Can be empty** - Firehose will write here |
| **Account** | My account | Data is in your AWS account |

**Why leave it empty?**
- The Glue table is just defining the schema (column structure)
- Firehose will automatically write Parquet files to your S3 bucket
- The table doesn't need to point to existing data yet
- If AWS requires a path, use: `s3://delice-datalake-parquet/`

#### Data Format

| Field | Value | Notes |
|-------|-------|-------|
| **Classification** | `parquet` | **CRITICAL - Must be Parquet** |
| **Format** | `Parquet` | Must match Firehose output format |

### 2.4 Complete Schema Definition

**Add all 30 columns in this order:**

| # | Column Name | Data Type | Comment |
|---|------------|-----------|---------|
| 1 | `device_id` | `string` | Device identifier (e.g., Andino_X1_P01) |
| 2 | `timestamp` | `bigint` | Unix timestamp in seconds |
| 3 | `temp_process_1` | `double` | Process temperature sensor 1 (°C) |
| 4 | `temp_process_2` | `double` | Process temperature sensor 2 (°C) |
| 5 | `temp_process_3` | `double` | Process temperature sensor 3 (°C) |
| 6 | `temp_water_1` | `double` | Water temperature sensor 1 (°C) |
| 7 | `temp_water_2` | `double` | Water temperature sensor 2 (°C) |
| 8 | `heating_set_point` | `double` | Heating setpoint (°C) |
| 9 | `cooling_set_point` | `double` | Cooling setpoint (°C) |
| 10 | `water_temp_set_point` | `double` | Water temperature setpoint (°C) |
| 11 | `tank_level_set_point` | `double` | Tank level setpoint (%) |
| 12 | `grid_valve_opening` | `double` | Grid valve opening percentage (%) |
| 13 | `steam_valve_opening` | `double` | Steam valve opening percentage (%) |
| 14 | `pump_frequency` | `double` | Pump frequency (Hz) |
| 15 | `product_pump_state` | `bigint` | Product pump state (0=off, 1=on) |
| 16 | `product_pump_mode` | `bigint` | Product pump operating mode |
| 17 | `water_pump_state` | `bigint` | Water pump state (0=off, 1=on) |
| 18 | `water_pump_mode` | `bigint` | Water pump operating mode |
| 19 | `product_state` | `bigint` | Product state indicator |
| 20 | `status_main` | `bigint` | Main system status |
| 21 | `status_product` | `bigint` | Product system status |
| 22 | `tank_level` | `double` | Current tank level (%) |
| 23 | `tank_return` | `double` | Tank return value |
| 24 | `water_flow_lph` | `double` | Water flow rate (liters per hour) |
| 25 | `detergent_concentration` | `double` | Detergent concentration (%) |
| 26 | `heater_mode_or_thermistor` | `bigint` | Heater mode or thermistor status |
| 27 | `termizing_or_heating` | `bigint` | Termizing or heating mode |
| 28 | `entering_holding_or_sending_tanks` | `bigint` | Tank entry/exit status |
| 29 | `machine` | `string` | Machine identifier (optional) |
| 30 | `event_time` | `string` | ISO 8601 timestamp string (optional) |

### 2.5 Data Type Mapping Guide

| JSON Type | Glue Type | Examples |
|-----------|-----------|----------|
| Text/IDs | `string` | device_id, machine |
| Whole numbers | `bigint` | states, modes (0/1) |
| Decimals | `double` | temperatures, frequencies |
| Unix timestamp | `bigint` | timestamp (seconds since epoch) |
| ISO timestamp | `string` | event_time ("2024-03-02T22:38:10Z") |

**Action**: Click **"Create table"**

---

## STEP 3: Create S3 Bucket

### 3.1 Navigate to S3 Console

1. AWS Console → Search **"S3"**
2. Click **"Create bucket"**

### 3.2 Bucket Configuration

| Field | Value | Notes |
|-------|-------|-------|
| **Bucket name** | `delice-datalake-parquet` | Must be globally unique |
| **Region** | `us-west-2` | **CRITICAL: Must match Firehose** |
| **Block Public Access** | ✅ All blocked | Keep data private |
| **Bucket Versioning** | Disabled | Optional |
| **Default encryption** | SSE-S3 | **Recommended for production** |
| **Object Lock** | Disabled | Not needed |

**Action**: Click **"Create bucket"**

### 3.3 Expected Directory Structure

After pipeline activation:
```
s3://delice-datalake-parquet/
├── 2024/03/02/23/                      # YYYY/MM/DD/HH
│   ├── FIREHOSE_DELICE_V1-1-2024-03-02-23-05-00-{UUID}.parquet
│   ├── FIREHOSE_DELICE_V1-1-2024-03-02-23-10-00-{UUID}.parquet
│   └── ...
├── format-conversion-failed/           # Failed conversions
└── scheduled-processing/               # (if applicable)
```

---

## STEP 4: Create IAM Role for Firehose

### 4.1 Create Role

1. AWS Console → **"IAM"** → **"Roles"**
2. Click **"Create role"**

3. **Select trusted entity**:
   - **Trusted entity type**: AWS service
   - Text appears: "Allow an AWS service like EC2, Lambda, or others to perform actions in this account"

4. **Service or use case**:
   - In the search box or dropdown, find and select: **"Kinesis"**

⚠️ **Important Note**: Depending on your AWS Console version, you may see different options:

**Option A: If you see "Kinesis Firehose" in the list**
   - Select **"Kinesis Firehose"** from the options
   - Description shows: "Allows Kinesis Firehose to call AWS services on your behalf"
   - Click **"Next"**

**Option B: If you only see "Kinesis Analytics - SQL"**
   - Select **"Kinesis Analytics - SQL"**
   - Click **"Next"**
   - **Continue to Step 4.2** - We will manually fix the trust policy in Step 4.4

### 4.2 Role Details

| Field | Value |
|-------|-------|
| **Role name** | `KinesisFirehoseServiceRole-DELICE-us-west-2-1709915890` |
| **Description** | `Allows Firehose to write Delice data to S3 and read Glue schema` |

**Action**: Click **"Create role"** (skip policy attachment for now)

### 4.3 Attach Inline Policy

1. Find your newly created role in the list
2. Click on the role name
3. Click **"Add permissions"** → **"Create inline policy"**
4. Switch to **JSON** tab
5. Paste the following policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "GlueSchemaAccess",
            "Effect": "Allow",
            "Action": [
                "glue:GetTable",
                "glue:GetTableVersion",
                "glue:GetTableVersions",
                "glue:GetDatabase"
            ],
            "Resource": [
                "arn:aws:glue:us-west-2:760135066147:catalog",
                "arn:aws:glue:us-west-2:760135066147:database/delice_db_v1",
                "arn:aws:glue:us-west-2:760135066147:table/delice_db_v1/delice_table_v1"
            ]
        },
        {
            "Sid": "S3WriteAccess",
            "Effect": "Allow",
            "Action": [
                "s3:AbortMultipartUpload",
                "s3:GetBucketLocation",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:ListBucketMultipartUploads",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::delice-datalake-parquet",
                "arn:aws:s3:::delice-datalake-parquet/*"
            ]
        },
        {
            "Sid": "CloudWatchLogsAccess",
            "Effect": "Allow",
            "Action": [
                "logs:PutLogEvents",
                "logs:CreateLogStream",
                "logs:CreateLogGroup"
            ],
            "Resource": [
                "arn:aws:logs:us-west-2:760135066147:log-group:/aws/kinesisfirehose/FIREHOSE_DELICE_V1:*"
            ]
        }
    ]
}
```

6. **Policy name**: `KinesisFirehoseServicePolicy-DELICE-us-west-2`
7. Click **"Create policy"**

### 4.4 Fix Trust Policy (Only if you selected "Kinesis Analytics - SQL" in Step 4.1)

⚠️ **Skip this step if you selected "Kinesis Firehose" in Step 4.1 - your trust policy is already correct**

If you created the role using "Kinesis Analytics - SQL", you need to manually update the trust policy:

1. In the IAM Console, find your role: `KinesisFirehoseServiceRole-DELICE-us-west-2-1709915890`
2. Click on the role name
3. Click **"Trust relationships"** tab
4. Click **"Edit trust policy"**
5. Replace the entire JSON with:

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

6. Click **"Update policy"**

**What this does**: Changes the trusted service from `kinesisanalytics.amazonaws.com` to `firehose.amazonaws.com`, allowing Kinesis Firehose to assume this role.

---

## STEP 5: Create Kinesis Data Firehose Delivery Stream

### 5.1 Open Kinesis Console

1. AWS Console → Search **"Kinesis"**
2. Click **"Kinesis Data Firehose"**
3. Click **"Create delivery stream"**

### 5.2 Source and Destination

| Field | Value | Notes |
|-------|-------|-------|
| **Source** | Direct PUT | For IoT rule integration |
| **Destination** | Amazon S3 | Data lake storage |

Click **"Next"**

### 5.3 Delivery Stream Name

| Field | Value |
|-------|-------|
| **Delivery stream name** | `FIREHOSE_DELICE_V1` |

### 5.4 Transform and Convert Records ⭐ CRITICAL SECTION

#### Data Transformation
| Field | Value |
|-------|-------|
| **Data transformation** | ❌ Disabled |

#### Record Format Conversion ⭐ MUST ENABLE
| Field | Value |
|-------|-------|
| **Record format conversion** | ✅ **ENABLED** |
| **Output format** | `Apache Parquet` |

**AWS Glue table for schema:**
- **Region**: `us-west-2`
- **Database**: `delice_db_v1`
- **Table**: `delice_table_v1`
- **Table version**: `Latest`

**Input format:**
- **Format**: `JSON`
- **Deserializer**: `OpenX JSON SerDe library`
- Leave all OpenX JSON SerDe options as default

**Parquet SerDe options:**
- Leave all as default (automatic Snappy compression)

### 5.5 Destination Settings

#### S3 Bucket Configuration

| Field | Value | Notes |
|-------|-------|-------|
| **S3 bucket** | `s3://delice-datalake-parquet` | Select from dropdown |
| **S3 bucket prefix** | (empty) | Leave blank for root |
| **S3 bucket error output prefix** | `format-conversion-failed/` | For failed records |
| **Dynamic partitioning** | Disabled | Use automatic time partitioning |

#### S3 Buffer Conditions ⭐ MATCH REY SETUP

| Field | Value | Notes |
|-------|-------|-------|
| **Buffer size** | `128` MB | Triggers when 128MB accumulated |
| **Buffer interval** | `300` seconds | Triggers after 5 minutes |

**Behavior**: S3 write occurs when **EITHER** condition is met first.

#### S3 Compression and Encryption

| Field | Value | Notes |
|-------|-------|-------|
| **Compression** | Disabled | Parquet has built-in Snappy |
| **Encryption** | SSE-S3 | **Recommended** - match bucket setting |

### 5.6 Advanced Settings

#### Permissions

| Field | Value |
|-------|-------|
| **IAM role** | Existing role |
| **Existing role** | `KinesisFirehoseServiceRole-DELICE-us-west-2-1709915890` |

#### CloudWatch Logging

| Field | Value |
|-------|-------|
| **Error logging** | ✅ Enabled |
| **CloudWatch log group** | `/aws/kinesisfirehose/FIREHOSE_DELICE_V1` (auto-created) |

#### Tags (Optional but Recommended)

| Key | Value |
|-----|-------|
| `Device` | `Delice` |
| `Environment` | `Production` |
| `DataSource` | `IoT` |
| `Project` | `DataLake` |

### 5.7 Review and Create

1. Review all settings carefully
2. Verify format conversion is **ENABLED**
3. Verify buffer settings: **128 MB / 300 seconds**
4. Click **"Create delivery stream"**
5. Wait for status to change to **"Active"** (~2-5 minutes)

---

## STEP 6: Add Firehose Action to IoT Rule

⭐ **This is the critical integration step**

### 6.1 Open IoT Core Console

1. AWS Console → Search **"IoT Core"**
2. Left sidebar → **"Message routing"** → **"Rules"**
3. Find and click **"delice_rule_test"**

### 6.2 View Current Configuration

You should see:
- **SQL Statement**: `SELECT * FROM '/E2i/Delice_topic'`
- **Current Actions**: 1 action (Timestream)
- **Error Action**: Republish to `/E2i/Delice_topic/error`

### 6.3 Add New Firehose Action

1. Scroll to **"Actions"** section
2. Click **"Add action"** button

### 6.4 Select Action Type

1. In the action list, search for **"Firehose"**
2. Select: **"Send a message to an Amazon Kinesis Data Firehose stream"**
3. Click **"Configure action"**

### 6.5 Configure Firehose Action

| Field | Value | Notes |
|-------|-------|-------|
| **Delivery stream name** | `FIREHOSE_DELICE_V1` | Select from dropdown |
| **Separator** | Leave empty | Each IoT message = 1 record |
| **Batch mode** | ✅ Enabled | **Recommended** for performance |

### 6.6 IAM Role for IoT Rule

**Option 1: Create New Role (Recommended)**
1. Select **"Create a new role"**
2. **Role name**: `iot-firehose-delice-role`
3. AWS will auto-generate policy with `firehose:PutRecord` permission
4. Click **"Create role"**

**Option 2: Use Existing Role**
- Select existing role that has:
  - `firehose:PutRecord`
  - `firehose:PutRecordBatch`

### 6.7 Finalize Action

1. Click **"Add action"**
2. You'll be returned to the rule page

### 6.8 Verify Final Configuration

The `delice_rule_test` rule should now have **2 actions**:

1. ✅ **Timestream**: `E2iDB.DeliceTableTimestream` (existing)
2. ✅ **Kinesis Firehose**: `FIREHOSE_DELICE_V1` (new)

**Error Action**: Republish to `/E2i/Delice_topic/error` (unchanged)

---

## STEP 7: Testing the Pipeline

### 7.1 Send Test Message via IoT MQTT Test Client

1. AWS Console → **IoT Core** → **"MQTT test client"**
2. Click **"Publish to a topic"** tab

**Configuration:**
- **Topic name**: `/E2i/Delice_topic`
- **Quality of Service**: 0

**Test Message Payload:**
```json
{
  "device_ID": "Test_Device_001",
  "timestamp": 1709915890,
  "temp_process_1": 65.5,
  "temp_process_2": 68.2,
  "temp_process_3": 58.9,
  "temp_water_1": 45.0,
  "temp_water_2": 47.3,
  "heating_set_point": 74.5,
  "cooling_set_point": 20.0,
  "water_temp_set_point": 50.0,
  "tank_level_set_point": 85.0,
  "grid_valve_opening": 100.0,
  "steam_valve_opening": 45.5,
  "pump_frequency": 35.37,
  "product_pump_state": 1,
  "product_pump_mode": 2,
  "water_pump_state": 1,
  "water_pump_mode": 1,
  "product_state": 0,
  "status_main": 1,
  "status_product": 1,
  "tank_level": 82.5,
  "tank_return": 5.2,
  "water_flow_lph": 1500.0,
  "detergent_concentration": 2.5,
  "heater_mode_or_thermistor": 1,
  "termizing_or_heating": 1,
  "entering_holding_or_sending_tanks": 0,
  "machine": "Andino_X1",
  "event_time": "2024-03-02T22:38:10Z"
}
```

3. Click **"Publish"**

### 7.2 Verify Firehose Ingestion

**Check CloudWatch Metrics (AWS Console)**:
1. Go to **CloudWatch** → **Metrics** → **All metrics**
2. Select namespace: **AWS/Firehose**
3. Select metric: **IncomingRecords**
4. Dimension: `DeliveryStreamName = FIREHOSE_DELICE_V1`
5. Should show 1+ incoming records

### 7.3 Wait for Buffer to Flush

⏱️ **Important**: Firehose buffers data. Files appear in S3 after:
- **128 MB** of data accumulated, OR
- **300 seconds** (5 minutes) elapsed

For testing with single message, **wait 5-10 minutes**.

### 7.4 Check S3 for Parquet Files

**Using AWS CLI:**
```bash
aws s3 ls s3://delice-datalake-parquet/ \
  --recursive \
  --profile E2i-dairel-760135066147 \
  | head -20
```

**Expected Output (after 5-10 minutes):**
```
2024-03-02 23:05:23  45678  2024/03/02/23/FIREHOSE_DELICE_V1-1-2024-03-02-23-05-00-abc123.parquet
```

**Using AWS Console:**
1. Go to **S3** → Select bucket: `delice-datalake-parquet`
2. Navigate: `2024/03/02/23/` (today's date + hour)
3. Should see `.parquet` files

### 7.5 Check CloudWatch Logs

**Using AWS CLI:**
```bash
aws logs tail /aws/kinesisfirehose/FIREHOSE_DELICE_V1 \
  --follow \
  --profile E2i-dairel-760135066147 \
  --region us-west-2
```

**Look for success messages:**
- ✅ `Successfully delivered to S3`
- ✅ `Format conversion succeeded`
- ✅ `Record count: X`

**Using AWS Console:**
1. Go to **CloudWatch** → **Log groups**
2. Find: `/aws/kinesisfirehose/FIREHOSE_DELICE_V1`
3. Click **DestinationDelivery** log stream
4. Review recent logs for errors

### 7.6 Verify Timestream (Existing Flow Still Works)

**Using AWS CLI:**
```bash
aws timestream-query query \
  --query-string "SELECT * FROM \"E2iDB\".\"DeliceTableTimestream\" WHERE device_ID = 'Test_Device_001' ORDER BY time DESC LIMIT 5" \
  --profile E2i-dairel-760135066147 \
  --region us-west-2
```

Should return your test message data, confirming the Timestream path still works.

---

## STEP 8: Query Data with Amazon Athena

### 8.1 Configure Athena Query Result Location (First Time Only)

1. AWS Console → Search **"Athena"**
2. Click **"Query Editor"**
3. If prompted for query result location:
   - Click **"Settings"** → **"Manage"**
   - Set location: `s3://athena-query-output-bucket-us-west-2-760135066147/`
   - (Use existing Athena bucket or create new one)
   - Click **"Save"**

### 8.2 Basic Query to View Data

```sql
-- Switch to Delice database
USE delice_db_v1;

-- View all data (most recent first)
SELECT *
FROM delice_table_v1
ORDER BY timestamp DESC
LIMIT 20;
```

### 8.3 Formatted Query with Readable Timestamp

```sql
SELECT
    device_id,
    FROM_UNIXTIME(timestamp) as event_time,
    temp_process_1,
    temp_process_2,
    temp_process_3,
    heating_set_point,
    pump_frequency,
    product_state,
    tank_level,
    water_flow_lph
FROM delice_table_v1
ORDER BY timestamp DESC
LIMIT 50;
```

### 8.4 Analytical Queries

**Average Temperatures by Hour:**
```sql
SELECT
    DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m-%d %H:00') as hour,
    device_id,
    COUNT(*) as measurement_count,
    AVG(temp_process_1) as avg_temp_process_1,
    AVG(temp_process_2) as avg_temp_process_2,
    AVG(temp_process_3) as avg_temp_process_3,
    AVG(heating_set_point) as avg_heating_setpoint,
    MIN(temp_process_1) as min_temp,
    MAX(temp_process_1) as max_temp
FROM delice_table_v1
WHERE timestamp > UNIX_TIMESTAMP(CURRENT_DATE - INTERVAL '7' DAY)
GROUP BY
    DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m-%d %H:00'),
    device_id
ORDER BY hour DESC;
```

**Pump Efficiency Analysis:**
```sql
SELECT
    device_id,
    AVG(pump_frequency) as avg_pump_frequency,
    AVG(water_flow_lph) as avg_water_flow,
    AVG(water_flow_lph / NULLIF(pump_frequency, 0)) as flow_per_hz_ratio,
    COUNT(*) as sample_count
FROM delice_table_v1
WHERE pump_frequency > 0
  AND water_flow_lph > 0
GROUP BY device_id;
```

**Temperature Setpoint vs Actual Analysis:**
```sql
SELECT
    device_id,
    DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m-%d') as date,
    AVG(heating_set_point) as avg_setpoint,
    AVG(temp_process_1) as avg_actual_temp,
    AVG(heating_set_point - temp_process_1) as avg_deviation,
    STDDEV(temp_process_1) as temp_std_dev
FROM delice_table_v1
WHERE timestamp > UNIX_TIMESTAMP(CURRENT_DATE - INTERVAL '30' DAY)
GROUP BY
    device_id,
    DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m-%d')
ORDER BY date DESC;
```

### 8.5 Create Athena View for Easy Access

```sql
-- Create view for hourly summaries
CREATE OR REPLACE VIEW delice_hourly_summary AS
SELECT
    DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m-%d %H:00') as hour,
    device_id,
    COUNT(*) as record_count,
    AVG(temp_process_1) as avg_temp_process_1,
    MIN(temp_process_1) as min_temp_process_1,
    MAX(temp_process_1) as max_temp_process_1,
    AVG(temp_process_2) as avg_temp_process_2,
    AVG(temp_process_3) as avg_temp_process_3,
    AVG(heating_set_point) as avg_heating_setpoint,
    AVG(cooling_set_point) as avg_cooling_setpoint,
    AVG(tank_level) as avg_tank_level,
    AVG(pump_frequency) as avg_pump_frequency,
    AVG(water_flow_lph) as avg_water_flow
FROM delice_table_v1
GROUP BY
    DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m-%d %H:00'),
    device_id;

-- Query the view
SELECT * FROM delice_hourly_summary
ORDER BY hour DESC
LIMIT 100;
```

### 8.6 Verify Query Performance

Run a simple query and note the results:
```sql
SELECT COUNT(*) as total_records
FROM delice_table_v1;
```

Athena will report:
- **Data scanned**: Should be minimal (Parquet columnar format)
- **Query cost**: ~$0.005 per TB scanned
- **Run time**: Should be fast (< 5 seconds for typical datasets)

---

## Architecture Comparison

### Before Implementation (Timestream Only)

```
IoT Device → IoT Rule (delice_rule_test) → Timestream (E2iDB.DeliceTableTimestream)
                                                      ↓
                                          Real-time queries only
                                          7-day memory retention
                                          360-day magnetic retention
                                          Higher query costs for analytics
```

### After Implementation (Dual Path)

```
IoT Device → IoT Rule (delice_rule_test) ─┬─→ Timestream (Real-time, 7-360 days)
                                           │    ↓
                                           │   Dashboards, alerts
                                           │
                                           └─→ Firehose (FIREHOSE_DELICE_V1)
                                                ↓
                                           JSON → Parquet conversion
                                                ↓
                                           S3 (delice-datalake-parquet)
                                                ↓
                                           Unlimited retention
                                                ↓
                                           Athena SQL Analytics
                                                ↓
                                           ML, BI, Compliance
```

### Benefits of Dual Architecture

| Aspect | Timestream Path | Data Lake Path |
|--------|----------------|----------------|
| **Purpose** | Real-time monitoring | Historical analytics |
| **Retention** | 7-360 days | Unlimited |
| **Query Type** | Time-series | SQL, aggregations, joins |
| **Cost** | Higher (per query) | Lower (Parquet + S3) |
| **Use Cases** | Dashboards, alerts | ML, compliance, BI |
| **Latency** | Seconds | Minutes (buffer) |

---

## Configuration Checklist

Use this to verify your implementation:

### AWS Glue
- [ ] Database `delice_db_v1` created in us-west-2
- [ ] Table `delice_table_v1` created with 30 columns
- [ ] Table classification set to **Parquet**
- [ ] All column data types correctly mapped (string, bigint, double)
- [ ] Column names match JSON field names exactly

### S3 Bucket
- [ ] Bucket `delice-datalake-parquet` created
- [ ] Region: **us-west-2** (same as Firehose)
- [ ] Public access: **Blocked**
- [ ] Encryption: **SSE-S3 enabled** (recommended)
- [ ] No bucket policy conflicts

### IAM Role (Firehose)
- [ ] Role `KinesisFirehoseServiceRole-DELICE-*` created
- [ ] Trust policy allows `firehose.amazonaws.com`
- [ ] Inline policy includes Glue GetTable permissions
- [ ] Inline policy includes S3 PutObject to `delice-datalake-parquet`
- [ ] Inline policy includes CloudWatch PutLogEvents
- [ ] Policy name: `KinesisFirehoseServicePolicy-DELICE-us-west-2`

### Kinesis Data Firehose
- [ ] Stream `FIREHOSE_DELICE_V1` created
- [ ] Status: **ACTIVE**
- [ ] Source: **Direct PUT**
- [ ] Destination: **Amazon S3**
- [ ] Format conversion: **ENABLED** ⭐
- [ ] Input format: **OpenX JSON SerDe**
- [ ] Output format: **Apache Parquet**
- [ ] Glue database linked: `delice_db_v1`
- [ ] Glue table linked: `delice_table_v1`
- [ ] Buffer size: **128 MB**
- [ ] Buffer interval: **300 seconds**
- [ ] S3 compression: **Disabled**
- [ ] S3 error prefix: `format-conversion-failed/`
- [ ] CloudWatch logging: **Enabled**
- [ ] IAM role: Correctly attached

### IoT Rule
- [ ] Rule `delice_rule_test` still active
- [ ] SQL unchanged: `SELECT * FROM '/E2i/Delice_topic'`
- [ ] **Two actions present**:
  - [ ] Timestream action (existing)
  - [ ] Firehose action (new)
- [ ] Firehose action configured:
  - [ ] Stream: `FIREHOSE_DELICE_V1`
  - [ ] Batch mode: **Enabled**
  - [ ] IAM role attached (PutRecord permission)
- [ ] Error action unchanged: Republish to `/E2i/Delice_topic/error`

### Testing
- [ ] Test message published to `/E2i/Delice_topic`
- [ ] Data appearing in Timestream (verify existing flow works)
- [ ] Firehose CloudWatch metrics show IncomingRecords > 0
- [ ] Parquet files appearing in S3 (after 5-10 minutes)
- [ ] CloudWatch logs show "Successfully delivered to S3"
- [ ] No errors in `format-conversion-failed/` folder
- [ ] Athena can query `delice_db_v1.delice_table_v1`
- [ ] Query returns test data correctly

---

## Monitoring and Maintenance

### CloudWatch Metrics to Monitor

**Firehose Metrics (Namespace: AWS/Firehose)**

| Metric | Description | Alarm Threshold |
|--------|-------------|-----------------|
| `IncomingRecords` | Records received from IoT | < 1 for 15 min (if expecting data) |
| `DeliveryToS3.Success` | Successful S3 writes | Monitor for trends |
| `DeliveryToS3.DataFreshness` | Age of oldest record in buffer | > 600 seconds (10 min) |
| `FormatConversion.FailedRecords` | Format conversion failures | > 10 in 5 min |
| `DeliveryToS3.Bytes` | Data delivered to S3 | Track data volume |

### Create CloudWatch Alarms

**Alarm 1: No Data Flowing**
```
Metric: IncomingRecords
Statistic: Sum
Period: 15 minutes
Threshold: < 1
Action: Send SNS notification
```

**Alarm 2: Format Conversion Failures**
```
Metric: FormatConversion.FailedRecords
Statistic: Sum
Period: 5 minutes
Threshold: > 10
Action: Send SNS notification
```

**Alarm 3: High Data Freshness (Buffer Not Flushing)**
```
Metric: DeliveryToS3.DataFreshness
Statistic: Maximum
Period: 5 minutes
Threshold: > 600 seconds
Action: Send SNS notification
```

### S3 Lifecycle Policy for Cost Optimization

Create lifecycle rule to move old data to cheaper storage tiers:

**Rule Name**: `MoveOldDataToGlacier`

**Configuration:**
```json
{
  "Rules": [
    {
      "Id": "TransitionToGlacier",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER_IR"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ],
      "NoncurrentVersionTransitions": [],
      "Filter": {
        "Prefix": ""
      }
    }
  ]
}
```

**Cost Impact:**
- Days 0-90: S3 Standard ($0.023/GB/month)
- Days 91-365: Glacier Instant Retrieval ($0.004/GB/month)
- Days 365+: Deep Archive ($0.00099/GB/month)

### Regular Maintenance Tasks

**Weekly:**
- [ ] Check CloudWatch dashboards for anomalies
- [ ] Review error logs in `/aws/kinesisfirehose/FIREHOSE_DELICE_V1`
- [ ] Check `format-conversion-failed/` folder for failed records

**Monthly:**
- [ ] Review S3 storage costs and apply lifecycle policies if needed
- [ ] Verify Athena queries running efficiently (check data scanned)
- [ ] Run data quality checks (missing fields, out-of-range values)

**Quarterly:**
- [ ] Review IAM policies (principle of least privilege)
- [ ] Update Glue table schema if device adds new metrics
- [ ] Audit data retention policies for compliance

---

## Cost Estimation

### Assumptions for Single Delice Device

- **Message frequency**: 1 message per minute
- **Message size**: ~2 KB per message
- **Monthly messages**: 43,200 messages
- **Monthly data volume**: ~86 MB

### Detailed Monthly Cost Breakdown

| Service | Usage | Unit Cost | Monthly Cost |
|---------|-------|-----------|--------------|
| **AWS IoT Rule Executions** | 43,200 messages | $0.0000015/message | **$0.06** |
| **Kinesis Firehose Ingestion** | 86 MB = 0.086 GB | $0.029/GB | **$0.003** |
| **S3 Storage (Standard)** | ~15 MB Parquet | $0.023/GB/month | **$0.0003** |
| **S3 PUT Requests** | ~8,640 requests | $0.005/1000 | **$0.04** |
| **Glue Data Catalog** | 1 database, 1 table | Free (first 1M objects) | **$0.00** |
| **Athena Queries** | 1 GB scanned/month | $0.005/GB | **$0.005** |
| **CloudWatch Logs** | 0.5 GB logs | Free (first 5 GB) | **$0.00** |
| **Timestream (existing)** | Existing cost | N/A | **(unchanged)** |
| | | **TOTAL NEW COST** | **~$0.11/month** |

### Cost Scaling for Multiple Devices

| Number of Devices | Monthly Data | Firehose | S3 Storage | S3 Requests | Total Additional Cost |
|-------------------|--------------|----------|------------|-------------|-----------------------|
| 1 | 86 MB | $0.003 | $0.0003 | $0.04 | **$0.11** |
| 10 | 860 MB | $0.03 | $0.003 | $0.40 | **$1.06** |
| 50 | 4.3 GB | $0.12 | $0.02 | $2.00 | **$5.30** |
| 100 | 8.6 GB | $0.25 | $0.04 | $4.00 | **$10.61** |

### Cost Comparison: Parquet vs JSON

**Scenario**: 100 devices, 12 months, 103 GB total data

| Storage Format | Storage Size | S3 Cost | Athena Scan Cost | Total Annual Cost | Savings |
|----------------|--------------|---------|------------------|-------------------|---------|
| **JSON (uncompressed)** | 103 GB | $28.48 | $61.80 | **$90.28** | - |
| **JSON (gzipped)** | 30 GB | $8.28 | $18.00 | **$26.28** | 71% |
| **Parquet (with Snappy)** | 15 GB | $4.14 | $0.90 | **$5.04** | **94%** |

**Key Insight**: Parquet format saves **$85/year** per 100 devices compared to JSON.

---

## Troubleshooting Guide

### Issue 1: No Parquet Files Appearing in S3

**Symptoms:**
- S3 bucket is empty after 10+ minutes
- No files in `format-conversion-failed/` either

**Possible Causes:**
1. Buffer not triggered (need 128MB or 300 seconds)
2. IAM role lacks S3 PutObject permission
3. Firehose stream not active
4. IoT rule not triggering Firehose action

**Diagnostic Steps:**

```bash
# 1. Check Firehose stream status
aws firehose describe-delivery-stream \
  --delivery-stream-name FIREHOSE_DELICE_V1 \
  --profile E2i-dairel-760135066147 \
  --region us-west-2 \
  --query 'DeliveryStreamDescription.DeliveryStreamStatus'

# Expected: "ACTIVE"

# 2. Check Firehose metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name IncomingRecords \
  --dimensions Name=DeliveryStreamName,Value=FIREHOSE_DELICE_V1 \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --profile E2i-dairel-760135066147 \
  --region us-west-2

# 3. Check CloudWatch logs for errors
aws logs tail /aws/kinesisfirehose/FIREHOSE_DELICE_V1 \
  --since 30m \
  --profile E2i-dairel-760135066147 \
  --region us-west-2
```

**Solutions:**
- If IncomingRecords = 0: Check IoT rule action is properly configured
- If status ≠ ACTIVE: Wait or recreate stream
- If logs show "Access Denied": Fix IAM role permissions

---

### Issue 2: Files in format-conversion-failed/ Folder

**Symptoms:**
- Files appearing in `s3://delice-datalake-parquet/format-conversion-failed/`
- No Parquet files in main bucket

**Possible Causes:**
1. JSON field names don't match Glue table schema
2. Data type mismatch (sending string when schema expects number)
3. Required fields missing in JSON
4. Invalid JSON structure

**Diagnostic Steps:**

```bash
# Download error file
aws s3 cp s3://delice-datalake-parquet/format-conversion-failed/ . \
  --recursive \
  --profile E2i-dairel-760135066147

# View error file content
cat format-conversion-failed/FIREHOSE_DELICE_V1-*

# Common error patterns:
# - "Field 'field_name' not found in schema"
# - "Cannot convert 'string' to 'bigint'"
# - "Required field missing"
```

**Solutions:**

**Mismatch Example 1: Wrong field name**
```json
// Sent JSON
{"device_ID": "...", "temp_proc_1": 65.5}  // Wrong!

// Expected by Glue schema
{"device_id": "...", "temp_process_1": 65.5}  // Correct
```

**Mismatch Example 2: Wrong data type**
```json
// Sent JSON
{"timestamp": "2024-03-02"}  // String!

// Expected by Glue schema (bigint)
{"timestamp": 1709915890}  // Unix timestamp
```

**Fix:**
1. Compare failed JSON with Glue table column names (exact match required)
2. Verify data types match schema
3. Update IoT device payload OR update Glue table schema
4. Republish test message

---

### Issue 3: IoT Rule Not Triggering

**Symptoms:**
- No data in Timestream OR Firehose
- IoT metrics show 0 messages

**Diagnostic Steps:**

```bash
# Check IoT rule metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/IoT \
  --metric-name RuleMessageMatched \
  --dimensions Name=RuleName,Value=delice_rule_test \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --profile E2i-dairel-760135066147 \
  --region us-west-2

# Check rule status
aws iot get-topic-rule \
  --rule-name delice_rule_test \
  --profile E2i-dairel-760135066147 \
  --region us-west-2 \
  --query 'rule.ruleDisabled'

# Expected: false
```

**Solutions:**
- If RuleMessageMatched = 0: No messages on topic `/E2i/Delice_topic`
- If ruleDisabled = true: Enable the rule in IoT Console
- Verify device is publishing to correct topic

---

### Issue 4: Athena Query Fails

**Symptoms:**
- Error: `HIVE_CANNOT_OPEN_SPLIT`
- Error: `Table not found`
- Query returns 0 rows

**Possible Causes:**
1. No Parquet files in S3 yet
2. Wrong database selected
3. Glue table metadata issues
4. S3 path mismatch

**Solutions:**

```sql
-- 1. Verify database exists
SHOW DATABASES;

-- 2. Switch to correct database
USE delice_db_v1;

-- 3. Verify table exists
SHOW TABLES;

-- 4. Check table metadata
SHOW CREATE TABLE delice_table_v1;

-- 5. Check if table has data
SELECT COUNT(*) FROM delice_table_v1;
```

**If COUNT returns 0:**
- Wait 5-10 minutes for first Parquet files
- Check S3 bucket has files: `aws s3 ls s3://delice-datalake-parquet/ --recursive`
- Run Glue Crawler to update partitions

---

### Issue 5: High Athena Query Costs

**Symptoms:**
- Athena queries scanning more data than expected
- Higher than expected charges

**Diagnostic Steps:**

Check data scanned in Athena query history:
```sql
SELECT * FROM delice_table_v1 LIMIT 10;
-- Note: Data scanned = X GB
```

**Solutions:**

**1. Use Partitioning (if enabled):**
```sql
-- Bad (scans all data)
SELECT * FROM delice_table_v1
WHERE timestamp > 1709000000;

-- Good (uses partitions if available)
SELECT * FROM delice_table_v1
WHERE year = '2024' AND month = '03' AND day = '02';
```

**2. Select Only Needed Columns:**
```sql
-- Bad (reads all 30 columns)
SELECT * FROM delice_table_v1 LIMIT 100;

-- Good (reads only 3 columns)
SELECT device_id, timestamp, temp_process_1
FROM delice_table_v1 LIMIT 100;
```

**3. Use LIMIT Effectively:**
```sql
-- Always use LIMIT for exploratory queries
SELECT * FROM delice_table_v1
ORDER BY timestamp DESC
LIMIT 100;  -- Prevents full table scan
```

---

### Issue 6: Firehose Delivery Delayed

**Symptoms:**
- Data appears in S3 but with 5-10 minute delay
- Dashboards showing stale data

**Explanation:**
This is **normal behavior**. Firehose buffers data:
- **Buffer size**: 128 MB
- **Buffer interval**: 300 seconds (5 minutes)

Data is written when **EITHER** condition is met first.

**If delay is critical:**

**Option 1: Reduce buffer interval (minimum 60 seconds)**
- Go to Firehose Console
- Edit delivery stream
- Change interval from 300 → 60 seconds
- ⚠️ This increases S3 PUT requests (higher cost)

**Option 2: Keep Timestream for real-time**
- Use Timestream for dashboards (< 1 minute latency)
- Use S3/Athena for historical analytics (5+ minute latency)

---

## Next Steps After Implementation

### Immediate (Week 1)
1. **Monitor CloudWatch**
   - Set up dashboard for Firehose metrics
   - Create alarms for failures
   - Review logs daily

2. **Validate Data Quality**
   - Run Athena queries to spot-check data
   - Compare counts: Timestream vs Athena
   - Check for missing fields or null values

3. **Document for Team**
   - Share this guide with operations team
   - Document any customizations made
   - Create runbook for common issues

### Short Term (Month 1)
1. **Optimize Queries**
   - Create Athena views for common queries
   - Save frequently used queries
   - Train team on SQL analytics

2. **Set Up Lifecycle Policies**
   - Configure S3 transitions to Glacier (90 days)
   - Set up Deep Archive (365 days)
   - Estimate long-term storage costs

3. **Expand to More Devices**
   - Add other Delice devices (same pipeline)
   - Consider separate streams for different device types
   - Scale IAM policies as needed

### Long Term (Quarter 1)
1. **Build Analytics Dashboard**
   - Use Amazon QuickSight for visualization
   - Create dashboards for:
     - Temperature trends
     - Pump efficiency
     - System uptime
     - Anomaly detection

2. **ML and Advanced Analytics**
   - Use SageMaker for predictive maintenance
   - Train models on historical Parquet data
   - Detect anomalies in temperature/flow patterns

3. **Compliance and Governance**
   - Implement data retention policies
   - Set up AWS Lake Formation for access control
   - Enable S3 Object Lock for immutability (if required)
   - Create audit logs for data access

---

## Reference Information

### AWS Service Endpoints (us-west-2)

| Service | Endpoint |
|---------|----------|
| AWS IoT Core | `iot.us-west-2.amazonaws.com` |
| Kinesis Firehose | `firehose.us-west-2.amazonaws.com` |
| S3 | `s3.us-west-2.amazonaws.com` |
| AWS Glue | `glue.us-west-2.amazonaws.com` |
| Amazon Athena | `athena.us-west-2.amazonaws.com` |
| Timestream | `timestream.us-west-2.amazonaws.com` |

### Quick Reference Commands

```bash
# Set environment variables
export PROFILE="E2i-dairel-760135066147"
export REGION="us-west-2"

# Check Firehose status
aws firehose describe-delivery-stream \
  --delivery-stream-name FIREHOSE_DELICE_V1 \
  --profile $PROFILE --region $REGION

# List S3 files
aws s3 ls s3://delice-datalake-parquet/ \
  --recursive --profile $PROFILE | head -20

# Tail logs
aws logs tail /aws/kinesisfirehose/FIREHOSE_DELICE_V1 \
  --follow --profile $PROFILE --region $REGION

# Query Timestream
aws timestream-query query \
  --query-string "SELECT * FROM \"E2iDB\".\"DeliceTableTimestream\" ORDER BY time DESC LIMIT 5" \
  --profile $PROFILE --region $REGION

# Check Firehose metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name IncomingRecords \
  --dimensions Name=DeliveryStreamName,Value=FIREHOSE_DELICE_V1 \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum \
  --profile $PROFILE --region $REGION
```

### Important ARNs

```
IoT Rule:
arn:aws:iot:us-west-2:760135066147:rule/delice_rule_test

Firehose Stream:
arn:aws:firehose:us-west-2:760135066147:deliverystream/FIREHOSE_DELICE_V1

S3 Bucket:
arn:aws:s3:::delice-datalake-parquet

Glue Database:
arn:aws:glue:us-west-2:760135066147:database/delice_db_v1

Glue Table:
arn:aws:glue:us-west-2:760135066147:table/delice_db_v1/delice_table_v1

IAM Role:
arn:aws:iam::760135066147:role/service-role/KinesisFirehoseServiceRole-DELICE-us-west-2-*
```

---

## Support and Resources

### AWS Documentation
- [Kinesis Data Firehose Developer Guide](https://docs.aws.amazon.com/firehose/)
- [AWS Glue Data Catalog](https://docs.aws.amazon.com/glue/latest/dg/catalog-and-crawler.html)
- [Amazon Athena User Guide](https://docs.aws.amazon.com/athena/)
- [Apache Parquet Documentation](https://parquet.apache.org/docs/)
- [AWS IoT Core Developer Guide](https://docs.aws.amazon.com/iot/)

### Internal Resources
- Original REY pipeline analysis (reference implementation)
- Generic replication manual (for other devices)
- AWS account: 760135066147
- AWS profile: E2i-dairel-760135066147

---

## Appendix: Complete Schema Reference

### Glue Table: delice_table_v1

| # | Column | Type | Description | JSON Example |
|---|--------|------|-------------|--------------|
| 1 | device_id | string | Device identifier | "Andino_X1_P01" |
| 2 | timestamp | bigint | Unix timestamp (seconds) | 1709915890 |
| 3 | temp_process_1 | double | Process temp sensor 1 (°C) | 65.5 |
| 4 | temp_process_2 | double | Process temp sensor 2 (°C) | 68.2 |
| 5 | temp_process_3 | double | Process temp sensor 3 (°C) | 58.9 |
| 6 | temp_water_1 | double | Water temp sensor 1 (°C) | 45.0 |
| 7 | temp_water_2 | double | Water temp sensor 2 (°C) | 47.3 |
| 8 | heating_set_point | double | Heating setpoint (°C) | 74.5 |
| 9 | cooling_set_point | double | Cooling setpoint (°C) | 20.0 |
| 10 | water_temp_set_point | double | Water temp setpoint (°C) | 50.0 |
| 11 | tank_level_set_point | double | Tank level setpoint (%) | 85.0 |
| 12 | grid_valve_opening | double | Grid valve opening (%) | 100.0 |
| 13 | steam_valve_opening | double | Steam valve opening (%) | 45.5 |
| 14 | pump_frequency | double | Pump frequency (Hz) | 35.37 |
| 15 | product_pump_state | bigint | Product pump state | 1 |
| 16 | product_pump_mode | bigint | Product pump mode | 2 |
| 17 | water_pump_state | bigint | Water pump state | 1 |
| 18 | water_pump_mode | bigint | Water pump mode | 1 |
| 19 | product_state | bigint | Product state | 0 |
| 20 | status_main | bigint | Main system status | 1 |
| 21 | status_product | bigint | Product system status | 1 |
| 22 | tank_level | double | Tank level (%) | 82.5 |
| 23 | tank_return | double | Tank return | 5.2 |
| 24 | water_flow_lph | double | Water flow (L/hr) | 1500.0 |
| 25 | detergent_concentration | double | Detergent conc. (%) | 2.5 |
| 26 | heater_mode_or_thermistor | bigint | Heater mode/thermistor | 1 |
| 27 | termizing_or_heating | bigint | Termizing/heating mode | 1 |
| 28 | entering_holding_or_sending_tanks | bigint | Tank entry/exit | 0 |
| 29 | machine | string | Machine identifier | "Andino_X1" |
| 30 | event_time | string | ISO timestamp | "2024-03-02T22:38:10Z" |

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-03-02 | System | Initial release |

---

**END OF IMPLEMENTATION GUIDE**

This document provides complete step-by-step instructions for implementing the Delice data lake pipeline. No infrastructure has been modified during the creation of this guide. All steps are manual and require explicit execution by authorized personnel.
