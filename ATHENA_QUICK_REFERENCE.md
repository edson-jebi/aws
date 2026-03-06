# Athena Query Editor - Quick Reference Card

## 🚀 Quick Start (3 Steps)

### 1. Open Athena
- AWS Console → Search "Athena" → Query editor
- Region: **us-west-2** (Oregon)

### 2. Configure (First Time Only)
- Settings → Query result location:
  ```
  s3://direct-put-rey-s3-v2/athena-results/
  ```

### 3. Select Database
- Database dropdown → **`rey_db_v3`**

---

## 📝 Query 1: Data Lake Overview

**Copy & Paste:**
```sql
SELECT
    COUNT(*) as total_records,
    COUNT(DISTINCT device_id) as unique_devices,
    MIN(timestamp) as first_record_timestamp,
    MAX(timestamp) as last_record_timestamp
FROM rey_db_v3.rey_table_only_v2
```

**Expected Result:**
- 132,380,514 records
- 1 unique device
- ~5-10 seconds
- ~3-5 GB scanned

---

## 📝 Query 2: Engine Performance

**Copy & Paste:**
```sql
SELECT
    device_id,
    AVG(eng_speed) as avg_engine_speed_rpm,
    AVG(eng_coolant_temp_2) as avg_coolant_temp_celsius,
    AVG(eng_oil_pressure) as avg_oil_pressure_kpa,
    COUNT(*) as total_readings,
    COUNT(*) * 5.0 / 3600.0 as estimated_operation_hours
FROM rey_db_v3.rey_table_only_v2
WHERE eng_speed > 0
GROUP BY device_id
ORDER BY total_readings DESC
```

**Expected Result:**
- 2 rows (GF401132 + null)
- RPM: 1335-1374
- ~6-10 seconds
- ~500 MB-1 GB scanned

---

## ✅ Success Checklist

- [ ] Status shows "SUCCEEDED" (green)
- [ ] Results table shows data
- [ ] Run time < 15 seconds
- [ ] Data scanned shown in GB
- [ ] Screenshot captured

---

## 💰 Cost Reference

| Query | Data Scanned | Cost |
|-------|--------------|------|
| Query 1 | 3-5 GB | $0.015-$0.025 |
| Query 2 | 0.5-1 GB | $0.0025-$0.005 |

**Total:** ~$0.02-$0.03 per run

---

## 🔧 Common Issues

### "Table does not exist"
→ Check database: `rey_db_v3`

### "Access Denied"
→ Verify profile: `E2i-dairel-760135066147`

### Query too slow (>30s)
→ First run of day (normal)

### Syntax error
→ Copy-paste queries exactly as shown

---

## 📸 Evidence to Capture

1. Screenshot showing:
   - SQL query
   - Results table
   - "SUCCEEDED" status
   - Run time + Data scanned

2. Optional: Download CSV results

---

## 🔗 Full Documentation

See: `ATHENA_QUERY_EDITOR_STEP_BY_STEP.md`
