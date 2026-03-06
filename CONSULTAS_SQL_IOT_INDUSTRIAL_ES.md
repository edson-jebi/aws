# Análisis de Datos IoT Industrial - Catálogo de Consultas SQL

**Industrias:** Minería, Pasteurización, Monitoreo de Equipos Industriales
**Fuentes de Datos:** AWS Timestream (Tiempo Real) y AWS Athena/S3 (Histórico)
**Fecha:** 4 de Marzo de 2026

---

## Resumen Ejecutivo

Este documento proporciona 15 consultas SQL estándar de la industria para analizar datos IoT de múltiples dispositivos industriales incluyendo:
- **Delice** (Equipo de pasteurización)
- **FESA_C15** (Equipo minero)
- **Shovel** (Equipo de excavación)
- **HVE** (Equipo de vehículos pesados)
- **Chinalco** (Operaciones mineras)

Las consultas cubren tanto el **monitoreo operacional en tiempo real** (Timestream) como el **análisis de tendencias históricas** (Athena/S3 Data Lake).

---

## Descripción General de Fuentes de Datos

### Datos en Tiempo Real (AWS Timestream)
- **Base de Datos:** `E2iDB`
- **Tablas:**
  - `DeliceTableTimestream` - Equipo de pasteurización
  - `FESA_C15` - Equipo minero
  - `Shovel` - Equipo de excavación
  - `HVE` - Equipo de vehículos pesados
  - `Chinalco` - Operaciones mineras
- **Frecuencia de Actualización:** Casi en tiempo real (segundos)
- **Retención:** Configurable (predeterminado: 30 días a 1 año)

### Datos Históricos (AWS Athena + S3)
- **Base de Datos:** `delice_db_v1`
- **Tablas:**
  - `delice_table_v1` - Datos históricos de Delice (formato Parquet)
- **Almacenamiento:** S3 Data Lake
- **Formato:** Apache Parquet (comprimido, columnar)
- **Retención:** Largo plazo (años)

---

## Categorías de Consultas

1. **Monitoreo en Tiempo Real** (Consultas 1-5) - Timestream
2. **Análisis Histórico** (Consultas 6-10) - Athena
3. **Comparaciones Entre Dispositivos** (Consultas 11-12) - Timestream
4. **Datos Crudos vs Procesados** (Consultas 13-15) - Ambas fuentes

---

# PARTE 1: MONITOREO EN TIEMPO REAL (Timestream)

## Consulta 1: Tiempo de Actividad de Equipos - Últimas 24 Horas

**Pregunta de Negocio:** "¿Cuál es el estado operacional actual y el porcentaje de tiempo de actividad de todas las unidades de pasteurización Delice en las últimas 24 horas?"

**Caso de Uso:** Panel de operaciones, monitoreo de SLA en tiempo real

**Consulta SQL (Timestream):**
```sql
SELECT
    device_ID,
    COUNT(*) as total_lecturas,
    SUM(CASE WHEN status_main = 1 THEN 1 ELSE 0 END) as lecturas_operacionales,
    ROUND(
        CAST(SUM(CASE WHEN status_main = 1 THEN 1 ELSE 0 END) AS DOUBLE) /
        CAST(COUNT(*) AS DOUBLE) * 100,
        2
    ) as porcentaje_actividad,
    MAX(time) as ultima_lectura
FROM "E2iDB"."DeliceTableTimestream"
WHERE time > ago(24h)
GROUP BY device_ID
ORDER BY porcentaje_actividad DESC
```

**Salida Esperada:**
```
device_ID         | total_lecturas | lecturas_operacionales | porcentaje_actividad | ultima_lectura
------------------|----------------|------------------------|---------------------|------------------
DELICE_PLANT_01   | 43200         | 42890                  | 99.28               | 2026-03-04 23:15:00
DELICE_PLANT_02   | 43200         | 41500                  | 96.07               | 2026-03-04 23:14:58
```

---

## Consulta 2: Alertas de Temperatura Crítica - Tiempo Real

**Pregunta de Negocio:** "¿Qué unidades de pasteurización tienen actualmente lecturas de temperatura fuera de rangos operativos seguros?"

**Caso de Uso:** Monitoreo de seguridad, alertas inmediatas, control de calidad

**Consulta SQL (Timestream):**
```sql
SELECT
    device_ID,
    time,
    temp_process_1,
    temp_process_2,
    temp_process_3,
    heating_set_point,
    CASE
        WHEN temp_process_1 < 65 THEN 'CRÍTICO: Por debajo del umbral de pasteurización'
        WHEN temp_process_1 > 100 THEN 'CRÍTICO: Riesgo de sobrecalentamiento'
        WHEN ABS(temp_process_1 - heating_set_point) > 5 THEN 'ADVERTENCIA: Desviación del punto de ajuste'
        ELSE 'NORMAL'
    END as estado_alerta
FROM "E2iDB"."DeliceTableTimestream"
WHERE time > ago(15m)
  AND (
      temp_process_1 < 65 OR
      temp_process_1 > 100 OR
      ABS(temp_process_1 - heating_set_point) > 5
  )
ORDER BY time DESC
```

