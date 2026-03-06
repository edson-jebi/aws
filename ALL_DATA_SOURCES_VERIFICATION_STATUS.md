# Estado de Verificación de Todas las Fuentes de Datos IoT

**Fecha:** 5 de Marzo de 2026
**Objetivo:** Verificar esquemas y consultas SQL para TODAS las fuentes de datos en E2iDB

---

## RESUMEN EJECUTIVO

| Tabla | Estado | Registros Verificados | Industria | Próxima Acción |
|-------|--------|----------------------|-----------|----------------|
| **DeliceTableTimestream** | ✅ **COMPLETADO** | 44.7M registros | Pasteurización | Ninguna - 17 consultas verificadas |
| **FESA_C15** | ⏳ **PENDIENTE** | Por verificar | Minería | Requiere credenciales AWS |
| **Shovel** | ⏳ **PENDIENTE** | Por verificar | Excavación | Requiere credenciales AWS |
| **HVE** | ⏳ **PENDIENTE** | Por verificar | Vehículos Pesados | Requiere credenciales AWS |
| **Chinalco** | ⏳ **PENDIENTE** | Por verificar | Operaciones Mineras | Requiere credenciales AWS |

---

## ✅ COMPLETADO: DeliceTableTimestream

### Dispositivos Identificados:
- **Andino_X1_P01** (dispositivo principal)
- Último mensaje: 4 de Marzo 2026, 11:50:05 AM
- Frecuencia normal: 3.6 mensajes/segundo (~13,000/hora)

### Medidas Confirmadas (14 métricas):
```
Temperaturas:
✓ temp_process_1, temp_process_2, temp_process_3
✓ temp_water_1
✓ heating_set_point, cooling_set_point

Control de Válvulas:
✓ grid_valve_opening
✓ steam_valve_opening

Bombas:
✓ pump_frequency
✓ product_pump_state
✓ water_pump_state

Estados:
✓ status_main
✓ status_product

Flujo:
✓ water_flow_lph

Otros:
✓ detergent_concentration
```

### Consultas Verificadas:
- ✅ 17 consultas SQL probadas con datos reales
- ✅ Documentadas en: `VERIFIED_SQL_QUERIES_REAL_DATA.md`
- ✅ Incluye: tiempo real, histórico, y Athena

---

## ⏳ PENDIENTE: Verificación de Otras Tablas

### Procedimiento de Verificación (Para Ejecutar con Credenciales AWS)

#### Paso 1: Verificar si la Tabla Tiene Datos Recientes

```bash
# FESA_C15
aws timestream-query query \
  --region us-west-2 \
  --profile E2i-dairel-760135066147 \
  --query-string "SELECT COUNT(*) as total FROM \"E2iDB\".\"FESA_C15\" WHERE time > ago(24h)"

# Shovel
aws timestream-query query \
  --region us-west-2 \
  --profile E2i-dairel-760135066147 \
  --query-string "SELECT COUNT(*) as total FROM \"E2iDB\".\"Shovel\" WHERE time > ago(24h)"

# HVE
aws timestream-query query \
  --region us-west-2 \
  --profile E2i-dairel-760135066147 \
  --query-string "SELECT COUNT(*) as total FROM \"E2iDB\".\"HVE\" WHERE time > ago(24h)"

# Chinalco
aws timestream-query query \
  --region us-west-2 \
  --profile E2i-dairel-760135066147 \
  --query-string "SELECT COUNT(*) as total FROM \"E2iDB\".\"Chinalco\" WHERE time > ago(24h)"
```

#### Paso 2: Obtener Lista de Medidas Disponibles

```bash
# Para cada tabla con datos, obtener medidas
aws timestream-query query \
  --region us-west-2 \
  --profile E2i-dairel-760135066147 \
  --query-string "
    SELECT
      measure_name,
      COUNT(*) as frecuencia,
      MAX(time) as ultima_actualizacion
    FROM \"E2iDB\".\"FESA_C15\"
    WHERE time > ago(24h)
    GROUP BY measure_name
    ORDER BY frecuencia DESC
    LIMIT 50
  "
```

#### Paso 3: Identificar Dispositivos Activos

