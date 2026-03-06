# Delice Firehose Rule - Test Results

**Test Date:** March 4, 2026, 6:29 PM EST
**Rule Name:** `delice_firehose_rule`

---

## Test Configuration

### New IoT Rule Created

**Rule:** `delice_firehose_rule`
- **Created:** March 4, 2026, 12:08 PM EST
- **Status:** Enabled ✅
- **SQL Statement:**
  ```sql
  SELECT * FROM '+/E2i/Delice_topic'
  ```
- **Action:** Firehose to `FIREHOSE_DELICE_V1`
- **Batch Mode:** Enabled
- **IAM Role:** `iot-firehose-delice-role`

### Test Message Details

**Published At:** 6:29:16 PM EST
**Topic:** `/E2i/Delice_topic`
**Device ID:** `DELICE_TEST_NEW_RULE`
**Payload Size:** ~1 KB

**Test Data:**
```json
{
  "device_ID": "DELICE_TEST_NEW_RULE",
  "timestamp": 1709600000,
  "temp_process_1": 75.5,
  "temp_process_2": 76.3,
  "temp_process_3": 74.8,
  "temp_water_1": 45.2,
  "temp_water_2": 44.8,
  "heating_set_point": 90.0,
  "cooling_set_point": 5.0,
  "water_temp_set_point": 45.0,
  "grid_valve_opening": 65.3,
  "steam_valve_opening": 45.8,
  "pump_frequency": 50.0,
  "product_pump_state": 1,
  "water_pump_state": 1,
  "product_state": 2,
  "status_main": 1,
  "status_product": 1,
  "water_flow_lph": 120.5,
  "tank_level": 75.3,
  "tank_return": 12.4,
  "detergent_concentration": 2.5,
  "cleaning_mode": 0,
  "heating_mode": 1,
  "cooling_mode": 0,
  "water_mode": 1,
  "alarm_active": 0,
  "emergency_stop": 0,
  "mqtt_topic": "/E2i/Delice_topic"
}
```

---

## Expected Timeline

| Time | Event | Status |
|------|-------|--------|
| 6:29 PM | Test message published | ✅ Complete |
| 6:29 PM | IoT Rule matches message | ⏳ Pending verification |
| 6:29 PM | Firehose receives record | ⏳ Pending verification |
| 6:34 PM | **Firehose buffer flushes to S3** | ⏳ **WAIT** |
| 6:35 PM | Parquet file appears in S3 | ⏳ To be checked |

---

## Verification Commands

