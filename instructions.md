# Prueba Técnica - Data Engineer

## Codeable Labs - Evaluación Técnica Integral

## Información General

La prueba técnica tiene una duración de 2 días (48 horas desde la recepción)

### Objetivo:
- Evaluar competencias clave en ingeniería de datos, modelado, procesamiento, infraestructura cloud y buenas prácticas.

### Entregables:
- Repositorio en GitHub (público o privado). Cada tarea completada debe ser registrada con un commit específico. Tiene que tener toda la documentación necesaria, un README y las dependencias en requirements.txt
- Presentación corta (15-20 min) explicando tu solución en una videollamada a agendar.

### El objetivo es observar:
- Cómo priorizas y gestionas tu tiempo
- Tu capacidad para tomar decisiones técnicas estratégicas
- La profundidad de tu conocimiento en las áreas que dominas
- Tu proceso de pensamiento y metodología de trabajo

### Se valorará mucho más:
- La calidad y profesionalismo en las fases que completes
- Una implementación parcial bien ejecutada sobre una completa pero superficial
- La claridad en explicar qué quedó pendiente y por qué

## NOTA IMPORTANTE SOBRE LA PRUEBA

Esta evaluación está diseñada intencionalmente para NO ser completada en su totalidad. No te preocupes si no llegas a todas las fases. Concéntrate en demostrar excelencia en lo que implementes.

## Contexto del Problema

Eres el Data Engineer de una fintech latinoamericana que procesa transacciones de pago. La empresa necesita construir un sistema de datos end-to-end que procese transacciones en tiempo real y permita análisis posteriores.

## Fases del Proyecto

### Fase 1: Data Lake - Ingesta de Datos
**Objetivo:** Configurar el almacenamiento de datos crudos (Data Lake)

**Tareas:**
- Utilizar la carpeta `./transactions` como Data Lake local para archivos CSV generados automáticamente
- Los datos son generados cada minuto por el script `main.py` proporcionado

**Puntos Extra:** Implementar MinIO como Data Lake compatible con S3 en lugar de carpeta local

---

### Fase 2: ETL Pipeline - Limpieza y Detección de Fraude
**Objetivo:** Completar las funciones en `main.py` para procesar transacciones en tiempo real

**Comportamiento esperado:**
- El script `main.py` genera transacciones cada 60 segundos
- Lee los CSV del Data Lake (carpeta `./transactions`)
- Limpia los datos usando tu implementación de `clean_data()`
- Detecta fraudes usando tu implementación de `detect_suspicious_transactions()`
- Guarda resultados en carpetas `./processed/` y `./suspicious/`

1. **Función `clean_data(df)`:**
   - Manejar valores nulos/faltantes
   - Eliminar duplicados
   - Validar tipos de datos
   - Manejar outliers en amounts
   - Estandarizar formatos (códigos de país, currencies)

   **Puntos Extra:** Transformar currencies mediante API en vez de valores fijos.

2. **Función `detect_suspicious_transactions(df)`:**
   - Detectar montos inusualmente altos
   - Identificar múltiples intentos fallidos del mismo usuario
   - Flaggear transacciones declined con códigos de seguridad
   - Detectar patrones anómalos
   - Identificar transacciones internacionales de alto riesgo
   - Retornar tupla: (df_normal, df_suspicious)

   **Puntos Extra:** Orquestar el pipeline ETL con Apache Airflow en lugar de ejecutarlo solo por consola

---

### Fase 3: Data Warehouse - Modelado y Almacenamiento
**Objetivo:** Diseñar e implementar un modelo dimensional para análisis

**Tareas:**
- Diseñar schema dimensional (star/snowflake) para transacciones
- Crear tablas en PostgreSQL (dimensiones y hechos)
- Implementar script de carga desde `./processed` hacia PostgreSQL
- Documentar el modelo de datos

**Tablas sugeridas:**
- `fact_transactions` - tabla de hechos
- `dim_users` - dimensión usuarios
- `dim_merchants` - dimensión comercios
- `dim_time` - dimensión temporal
- `dim_payment_methods` - dimensión métodos de pago

**Puntos Extra:** Dockerizar PostgreSQL con docker-compose para facilitar el setup

---

### Fase 4: Procesamiento en Tiempo Real
**Objetivo:** Diseñar un sistema de procesamiento de datos en tiempo real usando **Apache Kafka** para detectar y analizar transacciones sospechosas de forma continua. Documenta y justifica tu decisión basándote en el caso de uso de detección de fraude en una fintech.

**Documentar tareas para:**
- Configurar Apache Kafka.
- Configurar Producer: Enviar transacciones sospechosas detectadas en `main.py` a un topic de Kafka
- Configurar Consumer: Consumir mensajes y generar alertas o métricas en tiempo real
- Calcular estadísticas por minuto (número de fraudes, montos totales sospechosos)

**Puntos Extra:** Implementar el diseño de esta fase y procesar los datos en tiempo real

---

## Evaluación

Tu implementación y repositorio serán evaluados según:

1. **Calidad de limpieza de datos:**
   - Manejo apropiado de valores nulos
   - Eliminación efectiva de duplicados
   - Validaciones de datos robustas
   - Transformaciones correctas

2. **Detección de fraude:**
   - Criterios de detección bien fundamentados
   - Lógica clara y mantenible
   - Cobertura de múltiples patrones sospechosos
   - Balance entre falsos positivos y detección efectiva

3. **Código y documentación:**
   - Código limpio y bien comentado
   - Manejo de errores
   - Eficiencia en procesamiento
   - Documentación de decisiones tomadas

## Checklist Antes de Entregar

Antes de enviar tu solución, verifica:

- Repositorio GitHub accesible con permisos correctos
- README.md completo (instrucciones de setup, resumen, fases completadas, tiempo invertido, trabajo pendiente)
- Commits descriptivos por cada tarea completada
- Código ejecutable (incluir instrucciones de entorno)
- requirements.txt actualizado
- Al menos 1 diagrama de arquitectura
- Tests básicos si aplica

Recuerda: Esta prueba está diseñada para ser desafiante. Muéstranos cómo piensas, cómo priorizas y la calidad de tu trabajo. Eso es lo que realmente importa.

---

¡Mucho éxito! Queremos ver tu mejor trabajo.

**Codeable Labs - 2025**