```bash
aws timestream-query query \
  --region us-west-2 \
  --profile E2i-dairel-760135066147 \
  --query-string "
    SELECT
      device_ID,
      COUNT(*) as registros,
      MIN(time) as primera_lectura,
      MAX(time) as ultima_lectura
    FROM \"E2iDB\".\"FESA_C15\"
    WHERE time > ago(24h)
    GROUP BY device_ID
    ORDER BY registros DESC
  "
```

#### Paso 4: Obtener Muestra de Datos

```bash
aws timestream-query query \
  --region us-west-2 \
  --profile E2i-dairel-760135066147 \
  --query-string "
    SELECT
      device_ID,
      time,
      measure_name,
      measure_value::bigint,
      measure_value::double,
      measure_value::varchar
    FROM \"E2iDB\".\"FESA_C15\"
    WHERE time > ago(1h)
    LIMIT 100
  "
```

---

## ESTRUCTURA ESPERADA DE DATOS

Todas las tablas Timestream deberían seguir este modelo:

```
Columnas Fijas:
- device_ID (varchar)      - Identificador del dispositivo
- Machine (varchar)        - Nombre de la máquina (opcional)
- time (timestamp)         - Marca de tiempo
- measure_name (varchar)   - Nombre de la métrica
- measure_value::double    - Valor numérico decimal
- measure_value::bigint    - Valor numérico entero
- measure_value::varchar   - Valor texto
- measure_value::boolean   - Valor booleano
```

### Ejemplo de Consulta Genérica para Cualquier Tabla:

```sql
-- Obtener dashboard de última hora para cualquier tabla
SELECT
    device_ID,
    measure_name,
    COUNT(*) as num_lecturas,
    AVG(measure_value::double) as valor_promedio,
    MIN(measure_value::double) as valor_minimo,
    MAX(measure_value::double) as valor_maxima,
    MAX(time) as ultima_actualizacion
FROM "E2iDB"."[NOMBRE_TABLA]"
WHERE time > ago(1h)
  AND measure_value::double IS NOT NULL
GROUP BY device_ID, measure_name
ORDER BY device_ID, num_lecturas DESC
```

---

## CONSULTAS TIPO PARA VERIFICAR CADA TABLA

### 1. Verificación Básica de Conectividad

```sql
SELECT
    COUNT(*) as total_registros,
    COUNT(DISTINCT device_ID) as dispositivos,
    MIN(time) as primer_registro,
    MAX(time) as ultimo_registro,
    date_diff('hour', MIN(time), MAX(time)) as horas_de_datos
FROM "E2iDB"."[TABLA]"
WHERE time > ago(7d)
```

### 2. Catálogo de Medidas

```sql
SELECT
    measure_name,
    COUNT(*) as frecuencia,
    COUNT(DISTINCT device_ID) as dispositivos_que_envian,
    MAX(time) as ultima_vez_enviado
FROM "E2iDB"."[TABLA]"
WHERE time > ago(24h)
GROUP BY measure_name
ORDER BY frecuencia DESC
```

### 3. Actividad por Dispositivo

```sql
SELECT
    device_ID,
    COUNT(*) as registros_ultima_hora,
    COUNT(DISTINCT measure_name) as metricas_distintas,
    MAX(time) as ultima_actividad,
    date_diff('minute', MAX(time), current_time) as minutos_desde_ultima_actividad
FROM "E2iDB"."[TABLA]"
WHERE time > ago(1h)
GROUP BY device_ID
ORDER BY registros_ultima_hora DESC
```

### 4. Detección de Tipos de Datos

```sql
SELECT
    measure_name,
    COUNT(CASE WHEN measure_value::double IS NOT NULL THEN 1 END) as tiene_double,
    COUNT(CASE WHEN measure_value::bigint IS NOT NULL THEN 1 END) as tiene_bigint,
    COUNT(CASE WHEN measure_value::varchar IS NOT NULL THEN 1 END) as tiene_varchar,
    COUNT(CASE WHEN measure_value::boolean IS NOT NULL THEN 1 END) as tiene_boolean
FROM "E2iDB"."[TABLA]"
WHERE time > ago(1h)
GROUP BY measure_name
ORDER BY measure_name
```

---

## INDUSTRIAS Y MÉTRICAS ESPERADAS