**Estándar de la Industria:** Crítico para el cumplimiento HACCP en procesamiento de alimentos

---

## Consulta 3: Comparación de Rendimiento Entre Equipos

**Pregunta de Negocio:** "Comparar la eficiencia operacional actual entre diferentes tipos de equipos (Delice, FESA, Shovel) en la última hora"

**Caso de Uso:** Operaciones multi-sitio, gestión de flotas

**Consulta SQL (Timestream):**
```sql
-- Equipo Delice
SELECT
    'Delice' as tipo_equipo,
    COUNT(DISTINCT device_ID) as unidades_activas,
    AVG(temp_process_1) as temp_proceso_promedio,
    SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as conteo_alarmas,
    MAX(time) as ultima_actualizacion
FROM "E2iDB"."DeliceTableTimestream"
WHERE time > ago(1h)

UNION ALL

-- Equipo Minero FESA
SELECT
    'FESA_C15' as tipo_equipo,
    COUNT(DISTINCT device_ID) as unidades_activas,
    NULL as temp_proceso_promedio,
    SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as conteo_alarmas,
    MAX(time) as ultima_actualizacion
FROM "E2iDB"."FESA_C15"
WHERE time > ago(1h)

UNION ALL

-- Equipo Shovel
SELECT
    'Shovel' as tipo_equipo,
    COUNT(DISTINCT device_ID) as unidades_activas,
    NULL as temp_proceso_promedio,
    SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as conteo_alarmas,
    MAX(time) as ultima_actualizacion
FROM "E2iDB"."Shovel"
WHERE time > ago(1h)

ORDER BY tipo_equipo
```

---

## Consulta 4: Mantenimiento Predictivo - Detección de Anomalías en Sensores

**Pregunta de Negocio:** "Identificar equipos que muestran comportamiento anormal de sensores que puede indicar falla inminente"

**Caso de Uso:** Mantenimiento predictivo, reducir tiempo de inactividad no planificado

**Consulta SQL (Timestream):**
```sql
WITH estadisticas_recientes AS (
    SELECT
        device_ID,
        AVG(temp_process_1) as temp_promedio,
        STDDEV(temp_process_1) as desviacion_temp,
        MAX(temp_process_1) as temp_maxima,
        MIN(temp_process_1) as temp_minima,
        COUNT(*) as conteo_lecturas
    FROM "E2iDB"."DeliceTableTimestream"
    WHERE time > ago(6h)
    GROUP BY device_ID
)
SELECT
    device_ID,
    temp_promedio,
    desviacion_temp,
    temp_maxima - temp_minima as rango_temperatura,
    CASE
        WHEN desviacion_temp > 10 THEN 'ALTA VARIANZA - Verificar calibración de sensor'
        WHEN temp_maxima - temp_minima > 30 THEN 'FLUCTUACIÓN EXCESIVA - Posible problema de control'
        WHEN conteo_lecturas < 1000 THEN 'BAJA FRECUENCIA DE DATOS - Problema de conectividad'
        ELSE 'NORMAL'
    END as bandera_mantenimiento
FROM estadisticas_recientes
WHERE
    desviacion_temp > 10 OR
    (temp_maxima - temp_minima) > 30 OR
    conteo_lecturas < 1000
ORDER BY desviacion_temp DESC
```

**Contexto Industrial:** Reduce el tiempo de inactividad no planificado en 30-40% (Gartner)

---

## Consulta 5: Tasa de Producción - Rendimiento en Tiempo Real

**Pregunta de Negocio:** "¿Cuál es el rendimiento de producción actual y la tasa de consumo de agua en todas las líneas de pasteurización activas?"

**Caso de Uso:** Planificación de producción, optimización de recursos

**Consulta SQL (Timestream):**
```sql
SELECT
    device_ID,
    bin(time, 5m) as ventana_tiempo,
    COUNT(*) as ciclos_por_5min,
    AVG(water_flow_lph) as flujo_agua_promedio,
    SUM(water_flow_lph) / 12.0 as litros_totales_por_5min,
    AVG(temp_process_1) as temp_proceso_promedio,
    SUM(CASE WHEN product_pump_state = 1 THEN 1 ELSE 0 END) as conteo_bomba_activa
FROM "E2iDB"."DeliceTableTimestream"
WHERE time > ago(1h)
  AND status_main = 1
GROUP BY device_ID, bin(time, 5m)
ORDER BY ventana_tiempo DESC, device_ID
```

---

# PARTE 2: ANÁLISIS HISTÓRICO (Athena / S3 Data Lake)

## Consulta 6: Reporte de Cumplimiento de Temperatura a Largo Plazo

**Pregunta de Negocio:** "Generar un reporte de cumplimiento de 90 días mostrando adherencia a estándares regulatorios de temperatura de pasteurización"

**Caso de Uso:** Auditorías regulatorias, aseguramiento de calidad, documentación HACCP

