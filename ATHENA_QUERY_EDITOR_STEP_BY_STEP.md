# Cómo Probar las Consultas en Athena Query Editor - Guía Paso a Paso

**Fecha:** 5 de Marzo de 2026
**Propósito:** Validar las 2 consultas Athena en AWS Console manualmente

---

## REQUISITOS PREVIOS

✅ Acceso a AWS Console con perfil: `E2i-dairel-760135066147`
✅ Permisos para: Amazon Athena, S3
✅ Database: `rey_db_v3`
✅ Tabla: `rey_table_only_v2`

---

## PASO 1: ACCEDER A ATHENA QUERY EDITOR

### 1.1 Iniciar Sesión en AWS Console

1. Abrir navegador web
2. Ir a: https://console.aws.amazon.com/
3. Iniciar sesión con cuenta: **760135066147**
4. Seleccionar región: **US West (Oregon) us-west-2**
   - Verificar en esquina superior derecha que diga "US West (Oregon)"

### 1.2 Navegar a Amazon Athena

**Opción A - Barra de Búsqueda:**
1. Click en barra de búsqueda superior (dice "Search")
2. Escribir: `Athena`
3. Click en **"Athena"** en resultados (icono naranja con logo de consulta)

**Opción B - Menú de Servicios:**
1. Click en "Services" (esquina superior izquierda)
2. Categoría: **Analytics**
3. Click en **"Amazon Athena"**

### 1.3 Abrir Query Editor

1. En menú lateral izquierdo, click en **"Query editor"**
2. Si aparece un banner de bienvenida, click **"Get Started"** o cerrar

---

## PASO 2: CONFIGURAR ATHENA (PRIMERA VEZ SOLAMENTE)

### 2.1 Configurar Ubicación de Resultados

Si es la primera vez usando Athena, aparecerá un mensaje:
> "Before you run your first query, you need to set up a query result location in Amazon S3"

**Pasos:**
1. Click en **"Settings"** (pestaña superior) o botón **"Set up a query result location"**
2. En "Query result location", ingresar:
   ```
   s3://direct-put-rey-s3-v2/athena-results/
   ```
3. (Opcional) Marcar **"Encrypt query results"** si es necesario
4. Click **"Save"**
5. Volver a pestaña **"Editor"**

---

## PASO 3: SELECCIONAR DATABASE Y TABLA

### 3.1 Panel Izquierdo - Data

En el panel izquierdo verás:
```
Data
└── Data source: AwsDataCatalog
    └── Database: [dropdown]
```

**Pasos:**
1. Click en el dropdown **"Database"**
2. Buscar y seleccionar: **`rey_db_v3`**
3. Esperar 1-2 segundos a que cargue

### 3.2 Verificar Tabla Existe

Debajo del dropdown de Database verás:
```
Tables (X)
└── rey_table_only_v2
└── rey_table_prepro
└── rey_table_v3
└── ...
```

**Pasos:**
1. Verificar que aparece **`rey_table_only_v2`** en la lista
2. (Opcional) Click en el ícono de "..." junto a `rey_table_only_v2`
3. (Opcional) Seleccionar **"Preview table"** para ver primeras 10 filas

---

## PASO 4: EJECUTAR CONSULTA 1 - RESUMEN GENERAL

### 4.1 Limpiar Editor

En el panel central (Query editor):
1. Borrar cualquier consulta existente (si hay)
2. Asegurar que el editor esté vacío

### 4.2 Copiar Consulta 1

Copiar y pegar esta consulta EXACTAMENTE:

```sql
SELECT
    COUNT(*) as total_records,
    COUNT(DISTINCT device_id) as unique_devices,
    MIN(timestamp) as first_record_timestamp,
    MAX(timestamp) as last_record_timestamp
FROM rey_db_v3.rey_table_only_v2
```

### 4.3 Ejecutar Consulta

1. Click en botón **"Run"** (azul, esquina superior derecha del editor)
   - O presionar: **Ctrl + Enter** (Windows) / **Cmd + Enter** (Mac)

2. Observar barra de progreso en la parte inferior:
   ```
   Status: RUNNING → SUCCEEDED
   ```

3. **Tiempo esperado:** 5-10 segundos

### 4.4 Verificar Resultados

En la pestaña **"Results"** (parte inferior) deberías ver:

| total_records | unique_devices | first_record_timestamp | last_record_timestamp |
|---------------|----------------|------------------------|----------------------|
| 132380514     | 1              | [timestamp]            | [timestamp]          |

**✅ VALIDACIÓN:**
- ✅ `total_records` debe ser **aproximadamente 132 millones**
- ✅ `unique_devices` debe ser **1**
- ✅ Los timestamps deben mostrar fechas de **2024**

### 4.5 Verificar Datos Escaneados

En la parte superior de los resultados verás:
```
Run time: X seconds | Data scanned: X.XX GB
```

**Esperado:**
- Run time: 5-10 segundos
- Data scanned: 3-5 GB

### 4.6 Captura de Pantalla (Para Evidencia)

**Tomar captura de pantalla mostrando:**
- ✅ La consulta SQL en el editor
- ✅ Los resultados en la tabla
- ✅ "Status: SUCCEEDED" en verde
- ✅ "Run time" y "Data scanned"
- ✅ Database seleccionado: `rey_db_v3`

---

## PASO 5: EJECUTAR CONSULTA 2 - RENDIMIENTO DEL MOTOR

### 5.1 Limpiar Editor

1. Click en botón **"+"** (nueva pestaña) en el editor
   - O seleccionar todo el texto (Ctrl+A) y borrar

### 5.2 Copiar Consulta 2

Copiar y pegar esta consulta EXACTAMENTE:

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

### 5.3 Ejecutar Consulta

1. Click en botón **"Run"**
2. Observar progreso: `Status: RUNNING → SUCCEEDED`
3. **Tiempo esperado:** 6-10 segundos

### 5.4 Verificar Resultados

Deberías ver **2 filas de resultados**:

| device_id | avg_engine_speed_rpm | avg_coolant_temp_celsius | avg_oil_pressure_kpa | total_readings | estimated_operation_hours |
|-----------|---------------------|--------------------------|---------------------|----------------|---------------------------|
| GF401132  | 1335.39             | (null o número)          | (null o número)      | 1148963        | 1596.89                   |
| (null)    | 1374.13             | (null o número)          | (null o número)      | 677354         | 941.88                    |

**✅ VALIDACIÓN:**
- ✅ Debe haber **2 filas** (dos dispositivos)
- ✅ `avg_engine_speed_rpm` debe estar entre **1300-1400 RPM**
- ✅ `total_readings` para GF401132 debe ser **~1.1 millones**
- ✅ `estimated_operation_hours` debe ser **~1600 horas** para GF401132

### 5.5 Verificar Datos Escaneados

```
Run time: X seconds | Data scanned: X.XX GB
```

**Esperado:**
- Run time: 6-10 segundos
- Data scanned: 500 MB - 1.5 GB (menor que Consulta 1 porque usa filtro WHERE)

### 5.6 Captura de Pantalla (Para Evidencia)

**Tomar captura de pantalla mostrando:**
- ✅ La consulta SQL completa en el editor
- ✅ Las 2 filas de resultados
- ✅ "Status: SUCCEEDED"
- ✅ "Run time" y "Data scanned"

---

## PASO 6: DESCARGAR RESULTADOS (OPCIONAL)

### 6.1 Descargar como CSV

En la sección de resultados:
1. Click en botón **"Download results"** (ícono de descarga)
2. Seleccionar formato: **CSV**
3. Guardar archivo localmente

**Archivo guardado:**
- `Query_1_results.csv`
- `Query_2_results.csv`

### 6.2 Ver Resultados en S3

Los resultados también se guardan automáticamente en S3:

1. Ir a **Amazon S3** en AWS Console
2. Navegar a bucket: `direct-put-rey-s3-v2`
3. Ir a carpeta: `athena-results/`
4. Buscar archivos más recientes (ordenar por fecha)

Verás archivos como:
```
athena-results/
├── 10bfdf7a-8a88-4d8c-84a4-db31c095cdd2.csv
├── 10bfdf7a-8a88-4d8c-84a4-db31c095cdd2.csv.metadata
├── 6cf1acbc-0749-43ad-aa11-8595ab4a5ff6.csv
└── 6cf1acbc-0749-43ad-aa11-8595ab4a5ff6.csv.metadata
```

---

## PASO 7: VERIFICAR HISTORIAL DE CONSULTAS

### 7.1 Acceder al Historial

1. En Athena Query Editor, click en pestaña **"Recent queries"** (parte superior)
2. Verás lista de consultas ejecutadas recientemente