### FESA_C15 (Minería)
**Métricas Esperadas:**
- Presión hidráulica
- RPM de motor
- Temperatura de aceite
- Nivel de combustible
- Horas de operación
- Alarmas de sistema

### Shovel (Excavación)
**Métricas Esperadas:**
- Posición de brazo/balde
- Carga de trabajo
- Consumo de energía
- Ciclos de excavación
- Vibraciones
- Estado de frenos

### HVE (Heavy Vehicle Equipment)
**Métricas Esperadas:**
- Velocidad del vehículo
- GPS (latitud/longitud)
- Consumo de combustible
- Temperatura de motor
- Presión de neumáticos
- Estado de transmisión

### Chinalco (Operaciones Mineras)
**Métricas Esperadas:**
- Producción (toneladas)
- Nivel de tolvas
- Velocidad de cintas transportadoras
- Calidad de mineral
- Vibraciones de equipos
- Contadores de ciclos

---

## PLANTILLA PARA DOCUMENTAR CADA TABLA

Cuando se verifique cada tabla, documentar usando esta plantilla:

```markdown
## [NOMBRE_TABLA]

### Información Básica
- **Industria:** [Minería/Excavación/Transporte]
- **Dispositivos Activos:** [Lista de device_IDs]
- **Último Mensaje:** [Fecha y hora]
- **Frecuencia de Datos:** [Mensajes/segundo o mensajes/hora]
- **Periodo Analizado:** [Rango de fechas]

### Medidas Disponibles (Top 20)
| measure_name | Tipo | Frecuencia | Descripción |
|--------------|------|------------|-------------|
| [nombre] | double | 5000/hora | [qué mide] |

### Consultas Verificadas
1. **[Título]**
   - Pregunta: [En lenguaje natural]
   - SQL: [Consulta verificada]
   - Resultado: [Descripción de salida]

### Alertas y Umbrales Recomendados
- [Métrica]: Umbral [valor] - [razón]

### Notas Especiales
- [Cualquier comportamiento único o patrones observados]
```

---

## SCRIPTS DE AUTOMATIZACIÓN

### Script Bash para Verificar Todas las Tablas

```bash
#!/bin/bash
# verify_all_tables.sh

REGION="us-west-2"
PROFILE="E2i-dairel-760135066147"
DATABASE="E2iDB"
TABLES=("FESA_C15" "Shovel" "HVE" "Chinalco")

for TABLE in "${TABLES[@]}"; do
    echo "========================================="
    echo "Verificando: $TABLE"
    echo "========================================="

    # Conteo de registros últimas 24h
    echo "1. Registros últimas 24 horas:"
    aws timestream-query query \
        --region $REGION \
        --profile $PROFILE \
        --query-string "SELECT COUNT(*) as total FROM \"$DATABASE\".\"$TABLE\" WHERE time > ago(24h)"

    # Dispositivos activos
    echo "2. Dispositivos activos:"
    aws timestream-query query \
        --region $REGION \
        --profile $PROFILE \
        --query-string "SELECT device_ID, COUNT(*) as registros FROM \"$DATABASE\".\"$TABLE\" WHERE time > ago(24h) GROUP BY device_ID"

    # Medidas disponibles
    echo "3. Medidas disponibles (top 20):"
    aws timestream-query query \
        --region $REGION \
        --profile $PROFILE \
        --query-string "SELECT measure_name, COUNT(*) as freq FROM \"$DATABASE\".\"$TABLE\" WHERE time > ago(24h) GROUP BY measure_name ORDER BY freq DESC LIMIT 20"

    echo ""
done
```

### Python Script para Análisis Detallado