**Consulta SQL (Athena):**
```sql
SELECT
    DATE(from_unixtime(timestamp)) as fecha,
    COUNT(*) as registros_totales,

    -- Métricas de cumplimiento de temperatura
    SUM(CASE WHEN temp_process_1 >= 72 AND temp_process_1 <= 95 THEN 1 ELSE 0 END) as registros_conformes,
    SUM(CASE WHEN temp_process_1 < 72 THEN 1 ELSE 0 END) as bajo_umbral,
    SUM(CASE WHEN temp_process_1 > 95 THEN 1 ELSE 0 END) as sobre_umbral,

    -- Cálculos de porcentaje
    ROUND(
        CAST(SUM(CASE WHEN temp_process_1 >= 72 AND temp_process_1 <= 95 THEN 1 ELSE 0 END) AS DOUBLE) /
        CAST(COUNT(*) AS DOUBLE) * 100,
        2
    ) as porcentaje_cumplimiento,

    -- Estadísticas de temperatura
    ROUND(AVG(temp_process_1), 2) as temp_promedio,
    ROUND(MIN(temp_process_1), 2) as temp_minima,
    ROUND(MAX(temp_process_1), 2) as temp_maxima,
    ROUND(STDDEV(temp_process_1), 2) as desviacion_estandar_temp,

    -- Estado regulatorio
    CASE
        WHEN CAST(SUM(CASE WHEN temp_process_1 >= 72 THEN 1 ELSE 0 END) AS DOUBLE) / CAST(COUNT(*) AS DOUBLE) >= 0.99
        THEN 'APROBADO - Cumplimiento +99%'
        WHEN CAST(SUM(CASE WHEN temp_process_1 >= 72 THEN 1 ELSE 0 END) AS DOUBLE) / CAST(COUNT(*) AS DOUBLE) >= 0.95
        THEN 'MARGINAL - Cumplimiento 95-99%'
        ELSE 'REPROBADO - Cumplimiento <95%'
    END as estado_regulatorio

FROM delice_db_v1.delice_table_v1
WHERE from_unixtime(timestamp) >= CURRENT_DATE - INTERVAL '90' DAY
GROUP BY DATE(from_unixtime(timestamp))
ORDER BY fecha DESC
```

**Estándar de Cumplimiento:** La FDA requiere 72°C por 15 segundos (pasteurización HTST)

---

## Consulta 7: Análisis de Ciclo de Vida del Equipo - Degradación Histórica

**Pregunta de Negocio:** "Analizar la degradación del rendimiento del equipo a lo largo del tiempo para planificar ventanas de mantenimiento y reemplazos"

**Caso de Uso:** Planificación de capital, programación de mantenimiento

**Consulta SQL (Athena):**
```sql
WITH rendimiento_mensual AS (
    SELECT
        device_id,
        DATE_TRUNC('month', from_unixtime(timestamp)) as mes,

        -- Métricas operacionales
        COUNT(*) as operaciones_totales,
        AVG(temp_process_1) as temp_promedio,
        STDDEV(temp_process_1) as varianza_temp,

        -- Indicadores de eficiencia
        AVG(CAST(temp_process_1 - heating_set_point AS DOUBLE)) as error_temp_promedio,
        AVG(steam_valve_opening) as uso_vapor_promedio,
        AVG(pump_frequency) as frecuencia_bomba_promedio,

        -- Indicadores de falla
        SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as conteo_alarmas,
        SUM(CASE WHEN emergency_stop = 1 THEN 1 ELSE 0 END) as paradas_emergencia

    FROM delice_db_v1.delice_table_v1
    WHERE from_unixtime(timestamp) >= DATE_TRUNC('year', CURRENT_DATE)
    GROUP BY device_id, DATE_TRUNC('month', from_unixtime(timestamp))
)
SELECT
    device_id,
    mes,
    temp_promedio,
    varianza_temp,
    error_temp_promedio,
    uso_vapor_promedio,
    conteo_alarmas,

    -- Indicadores de degradación
    uso_vapor_promedio - LAG(uso_vapor_promedio) OVER (PARTITION BY device_id ORDER BY mes) as aumento_uso_vapor,
    varianza_temp - LAG(varianza_temp) OVER (PARTITION BY device_id ORDER BY mes) as aumento_varianza,

    -- Puntuación de salud (0-100)
    ROUND(
        100 -
        (varianza_temp * 2) -
        (conteo_alarmas * 0.5) -
        (ABS(error_temp_promedio) * 3),
        2
    ) as puntuacion_salud_equipo

FROM rendimiento_mensual
ORDER BY device_id, mes DESC
```

---

## Consulta 8: Análisis de Consumo de Agua y Costos

**Pregunta de Negocio:** "Calcular el consumo total de agua y costos estimados por lote de producción durante el último trimestre"

**Caso de Uso:** Optimización de costos, reportes de sustentabilidad