### 7.2 Verificar Detalles

Para cada consulta verás:
- **Query**: Primeras palabras de la consulta SQL
- **Status**: SUCCEEDED (verde) o FAILED (rojo)
- **Run time**: Duración en segundos
- **Data scanned**: GB escaneados
- **Query ID**: Identificador único (ej: `10bfdf7a-8a88-4d8c-84a4-db31c095cdd2`)
- **Date**: Fecha y hora de ejecución

### 7.3 Re-ejecutar Consulta Anterior

1. Click en cualquier fila de consulta anterior
2. La consulta se cargará en el editor
3. Click **"Run"** para ejecutar nuevamente

---

## PASO 8: VALIDACIÓN FINAL - CHECKLIST

Marca cada ítem al completarlo:

### Consulta 1: Resumen General
- [ ] Consulta ejecutada sin errores (Status: SUCCEEDED)
- [ ] Resultado muestra ~132 millones de registros
- [ ] Tiempo de ejecución: 5-10 segundos
- [ ] Datos escaneados: 3-5 GB
- [ ] Captura de pantalla tomada
- [ ] Resultados descargados (opcional)

### Consulta 2: Rendimiento Motor
- [ ] Consulta ejecutada sin errores (Status: SUCCEEDED)
- [ ] Resultado muestra 2 filas (dispositivos)
- [ ] RPM promedio entre 1300-1400
- [ ] Tiempo de ejecución: 6-10 segundos
- [ ] Datos escaneados: 500 MB - 1.5 GB
- [ ] Captura de pantalla tomada
- [ ] Resultados descargados (opcional)

### Configuración Athena
- [ ] Database `rey_db_v3` seleccionado
- [ ] Tabla `rey_table_only_v2` visible en lista
- [ ] Ubicación de resultados configurada: `s3://direct-put-rey-s3-v2/athena-results/`
- [ ] Historial de consultas muestra ambas ejecuciones

---

## PASO 9: CONSULTAS ADICIONALES PARA PROBAR (OPCIONAL)

### Consulta Rápida 1: Ver Primeras 10 Filas

```sql
SELECT *
FROM rey_db_v3.rey_table_only_v2
LIMIT 10
```

**Esperado:** 10 filas con todas las 221 columnas
**Tiempo:** <1 segundo
**Datos escaneados:** <10 MB

---

### Consulta Rápida 2: Contar Registros por Mes (2024)

```sql
SELECT
    month,
    COUNT(*) as records_per_month
FROM rey_db_v3.rey_table_only_v2
WHERE year = '2024'
GROUP BY month
ORDER BY month
```

**Esperado:** Lista de meses con conteos
**Tiempo:** 5-8 segundos
**Datos escaneados:** 1-2 GB

---

### Consulta Rápida 3: Dispositivos Únicos

```sql
SELECT
    device_id,
    COUNT(*) as total_records
FROM rey_db_v3.rey_table_only_v2
GROUP BY device_id
ORDER BY total_records DESC
```

**Esperado:** 2 filas (GF401132 + null)
**Tiempo:** 5-8 segundos
**Datos escaneados:** 500 MB - 1 GB

---

## PASO 10: SOLUCIÓN DE PROBLEMAS

### Problema 1: "HIVE_CURSOR_ERROR: Row is not a valid JSON Object"

**Causa:** Archivo Parquet corrupto o mal formateado

**Solución:**
```sql
-- Usar partición específica para evitar archivos problemáticos
SELECT COUNT(*)
FROM rey_db_v3.rey_table_only_v2
WHERE year = '2024' AND month = '08'
```

---

### Problema 2: "SYNTAX_ERROR: line X:Y: mismatched input"

**Causa:** Error de sintaxis SQL

**Solución:**
- Verificar que la consulta esté copiada EXACTAMENTE como se muestra
- Verificar que el nombre de tabla sea: `rey_db_v3.rey_table_only_v2`
- Verificar que no haya caracteres especiales ocultos

---

### Problema 3: "Table does not exist"

**Causa:** Database o tabla incorrecta

**Solución:**
1. Verificar database seleccionado en dropdown: `rey_db_v3`
2. Listar tablas disponibles:
   ```sql
   SHOW TABLES IN rey_db_v3
   ```
3. Verificar nombre exacto de tabla en lista

---