```python
#!/usr/bin/env python3
# analyze_timestream_table.py

import boto3
import json
from datetime import datetime

def analyze_table(database, table):
    client = boto3.client('timestream-query', region_name='us-west-2')

    queries = {
        'record_count': f'SELECT COUNT(*) as total FROM "{database}"."{table}" WHERE time > ago(24h)',
        'devices': f'SELECT device_ID, COUNT(*) as records FROM "{database}"."{table}" WHERE time > ago(24h) GROUP BY device_ID',
        'measures': f'SELECT measure_name, COUNT(*) as freq FROM "{database}"."{table}" WHERE time > ago(24h) GROUP BY measure_name ORDER BY freq DESC LIMIT 50',
        'sample': f'SELECT * FROM "{database}"."{table}" WHERE time > ago(1h) LIMIT 100'
    }

    results = {}
    for key, query in queries.items():
        try:
            response = client.query(QueryString=query)
            results[key] = response['Rows']
        except Exception as e:
            results[key] = f"Error: {str(e)}"

    return results

if __name__ == "__main__":
    tables = ["FESA_C15", "Shovel", "HVE", "Chinalco"]
    database = "E2iDB"

    for table in tables:
        print(f"\n{'='*60}")
        print(f"Analyzing: {table}")
        print('='*60)
        results = analyze_table(database, table)
        print(json.dumps(results, indent=2, default=str))
```

---

## PRÓXIMOS PASOS INMEDIATOS

### Cuando Credenciales AWS Estén Disponibles:

1. **Ejecutar Verificación de Conectividad** (5 minutos)
   ```bash
   ./verify_all_tables.sh > table_verification_results.txt
   ```

2. **Analizar Resultados** (10 minutos)
   - Identificar qué tablas tienen datos recientes
   - Listar dispositivos activos en cada tabla
   - Catalogar medidas disponibles

3. **Crear Consultas Verificadas** (30 minutos por tabla)
   - Usar plantilla de consultas tipo
   - Probar con datos reales
   - Documentar resultados

4. **Generar Reporte Final** (20 minutos)
   - Consolidar todos los hallazgos
   - Crear catálogo completo de consultas
   - Traducir a español si es necesario

### Total Estimado: 2-3 horas de trabajo

---

## ENTREGABLES FINALES ESPERADOS

1. ✅ `VERIFIED_SQL_QUERIES_REAL_DATA.md` - **COMPLETADO** (DeliceTableTimestream)
2. ⏳ `FESA_C15_VERIFIED_QUERIES.md` - PENDIENTE
3. ⏳ `SHOVEL_VERIFIED_QUERIES.md` - PENDIENTE
4. ⏳ `HVE_VERIFIED_QUERIES.md` - PENDIENTE
5. ⏳ `CHINALCO_VERIFIED_QUERIES.md` - PENDIENTE
6. ⏳ `ALL_SOURCES_SQL_CATALOG.md` - Catálogo consolidado - PENDIENTE

---

## LECCIONES APRENDIDAS DE DELICETABLETIMESTREAM

### ✅ Qué Funcionó Bien:
1. Identificar estructura measure-based antes de crear consultas
2. Probar consultas con datos reales para verificar sintaxis
3. Documentar tipos de datos (::double, ::bigint, ::varchar)
4. Usar funciones de agregación con CASE WHEN para múltiples métricas

### ❌ Errores a Evitar:
1. NO asumir estructura columnar tradicional
2. NO usar `SELECT column1, column2` directamente
3. NO olvidar especificar tipo de measure_value (::double, ::bigint)
4. NO crear consultas sin verificar que las medidas existen

### 💡 Tips para Verificación Rápida:
1. Siempre empezar con `SELECT COUNT(*)` para verificar datos
2. Usar `LIMIT 10` en consultas de prueba
3. Verificar `MAX(time)` para confirmar datos recientes
4. Listar `measure_name` disponibles antes de crear consultas complejas

---

## CONTACTO Y MANTENIMIENTO

**Documento Creado:** 5 de Marzo de 2026
**Última Actualización:** 5 de Marzo de 2026
**Estado:** DeliceTableTimestream verificado, otras tablas pendientes de credenciales AWS
**Mantenedor:** Equipo E2i Analytics
**Próxima Revisión:** Cuando se obtengan credenciales AWS

---

## REFERENCIAS

- AWS Timestream SQL Reference: https://docs.aws.amazon.com/timestream/latest/developerguide/sql-reference.html
- Consultas Verificadas Delice: `VERIFIED_SQL_QUERIES_REAL_DATA.md`
- Documentación Original: `INDUSTRIAL_IOT_SQL_QUERIES_REPORT.md`
- Guía Athena: `DELICE_ATHENA_GUIDE.md`