**Consulta SQL (Athena):**
```sql
SELECT
    DATE_TRUNC('week', from_unixtime(timestamp)) as semana,
    device_id,

    -- Consumo de agua
    SUM(water_flow_lph) / 60.0 as litros_totales,
    SUM(water_flow_lph) / 60.0 / 1000.0 as metros_cubicos_totales,

    -- Métricas de producción
    COUNT(*) as horas_operacion,
    SUM(CASE WHEN heating_mode = 1 THEN 1 ELSE 0 END) as horas_calentamiento,
    SUM(CASE WHEN cooling_mode = 1 THEN 1 ELSE 0 END) as horas_enfriamiento,
    SUM(CASE WHEN cleaning_mode = 1 THEN 1 ELSE 0 END) as horas_limpieza,

    -- Cálculos de costo (tasa ejemplo: $2 por metro cúbico)
    ROUND(SUM(water_flow_lph) / 60.0 / 1000.0 * 2.0, 2) as costo_agua_estimado_usd,

    -- Métricas de eficiencia
    ROUND(
        SUM(water_flow_lph) / 60.0 /
        NULLIF(SUM(CASE WHEN heating_mode = 1 THEN 1 ELSE 0 END), 0),
        2
    ) as litros_por_hora_produccion

FROM delice_db_v1.delice_table_v1
WHERE from_unixtime(timestamp) >= CURRENT_DATE - INTERVAL '90' DAY
  AND water_flow_lph > 0
GROUP BY DATE_TRUNC('week', from_unixtime(timestamp)), device_id
ORDER BY semana DESC, device_id
```

**Referencia Industrial:** El procesamiento de alimentos usa 2-10 litros por kg de producto

---

## Consulta 9: Efectividad de Ciclos de Limpieza - Tendencias Históricas

**Pregunta de Negocio:** "Analizar frecuencia, duración y efectividad de ciclos de limpieza a lo largo del tiempo para optimizar programas CIP (Clean-In-Place)"

**Caso de Uso:** Cumplimiento de saneamiento, eficiencia operacional

**Consulta SQL (Athena):**
```sql
WITH ciclos_limpieza AS (
    SELECT
        device_id,
        from_unixtime(timestamp) as tiempo_evento,
        DATE(from_unixtime(timestamp)) as fecha,
        cleaning_mode,
        detergent_concentration,
        temp_water_1 as temp_limpieza,
        water_flow_lph,

        -- Detectar inicios de ciclo
        CASE
            WHEN cleaning_mode = 1 AND
                 LAG(cleaning_mode, 1, 0) OVER (PARTITION BY device_id ORDER BY timestamp) = 0
            THEN 1
            ELSE 0
        END as inicio_ciclo

    FROM delice_db_v1.delice_table_v1
    WHERE from_unixtime(timestamp) >= CURRENT_DATE - INTERVAL '30' DAY
),
resumen_ciclos AS (
    SELECT
        device_id,
        fecha,
        SUM(inicio_ciclo) as ciclos_limpieza,
        AVG(CASE WHEN cleaning_mode = 1 THEN detergent_concentration END) as detergente_promedio_pct,
        AVG(CASE WHEN cleaning_mode = 1 THEN temp_limpieza END) as temp_limpieza_promedio,
        SUM(CASE WHEN cleaning_mode = 1 THEN 1 ELSE 0 END) as lecturas_duracion_limpieza
    FROM ciclos_limpieza
    GROUP BY device_id, fecha
)
SELECT
    device_id,
    fecha,
    ciclos_limpieza,
    lecturas_duracion_limpieza / 60 as duracion_estimada_horas,
    detergente_promedio_pct,
    temp_limpieza_promedio,

    -- Puntuación de efectividad (0-100)
    ROUND(
        (CASE
            WHEN temp_limpieza_promedio >= 75 THEN 40
            WHEN temp_limpieza_promedio >= 65 THEN 30
            ELSE 15
        END) +
        (CASE
            WHEN detergente_promedio_pct BETWEEN 2.0 AND 3.0 THEN 40
            WHEN detergente_promedio_pct BETWEEN 1.5 AND 3.5 THEN 30
            ELSE 15
        END) +
        (CASE
            WHEN ciclos_limpieza >= 1 THEN 20
            ELSE 0
        END),
        2
    ) as puntuacion_efectividad_limpieza,

    -- Estado de cumplimiento
    CASE
        WHEN ciclos_limpieza = 0 THEN 'NO CONFORME: Sin limpieza'
        WHEN temp_limpieza_promedio < 65 THEN 'NO CONFORME: Temperatura baja'
        WHEN detergente_promedio_pct < 1.5 THEN 'NO CONFORME: Detergente bajo'
        ELSE 'CONFORME'
    END as cumplimiento_saneamiento

FROM resumen_ciclos
ORDER BY fecha DESC, device_id
```

**Requisito FDA:** Limpieza diaria para superficies en contacto con alimentos

---

## Consulta 10: Análisis de Patrones de Consumo Energético

**Pregunta de Negocio:** "Identificar períodos de consumo energético máximo y oportunidades para cambio de carga para reducir costos de electricidad"

**Caso de Uso:** Gestión energética, reducción de costos

