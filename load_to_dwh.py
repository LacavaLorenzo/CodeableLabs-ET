import pandas as pd
import s3fs
from sqlalchemy import create_engine, text
from io import StringIO
import warnings

# Ignoramos warnings que no son críticos para esta prueba
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# ===================================================
# 1. CONFIGURACIÓN DE CONEXIONES
# ===================================================

# (Copiada de main.py)
MINIO_STORAGE_OPTIONS = {
    "key": "minioadmin",
    "secret": "minioadminpassword",
    "client_kwargs": {"endpoint_url": "http://localhost:9000"}
}

# (Copiada del notebook)
DB_URL = "postgresql://user:password@localhost:5432/fintech_db"

PROCESSED_BUCKET = "processed"

# ===================================================
# 2. FUNCIÓN "UPSERT" (INSERT ON CONFLICT)
# ===================================================
def upsert_to_db(df, engine, table_name, conflict_key):
    """
    Inserta/Actualiza un DataFrame en una tabla de PostgreSQL.
    Usa 'ON CONFLICT DO NOTHING' para evitar duplicados (Idempotencia).
    """
    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False, sep='\t', na_rep='\\N')
    buffer.seek(0)
    
    if isinstance(conflict_key, list):
        conflict_cols_sql = ", ".join(conflict_key)
    else:
        conflict_cols_sql = conflict_key
        
    # [CORRECCIÓN] Convertimos la lista de columnas del DF en un string SQL
    df_cols_sql = ", ".join(df.columns)
        
    with engine.connect() as conn:
        with conn.begin(): 
            conn.execute(text(f"CREATE TEMP TABLE temp_table ON COMMIT DROP AS SELECT * FROM {table_name} WITH NO DATA;"))
            
            raw_conn = conn.connection.driver_connection
            with raw_conn.cursor() as cur:
                # El 'copy_from' es inteligente y solo llena las columnas que le pasamos
                cur.copy_from(buffer, 'temp_table', sep='\t', columns=df.columns)
            
            # [CORRECCIÓN] Ahora el INSERT y el SELECT especifican las MISMAS columnas
            conn.execute(text(f"""
                INSERT INTO {table_name} ({df_cols_sql})
                SELECT {df_cols_sql} FROM temp_table
                ON CONFLICT ({conflict_cols_sql}) DO NOTHING;
            """))