### Check IoT Rule Metrics (After 2 minutes)
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/IoT \
  --metric-name RuleMessageMatched \
  --dimensions Name=RuleName,Value=delice_firehose_rule \
  --start-time $(date -u -v-10M +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 --statistics Sum \
  --region us-west-2 --profile E2i-dairel-760135066147
```

### Check Firehose Metrics (After 5 minutes)
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Firehose \
  --metric-name DeliveryToS3.Success \
  --dimensions Name=DeliveryStreamName,Value=FIREHOSE_DELICE_V1 \
  --start-time $(date -u -v-10M +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 --statistics Sum \
  --region us-west-2 --profile E2i-dairel-760135066147
```

### Check S3 for New Files (After 5 minutes)
```bash
aws s3 ls s3://delice-datalake-parquet/2026/03/04/23/ \
  --profile E2i-dairel-760135066147 \
  --recursive --human-readable
```
*Note: Time is in UTC, so local 6:34 PM EST = 11:34 PM UTC = hour 23*

---

## Success Criteria

✅ **Test Passes If:**
1. CloudWatch shows `RuleMessageMatched = 1` for `delice_firehose_rule`
2. CloudWatch shows `IncomingRecords = 1` for `FIREHOSE_DELICE_V1`
3. New Parquet file appears in S3 at `2026/03/04/23/FIREHOSE_DELICE_V1-*.parquet`
4. Athena query shows new record with `device_id = 'DELICE_TEST_NEW_RULE'`

❌ **Test Fails If:**
- No CloudWatch metrics appear after 10 minutes
- No S3 file after 10 minutes
- Parquet file contains NULL values or wrong data

---

## Differences from Previous Tests

### Why This Should Work

| Previous Issue | New Rule Solution |
|---------------|-------------------|
| SQL had quotes: `'/E2i/Delice_topic'` | ✅ Fixed: `'+/E2i/Delice_topic'` |
| Mixed with Timestream action | ✅ Dedicated Firehose-only rule |
| Hard to debug which action failed | ✅ Single action, easy to troubleshoot |
| Tested with `#` wildcard (all topics) | ✅ Specific Delice topic filter |

---

## Next Steps After 5 Minutes

### If Test SUCCEEDS ✅

1. **Verify Data in Athena:**
   ```sql
   SELECT * FROM delice_db_v1.delice_table_v1
   WHERE device_id = 'DELICE_TEST_NEW_RULE'
   LIMIT 10;
   ```

2. **Wait for Real Device Data:**
   - Device expected to resume tomorrow morning
   - Pipeline will capture real Delice data automatically

3. **Optional: Clean Up Old Test Data:**
   ```bash
   # Delete the 13 test Parquet files from when using '#' wildcard
   aws s3 rm s3://delice-datalake-parquet/2026/03/04/14/ --recursive
   aws s3 rm s3://delice-datalake-parquet/2026/03/04/15/ --recursive
   ```

4. **Update Documentation:**
   - Mark `delice_firehose_rule` as production rule
   - Consider removing Firehose action from old `delice_rule_test`

---

### If Test FAILS ❌

**Troubleshooting Steps:**

1. **Check IoT Rule is Enabled:**
   ```bash
   aws iot get-topic-rule --rule-name delice_firehose_rule \
     --region us-west-2 --profile E2i-dairel-760135066147 \
     --query 'rule.ruleDisabled'
   ```

2. **Check IAM Role Permissions:**
   ```bash
   aws iam get-role-policy \
     --role-name iot-firehose-delice-role \
     --policy-name aws-iot-rule-delice_rule_test-action-2-role-iot-firehose-delice-role \
     --profile E2i-dairel-760135066147
   ```

3. **Check Firehose Error Logs:**
   ```bash
   aws logs tail /aws/kinesisfirehose/FIREHOSE_DELICE_V1 \
     --region us-west-2 --profile E2i-dairel-760135066147 \
     --since 10m
   ```

4. **Try Different SQL Patterns:**
   - Test with `#` (all topics) to verify Firehose works
   - If `#` works but `'+/E2i/Delice_topic'` doesn't, topic format issue

5. **Check Glue Schema Compatibility:**
   - Ensure test message JSON matches Glue table schema
   - Verify all 30 columns exist in test payload

---

## Architecture - Current State

```
Delice Device → /E2i/Delice_topic
                      ↓
                ┌─────┴─────┐
                ↓           ↓
   delice_rule_test    delice_firehose_rule (NEW)
        ↓                   ↓
    Timestream         Firehose
    (working ✅)           ↓
                      Format Convert
                      (JSON→Parquet)
                           ↓
                       S3 Bucket
                 delice-datalake-parquet/
                           ↓
                       Athena
                    (queryable)
```

---

## Test Execution Checklist

- [x] Create new IoT rule `delice_firehose_rule`
- [x] Configure SQL with wildcard: `SELECT * FROM '+/E2i/Delice_topic'`
- [x] Configure Firehose action with correct role
- [x] Publish test message to `/E2i/Delice_topic`
- [ ] Wait 5 minutes for buffer
- [ ] Check CloudWatch metrics
- [ ] Check S3 for new Parquet file
- [ ] Query data with Athena
- [ ] Document results

---

**Status:** ⏳ Waiting for Firehose 5-minute buffer to flush data to S3

**Expected File Location:**
```
s3://delice-datalake-parquet/2026/03/04/23/FIREHOSE_DELICE_V1-1-2026-03-04-23-XX-XX-<uuid>.parquet
```

**Check at:** 6:35 PM EST (11:35 PM UTC)

---

**Document Created:** March 4, 2026, 6:30 PM EST
**Test In Progress**