**Consulta SQL (Athena):**
```sql
SELECT
    HOUR(from_unixtime(timestamp)) as hora_del_dia,
    DATE_TRUNC('day', from_unixtime(timestamp)) as fecha,

    -- Métricas proxy de energía (valores más altos = más energía)
    COUNT(*) as conteo_operaciones,
    SUM(CASE WHEN heating_mode = 1 THEN 1 ELSE 0 END) as operaciones_calentamiento,
    SUM(CASE WHEN cooling_mode = 1 THEN 1 ELSE 0 END) as operaciones_enfriamiento,

    AVG(steam_valve_opening) as valvula_vapor_promedio,
    AVG(pump_frequency) as frecuencia_bomba_promedio,

    -- Índice de intensidad energética (0-100)
    ROUND(
        (AVG(steam_valve_opening) * 0.5) +
        (AVG(pump_frequency) * 0.3) +
        (CAST(SUM(CASE WHEN heating_mode = 1 THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*) * 20),
        2
    ) as indice_intensidad_energia,

    -- Implicaciones de costo (ejemplo: $0.15/kWh pico, $0.08/kWh valle)
    CASE
        WHEN HOUR(from_unixtime(timestamp)) BETWEEN 7 AND 22 THEN 'TARIFA PICO ($0.15/kWh)'
        ELSE 'TARIFA VALLE ($0.08/kWh)'
    END as periodo_tarifa_electrica

FROM delice_db_v1.delice_table_v1
WHERE from_unixtime(timestamp) >= CURRENT_DATE - INTERVAL '30' DAY
GROUP BY HOUR(from_unixtime(timestamp)), DATE_TRUNC('day', from_unixtime(timestamp))
ORDER BY fecha DESC, hora_del_dia
```

**Oportunidad de Optimización:** El cambio de carga puede reducir costos energéticos en 20-40%

---

# PARTE 3: ANÁLISIS ENTRE DISPOSITIVOS Y FLOTAS

## Consulta 11: Panel Operacional Multi-Equipo

**Pregunta de Negocio:** "Crear un panel operacional unificado mostrando el estado actual de todos los tipos de equipos en la instalación"

**Caso de Uso:** Monitoreo central de operaciones, panel ejecutivo

**Consulta SQL (Timestream - Multi-tabla):**
```sql
-- Unidades de Pasteurización Delice
SELECT
    'DELICE' as categoria_equipo,
    device_ID as id_equipo,
    time as ultima_actualizacion,
    'temp_process_1' as nombre_metrica_principal,
    temp_process_1 as valor_metrica_principal,
    status_main as estado_operacional,
    alarm_active as tiene_alarma
FROM "E2iDB"."DeliceTableTimestream"
WHERE time > ago(5m)
  AND time = (SELECT MAX(time) FROM "E2iDB"."DeliceTableTimestream" WHERE device_ID = device_ID)

UNION ALL

-- Equipo Minero FESA
SELECT
    'FESA_MINERO' as categoria_equipo,
    device_ID as id_equipo,
    time as ultima_actualizacion,
    'engine_temp' as nombre_metrica_principal,
    engine_temp as valor_metrica_principal,
    operational_status as estado_operacional,
    alarm_active as tiene_alarma
FROM "E2iDB"."FESA_C15"
WHERE time > ago(5m)
  AND time = (SELECT MAX(time) FROM "E2iDB"."FESA_C15" WHERE device_ID = device_ID)

UNION ALL

-- Equipo Shovel
SELECT
    'SHOVEL' as categoria_equipo,
    device_ID as id_equipo,
    time as ultima_actualizacion,
    'hydraulic_pressure' as nombre_metrica_principal,
    hydraulic_pressure as valor_metrica_principal,
    operational_status as estado_operacional,
    alarm_active as tiene_alarma
FROM "E2iDB"."Shovel"
WHERE time > ago(5m)
  AND time = (SELECT MAX(time) FROM "E2iDB"."Shovel" WHERE device_ID = device_ID)

ORDER BY categoria_equipo, id_equipo
```

---

## Consulta 12: Correlación de Fallas Entre Equipos

**Pregunta de Negocio:** "Identificar si las fallas en un tipo de equipo se correlacionan con problemas en otros equipos (ej. problemas de red eléctrica afectando múltiples sistemas)"

**Caso de Uso:** Análisis de causa raíz, monitoreo de infraestructura