# ===================================================
# 3. FUNCIÓN PRINCIPAL DEL ETL
# ===================================================
def main():
    print("--- Iniciando script de carga al Data Warehouse (Fase 3) ---")
    
    try:
        # 1. Conectarse a la infraestructura (MinIO y Postgres)
        engine = create_engine(DB_URL)
        fs = s3fs.S3FileSystem(**MINIO_STORAGE_OPTIONS)
        print("Conectado a PostgreSQL y MinIO.")
    except Exception as e:
        print(f"ERROR: No se pudo conectar a la infraestructura: {e}")
        return

    # 2. Encontrar todos los archivos en el bucket 'processed'
    s3_files = fs.glob(f"{PROCESSED_BUCKET}/processed_*.csv")
    if not s3_files:
        print("No se encontraron archivos nuevos en el bucket 'processed'. Saliendo.")
        return
        
    print(f"Se encontraron {len(s3_files)} archivos para procesar.")

    for file_path in s3_files:
        print(f"\nProcesando archivo: {file_path}...")
        try:
            # --- E: EXTRAER ---
            with fs.open(file_path) as f:
                df = pd.read_csv(f)
            
            # Convertimos las columnas de fecha (se leen como texto)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # --- T/L: TRANSFORMAR Y CARGAR DIMENSIONES ---
            
            # 1. dim_time
            print("Cargando 'dim_time'...")
            df_dim_time = pd.DataFrame({
                'full_timestamp': df['timestamp'].drop_duplicates(),
            })
            df_dim_time['time_key'] = df_dim_time['full_timestamp'].dt.strftime('%Y%m%d%H').astype(int)
            df_dim_time['date'] = df_dim_time['full_timestamp'].dt.date
            df_dim_time['year'] = df_dim_time['full_timestamp'].dt.year
            df_dim_time['quarter'] = df_dim_time['full_timestamp'].dt.quarter
            df_dim_time['month'] = df_dim_time['full_timestamp'].dt.month
            df_dim_time['day'] = df_dim_time['full_timestamp'].dt.day
            df_dim_time['hour'] = df_dim_time['full_timestamp'].dt.hour
            df_dim_time['day_of_week'] = df_dim_time['full_timestamp'].dt.dayofweek
            # Reordenamos para que coincida con la tabla
            df_dim_time = df_dim_time[['time_key', 'full_timestamp', 'date', 'year', 'quarter', 'month', 'day', 'hour', 'day_of_week']].drop_duplicates('time_key')
            upsert_to_db(df_dim_time, engine, 'dim_time', 'time_key')

            # 2. dim_users
            print("Cargando 'dim_users'...")
            df_dim_users = df[['user_id', 'country', 'device_type']].drop_duplicates('user_id')
            upsert_to_db(df_dim_users, engine, 'dim_users', 'user_id')
            
            # 3. dim_merchants
            print("Cargando 'dim_merchants'...")
            df_dim_merchants = df[['merchant_id', 'category']].drop_duplicates('merchant_id')
            # Nota: 'merchant_name' no está en el archivo de transacciones, se cargará como Nulo.
            upsert_to_db(df_dim_merchants, engine, 'dim_merchants', 'merchant_id')

            # 4. dim_payment_methods
            print("Cargando 'dim_payment_methods'...")
            df_dim_pm = df[['payment_method', 'payment_provider']].drop_duplicates()
            upsert_to_db(df_dim_pm, engine, 'dim_payment_methods', ['payment_method', 'payment_provider'])
            
            # --- T/L: TRANSFORMAR Y CARGAR TABLA DE HECHOS (FACT) ---
            print("Transformando 'fact_transactions'...")
            
            # 1. Leer las claves (keys) de las dimensiones que acabamos de cargar
            # Esto es para hacer el "mapeo" de ID de negocio a Clave de DWH
            df_keys_time = pd.read_sql("SELECT time_key, full_timestamp FROM dim_time", engine)
            df_keys_users = pd.read_sql("SELECT user_key, user_id FROM dim_users", engine)
            df_keys_merchants = pd.read_sql("SELECT merchant_key, merchant_id FROM dim_merchants", engine)
            df_keys_pm = pd.read_sql("SELECT payment_method_key, payment_method, payment_provider FROM dim_payment_methods", engine)

            # 2. Unir (merge) las claves de vuelta al DataFrame principal
            df_fact = df.merge(df_keys_time, left_on='timestamp', right_on='full_timestamp', how='left')
            df_fact = df_fact.merge(df_keys_users, on='user_id', how='left')
            df_fact = df_fact.merge(df_keys_merchants, on='merchant_id', how='left')
            df_fact = df_fact.merge(df_keys_pm, on=['payment_method', 'payment_provider'], how='left')

            key_columns = ['time_key', 'user_key', 'merchant_key', 'payment_method_key']
            for col in key_columns:
                # Usamos .astype('Int64') que maneja nulos (NaN)
                df_fact[col] = df_fact[col].astype('Int64')

            # 3. Seleccionar las columnas finales para la tabla de hechos
            fact_columns = [
                'transaction_id', 'time_key', 'user_key', 'merchant_key', 'payment_method_key',
                'amount', 'transaction_fee', 'net_amount', 'installments', 'processing_time_ms',
                'attempt_number', 'status', 'response_code', 'response_message', 'is_international'
            ]
            df_fact_final = df_fact[fact_columns].drop_duplicates('transaction_id')

            # 4. Cargar la tabla de hechos
            print("Cargando 'fact_transactions'...")
            upsert_to_db(df_fact_final, engine, 'fact_transactions', 'transaction_id')

            print(f"¡Éxito! Archivo {file_path} cargado en el Data Warehouse.")
            
            # Opcional (Buena práctica): Mover el archivo procesado a un bucket 'archive'
            # fs.move(file_path, f"archive/{file_path.split('/')[-1]}")
            # print(f"Archivo movido a 'archive'.")

        except Exception as e:
            print(f"ERROR: No se pudo procesar el archivo {file_path}: {e}")
            # Opcional (Buena práctica): Mover el archivo fallido a un bucket 'failed'
            # fs.move(file_path, f"failed/{file_path.split('/')[-1]}")

    print("\n--- Proceso de carga al DWH completado ---")

if __name__ == "__main__":
    main()