### Problema 4: "Access Denied" o "Insufficient permissions"

**Causa:** Permisos IAM insuficientes

**Solución:**
- Verificar que estás usando el perfil correcto: `E2i-dairel-760135066147`
- Contactar administrador AWS para verificar permisos:
  - `athena:StartQueryExecution`
  - `athena:GetQueryResults`
  - `s3:GetObject` en `direct-put-rey-s3-v2`
  - `s3:PutObject` en `athena-results/`
  - `glue:GetDatabase`
  - `glue:GetTable`

---

### Problema 5: Query muy lenta (>30 segundos)

**Posibles causas:**
- Primera consulta del día (Athena "warming up")
- Muchos archivos pequeños en S3
- Sin particiones utilizadas

**Solución:**
```sql
-- Agregar filtros de partición para acelerar
SELECT COUNT(*)
FROM rey_db_v3.rey_table_only_v2
WHERE year = '2024'
  AND month = '08'
  AND day = '15'
```

---

## PASO 11: EVIDENCIA PARA REPORTE

### Documentación Requerida

Para cada consulta validada, documentar:

1. **Captura de Pantalla** que muestre:
   - [ ] Consulta SQL completa en editor
   - [ ] Resultados en tabla
   - [ ] Status: SUCCEEDED (verde)
   - [ ] Run time y Data scanned
   - [ ] Database y tabla seleccionados
   - [ ] Timestamp de ejecución

2. **Archivo CSV Descargado**:
   - [ ] `Query_1_results.csv`
   - [ ] `Query_2_results.csv`

3. **Query Execution IDs**:
   - Consulta 1: `_______________________________`
   - Consulta 2: `_______________________________`

4. **Métricas de Rendimiento**:

| Métrica | Consulta 1 | Consulta 2 |
|---------|-----------|-----------|
| Run time (segundos) | | |
| Data scanned (GB) | | |
| Rows returned | | |
| Status | | |

---

## COMANDOS EQUIVALENTES EN AWS CLI

Si prefieres usar CLI en lugar de console:

### Ejecutar Consulta 1 (CLI):
```bash
aws athena start-query-execution \
  --region us-west-2 \
  --profile E2i-dairel-760135066147 \
  --query-string "SELECT COUNT(*) as total_records, COUNT(DISTINCT device_id) as unique_devices, MIN(timestamp) as first_record_timestamp, MAX(timestamp) as last_record_timestamp FROM rey_db_v3.rey_table_only_v2" \
  --result-configuration "OutputLocation=s3://direct-put-rey-s3-v2/athena-results/" \
  --query-execution-context "Database=rey_db_v3"
```

### Obtener Resultados (CLI):
```bash
# Copiar QueryExecutionId del resultado anterior
QUERY_ID="PEGAR_AQUI_EL_ID"

# Esperar 10 segundos
sleep 10

# Obtener resultados
aws athena get-query-results \
  --region us-west-2 \
  --profile E2i-dairel-760135066147 \
  --query-execution-id $QUERY_ID
```

---

## RESUMEN DE ÉXITO

Si completaste todos los pasos, deberías tener:

✅ **2 consultas Athena ejecutadas exitosamente**
✅ **Resultados validados:**
   - Consulta 1: ~132M registros totales
   - Consulta 2: 2 dispositivos con RPM ~1335-1374

✅ **Evidencia recopilada:**
   - 2 capturas de pantalla
   - 2 archivos CSV (opcional)
   - Query Execution IDs anotados
   - Métricas de rendimiento documentadas

✅ **Conocimiento adquirido:**
   - Cómo usar Athena Query Editor
   - Cómo validar consultas SQL
   - Cómo interpretar resultados
   - Cómo solucionar problemas comunes

---

## SIGUIENTE PASO

Con estas consultas validadas, puedes:
1. Crear dashboards en Amazon QuickSight
2. Automatizar reportes con AWS Lambda + Athena
3. Exportar datos para análisis en Python/Pandas
4. Crear alertas basadas en umbrales (ej: RPM > 1500)
5. Integrar con herramientas BI externas (Tableau, Power BI)

---

**Documento Creado:** 5 de Marzo de 2026
**Propósito:** Guía práctica para validar consultas Athena en AWS Console
**Nivel:** Principiante a Intermedio
**Tiempo Estimado:** 15-20 minutos
**Costo Estimado:** $0.02 - $0.03 USD