**Consulta SQL (Timestream - Correlación basada en tiempo):**
```sql
WITH alarmas_delice AS (
    SELECT
        bin(time, 1m) as periodo_tiempo,
        COUNT(*) as conteo_alarmas_delice
    FROM "E2iDB"."DeliceTableTimestream"
    WHERE time > ago(24h)
      AND alarm_active = 1
    GROUP BY bin(time, 1m)
),
alarmas_fesa AS (
    SELECT
        bin(time, 1m) as periodo_tiempo,
        COUNT(*) as conteo_alarmas_fesa
    FROM "E2iDB"."FESA_C15"
    WHERE time > ago(24h)
      AND alarm_active = 1
    GROUP BY bin(time, 1m)
),
alarmas_shovel AS (
    SELECT
        bin(time, 1m) as periodo_tiempo,
        COUNT(*) as conteo_alarmas_shovel
    FROM "E2iDB"."Shovel"
    WHERE time > ago(24h)
      AND alarm_active = 1
    GROUP BY bin(time, 1m)
)
SELECT
    COALESCE(d.periodo_tiempo, f.periodo_tiempo, s.periodo_tiempo) as periodo_tiempo,
    COALESCE(d.conteo_alarmas_delice, 0) as alarmas_delice,
    COALESCE(f.conteo_alarmas_fesa, 0) as alarmas_fesa,
    COALESCE(s.conteo_alarmas_shovel, 0) as alarmas_shovel,

    -- Bandera de correlación
    CASE
        WHEN COALESCE(d.conteo_alarmas_delice, 0) > 0 AND
             COALESCE(f.conteo_alarmas_fesa, 0) > 0 AND
             COALESCE(s.conteo_alarmas_shovel, 0) > 0
        THEN 'PROBLEMA EN TODA LA INSTALACIÓN'
        WHEN (COALESCE(d.conteo_alarmas_delice, 0) > 0 AND COALESCE(f.conteo_alarmas_fesa, 0) > 0) OR
             (COALESCE(f.conteo_alarmas_fesa, 0) > 0 AND COALESCE(s.conteo_alarmas_shovel, 0) > 0) OR
             (COALESCE(d.conteo_alarmas_delice, 0) > 0 AND COALESCE(s.conteo_alarmas_shovel, 0) > 0)
        THEN 'ALARMAS CORRELACIONADAS'
        ELSE 'ALARMA AISLADA'
    END as estado_correlacion

FROM alarmas_delice d
FULL OUTER JOIN alarmas_fesa f ON d.periodo_tiempo = f.periodo_tiempo
FULL OUTER JOIN alarmas_shovel s ON d.periodo_tiempo = s.periodo_tiempo
WHERE COALESCE(d.conteo_alarmas_delice, 0) > 0 OR
      COALESCE(f.conteo_alarmas_fesa, 0) > 0 OR
      COALESCE(s.conteo_alarmas_shovel, 0) > 0
ORDER BY periodo_tiempo DESC
```

**Caso de Uso:** Detecta cortes de energía, problemas de red, factores ambientales

---

# PARTE 4: ANÁLISIS DE DATOS CRUDOS vs PROCESADOS

## Consulta 13: Comparación de Calidad de Datos - Timestream Crudo vs S3 Procesado

**Pregunta de Negocio:** "Comparar completitud y calidad de datos entre datos crudos en tiempo real y data lake histórico procesado"

**Caso de Uso:** Validación de pipeline de datos, monitoreo ETL

**Consulta SQL (Timestream):**
```sql
-- Calidad de Datos Crudos - Últimas 24h
SELECT
    'TIMESTREAM_CRUDO' as fuente_datos,
    COUNT(*) as registros_totales,
    COUNT(DISTINCT device_ID) as dispositivos_unicos,

    -- Métricas de completitud
    ROUND(COUNT(temp_process_1) * 100.0 / COUNT(*), 2) as completitud_temp_pct,
    ROUND(COUNT(water_flow_lph) * 100.0 / COUNT(*), 2) as completitud_flujo_pct,
    ROUND(COUNT(mqtt_topic) * 100.0 / COUNT(*), 2) as completitud_topic_pct,

    -- Frescura de datos
    MAX(time) as registro_mas_reciente,
    date_diff('second', MAX(time), current_time) as segundos_desde_ultima_actualizacion,

    -- Detección de anomalías
    SUM(CASE WHEN temp_process_1 IS NULL THEN 1 ELSE 0 END) as registros_temp_faltante,
    SUM(CASE WHEN temp_process_1 < 0 OR temp_process_1 > 150 THEN 1 ELSE 0 END) as temps_fuera_rango

FROM "E2iDB"."DeliceTableTimestream"
WHERE time > ago(24h)
```

**Consulta SQL (Athena):**
```sql
-- Calidad de Datos Procesados - Últimas 24h
SELECT
    'S3_PROCESADO' as fuente_datos,
    COUNT(*) as registros_totales,
    COUNT(DISTINCT device_id) as dispositivos_unicos,

    -- Métricas de completitud
    ROUND(CAST(COUNT(temp_process_1) AS DOUBLE) * 100.0 / COUNT(*), 2) as completitud_temp_pct,
    ROUND(CAST(COUNT(water_flow_lph) AS DOUBLE) * 100.0 / COUNT(*), 2) as completitud_flujo_pct,
    ROUND(CAST(COUNT(mqtt_topic) AS DOUBLE) * 100.0 / COUNT(*), 2) as completitud_topic_pct,

    -- Frescura de datos
    MAX(from_unixtime(timestamp)) as registro_mas_reciente,
    date_diff('second', MAX(from_unixtime(timestamp)), CURRENT_TIMESTAMP) as segundos_desde_ultima_actualizacion,

    -- Detección de anomalías
    SUM(CASE WHEN temp_process_1 IS NULL THEN 1 ELSE 0 END) as registros_temp_faltante,
    SUM(CASE WHEN temp_process_1 < 0 OR temp_process_1 > 150 THEN 1 ELSE 0 END) as temps_fuera_rango

FROM delice_db_v1.delice_table_v1
WHERE from_unixtime(timestamp) >= CURRENT_TIMESTAMP - INTERVAL '24' HOUR
```

**Resultado Esperado:** Ambas deben mostrar completitud >99%; identificar pérdida de datos en pipeline

---

## Consulta 14: Rendimiento Agregado - Datos Crudos vs Pre-Agregados

**Pregunta de Negocio:** "Comparar rendimiento de consultas entre consultar datos crudos vs tablas pre-agregadas para reportes"

**Caso de Uso:** Optimización de consultas, evaluación de vistas materializadas

**Opción A: Consultar Datos Crudos (Más lento pero flexible)**
```sql
-- Athena en Parquet crudo
SELECT
    DATE(from_unixtime(timestamp)) as fecha,
    device_id,
    COUNT(*) as registros,
    AVG(temp_process_1) as temp_promedio,
    MAX(temp_process_1) as temp_maxima,
    MIN(temp_process_1) as temp_minima,
    STDDEV(temp_process_1) as desviacion_temp,
    SUM(water_flow_lph) / 60.0 as litros_totales
FROM delice_db_v1.delice_table_v1
WHERE from_unixtime(timestamp) >= DATE '2026-01-01'
GROUP BY DATE(from_unixtime(timestamp)), device_id
ORDER BY fecha DESC, device_id
```

**Opción B: Crear Tabla Pre-Agregada (Recomendado para consultas frecuentes)**
```sql
-- CTAS (Create Table As Select) - Ejecutar una vez al día
CREATE TABLE delice_db_v1.resumen_diario_delice
WITH (
    format = 'PARQUET',
    external_location = 's3://delice-datalake-parquet/aggregated/daily/',
    partitioned_by = ARRAY['anio', 'mes']
) AS
SELECT
    YEAR(from_unixtime(timestamp)) as anio,
    MONTH(from_unixtime(timestamp)) as mes,
    DATE(from_unixtime(timestamp)) as fecha,
    device_id,

    -- Métricas pre-calculadas
    COUNT(*) as conteo_registros,
    AVG(temp_process_1) as temp_promedio,
    MAX(temp_process_1) as temp_maxima,
    MIN(temp_process_1) as temp_minima,
    STDDEV(temp_process_1) as desviacion_temp,
    SUM(water_flow_lph) / 60.0 as litros_agua_totales,
    SUM(CASE WHEN alarm_active = 1 THEN 1 ELSE 0 END) as conteo_alarmas,
    SUM(CASE WHEN cleaning_mode = 1 THEN 1 ELSE 0 END) as horas_limpieza

FROM delice_db_v1.delice_table_v1
GROUP BY
    YEAR(from_unixtime(timestamp)),
    MONTH(from_unixtime(timestamp)),
    DATE(from_unixtime(timestamp)),
    device_id
```

**Luego consultar tabla agregada (10-100x más rápido):**
```sql
SELECT * FROM delice_db_v1.resumen_diario_delice
WHERE anio = 2026 AND mes = 3
ORDER BY fecha DESC
```

**Ganancia de Rendimiento:** Las consultas agregadas son 10-100x más rápidas para grandes conjuntos de datos

---

## Consulta 15: Validación de Pipeline de Datos de Extremo a Extremo

**Pregunta de Negocio:** "Validar la consistencia de datos a través de todo el pipeline desde el dispositivo hasta el data lake"

**Caso de Uso:** Gobernanza de datos, pista de auditoría, verificación de salud del pipeline

**Paso 1: Verificar Datos Crudos en Timestream**
```sql
-- Timestream: Ingesta cruda desde dispositivos
SELECT
    'PASO_1_DISPOSITIVO_A_TIMESTREAM' as etapa_pipeline,
    DATE(time) as fecha,
    COUNT(*) as conteo_registros,
    COUNT(DISTINCT device_ID) as conteo_dispositivos,
    MIN(time) as registro_mas_antiguo,
    MAX(time) as registro_mas_reciente
FROM "E2iDB"."DeliceTableTimestream"
WHERE time >= current_date - INTERVAL '7' DAY
GROUP BY DATE(time)
ORDER BY fecha DESC
```

**Paso 2: Verificar Aterrizaje en S3 de Firehose (JSON Crudo)**
```bash
# Verificar zona de aterrizaje cruda en S3 (si está habilitada)
aws s3 ls s3://delice-datalake-raw/2026/03/ --recursive --human-readable --summarize
```

**Paso 3: Verificar Data Lake Procesado en Parquet**
```sql
-- Athena: Datos procesados en S3 Data Lake
SELECT
    'PASO_3_DATA_LAKE_PROCESADO' as etapa_pipeline,
    DATE(from_unixtime(timestamp)) as fecha,
    COUNT(*) as conteo_registros,
    COUNT(DISTINCT device_id) as conteo_dispositivos,
    MIN(from_unixtime(timestamp)) as registro_mas_antiguo,
    MAX(from_unixtime(timestamp)) as registro_mas_reciente,

    -- Metadata de archivos
    COUNT(DISTINCT "$path") as conteo_archivos_parquet

FROM delice_db_v1.delice_table_v1
WHERE from_unixtime(timestamp) >= CURRENT_DATE - INTERVAL '7' DAY
GROUP BY DATE(from_unixtime(timestamp))
ORDER BY fecha DESC
```

**Paso 4: Comparar Conteos de Registros (Detección de Pérdida de Datos)**
```sql
-- Esperado: Registros Timestream ≈ Registros S3 (dentro del 1-2%)
WITH conteos_timestream AS (
    SELECT DATE(time) as fecha, COUNT(*) as conteo_ts
    FROM "E2iDB"."DeliceTableTimestream"
    WHERE time >= current_date - INTERVAL '7' DAY
    GROUP BY DATE(time)
),
conteos_s3 AS (
    SELECT DATE(from_unixtime(timestamp)) as fecha, COUNT(*) as conteo_s3
    FROM delice_db_v1.delice_table_v1
    WHERE from_unixtime(timestamp) >= CURRENT_DATE - INTERVAL '7' DAY
    GROUP BY DATE(from_unixtime(timestamp))
)
SELECT
    COALESCE(ts.fecha, s3.fecha) as fecha,
    COALESCE(ts.conteo_ts, 0) as registros_timestream,
    COALESCE(s3.conteo_s3, 0) as registros_datalake_s3,
    COALESCE(ts.conteo_ts, 0) - COALESCE(s3.conteo_s3, 0) as diferencia_registros,
    ROUND(
        ABS(COALESCE(ts.conteo_ts, 0) - COALESCE(s3.conteo_s3, 0)) * 100.0 /
        NULLIF(COALESCE(ts.conteo_ts, 1), 0),
        2
    ) as porcentaje_diferencia,

    CASE
        WHEN ABS(COALESCE(ts.conteo_ts, 0) - COALESCE(s3.conteo_s3, 0)) * 100.0 /
             NULLIF(COALESCE(ts.conteo_ts, 1), 0) < 2.0
        THEN 'SALUDABLE - Diferencia <2%'
        WHEN ABS(COALESCE(ts.conteo_ts, 0) - COALESCE(s3.conteo_s3, 0)) * 100.0 /
             NULLIF(COALESCE(ts.conteo_ts, 1), 0) < 5.0
        THEN 'ADVERTENCIA - Pérdida de datos 2-5%'
        ELSE 'CRÍTICO - Pérdida de datos >5%'
    END as salud_pipeline

FROM conteos_timestream ts
FULL OUTER JOIN conteos_s3 s3 ON ts.fecha = s3.fecha
ORDER BY fecha DESC
```

**SLA:** La pérdida de datos debe ser <1% para pipelines de producción

---

# APÉNDICE: Consejos de Optimización de Consultas

## Optimización de Timestream

1. **Usar filtros de tiempo agresivamente** - Siempre filtrar con `WHERE time > ago(Xh)`
2. **Agregaciones en bins** - Usar `bin(time, 5m)` para agrupación de series temporales
3. **Limitar resultados** - Agregar cláusula `LIMIT` para consultas exploratorias
4. **Filtro de medidas** - Filtrar medidas específicas temprano en la consulta

## Optimización de Athena/S3

1. **Poda de particiones** - Siempre filtrar en columnas de partición (fecha/hora)
2. **Usar Parquet** - Formato columnar reduce escaneo en 80-90%
3. **CTAS para agregaciones** - Pre-agregar datos consultados frecuentemente
4. **Limitar proyecciones** - Solo SELECT las columnas que necesitas
5. **Evitar comodines** - Especificar nombres de columnas explícitos

---

# Resumen

Este documento proporciona **15 consultas SQL listas para producción** cubriendo:

✅ **Monitoreo en tiempo real** (Timestream) - Consultas 1-5
✅ **Análisis histórico** (Athena) - Consultas 6-10
✅ **Perspectivas entre dispositivos** - Consultas 11-12
✅ **Validación de calidad de datos** - Consultas 13-15

**Industrias Cubiertas:**
- Alimentos y Bebidas (Pasteurización)
- Minería y Excavación
- Manufactura de Equipo Pesado
- IoT Industrial General

**Estándares de Cumplimiento:**
- Ley de Modernización de Seguridad Alimentaria de la FDA (FSMA)
- Puntos Críticos de Control HACCP
- Gestión de Seguridad Alimentaria ISO 22000
- Regulaciones de seguridad minera

---

**Versión del Documento:** 1.0
**Última Actualización:** 4 de Marzo de 2026
**Autor:** Equipo de Análisis de Datos E2i
**Para:** Monitoreo de operaciones IoT multi-industria
