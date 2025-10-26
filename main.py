"""
Main ETL Pipeline for Transaction Processing

This script runs continuously, generating fake transactions every minute
and processing them through a data pipeline.

TODO: Complete the following functions:
1. clean_data() - Clean and validate the raw transaction data
2. detect_suspicious_transactions() - Identify potentially fraudulent transactions
"""

import time
import pandas as pd
from datetime import datetime
from pathlib import Path
from scripts.generate_transactions import generate_transactions
import s3fs  # [CAMBIO] Importamos la librería para S3
import warnings


# [CAMBIO] Usamos nombres de buckets en lugar de carpetas
TRANSACTIONS_BUCKET = "transactions"
PROCESSED_BUCKET = "processed"
SUSPICIOUS_BUCKET = "suspicious"

# [CAMBIO] Configuración de S3 (MinIO)
# s3fs (y pandas) esperan 'key' y 'secret' como argumentos directos,
# y 'endpoint_url' debe ir dentro de 'client_kwargs'.
MINIO_STORAGE_OPTIONS = {
    "key": "minioadmin",
    "secret": "minioadminpassword",
    "client_kwargs": {"endpoint_url": "http://localhost:9000"}
}
# [CAMBIO] Creamos un sistema de archivos S3
# Usamos ** para desempaquetar el diccionario (key=..., secret=..., client_kwargs=...)
fs = s3fs.S3FileSystem(**MINIO_STORAGE_OPTIONS)

INTERVAL_SECONDS = 60  # Generar transacciones cada 1 minuto
TRANSACTIONS_PER_BATCH = 100  # Número de transacciones a generar cada vez

# Ignoramos warnings de S3FS y Pandas que no son críticos
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', message=".*deprecated.*")


def setup_folders():
    """Create necessary folders if they don't exist"""
    TRANSACTIONS_FOLDER.mkdir(exist_ok=True)
    PROCESSED_FOLDER.mkdir(exist_ok=True)
    SUSPICIOUS_FOLDER.mkdir(exist_ok=True)
    print(f"Folders initialized:")
    print(f"  - Data Lake: {TRANSACTIONS_FOLDER}")
    print(f"  - Processed: {PROCESSED_FOLDER}")
    print(f"  - Suspicious: {SUSPICIOUS_FOLDER}")


def setup_minio_buckets():
    """
    [CAMBIO] Verifica y crea buckets en MinIO si no existen
    """
    print("--- Configurando Infraestructura (MinIO) ---")
    try:
        for bucket in [TRANSACTIONS_BUCKET, PROCESSED_BUCKET, SUSPICIOUS_BUCKET]:
            if not fs.exists(bucket):
                fs.mkdir(bucket)
                print(f"Bucket '{bucket}' creado en MinIO.")
            else:
                print(f"Bucket '{bucket}' ya existe.")
        print("Buckets de MinIO configurados correctamente.")
    except Exception as e:
        print(f"ERROR: No se pudo conectar o crear buckets en MinIO: {e}")
        print("Asegúrate de que el contenedor Docker de MinIO ('fintech_minio') esté corriendo.")
        raise e


def generate_batch():
    """
    [CAMBIO] Genera un lote de transacciones y lo guarda en MinIO
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # [CAMBIO] Definimos la ruta del archivo en S3
    s3_path = f"{TRANSACTIONS_BUCKET}/transactions_{timestamp}.csv"
    
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Generating {TRANSACTIONS_PER_BATCH} transactions...")
    df = generate_transactions(TRANSACTIONS_PER_BATCH)
    
    try:
        # [CAMBIO] Escribimos el CSV directamente a S3 (MinIO)
        with fs.open(s3_path, 'w') as f:
            df.to_csv(f, index=False)
            
        print(f"Saved to S3 Data Lake: s3://{s3_path}")
        return s3_path # Devolvemos la ruta S3
        
    except Exception as e:
        print(f"ERROR: No se pudo escribir en el bucket S3 '{TRANSACTIONS_BUCKET}': {e}")
        return None


def clean_data(df):
    """
    TODO: Implement data cleaning logic

    Clean and validate the transaction data. Consider:
    - Handling missing values
    - Removing duplicates
    - Data type validation
    - Standardizing formats
    - Handling outliers

    Args:
        df (pd.DataFrame): Raw transaction data

    Returns:
        pd.DataFrame: Cleaned transaction data
    """
    """
    Limpia y valida los datos crudos de transacciones.
    
    Aplica las siguientes reglas basadas en el análisis EDA (EDA_Limpieza_Fraude.ipynb):
    - Elimina duplicados basados en 'transaction_id'.
    - Rellena valores nulos (NaN) en 'three_ds_verified' (como False) e 'ip_address' (como 'Unknown').
    - Convierte 'timestamp' y 'settlement_date' a formato datetime.
    - Asegura que 'three_ds_verified' e 'is_international' sean booleanos.
    - Estandariza formatos de texto (mayúsculas/minúsculas) para consistencia.
    """
    try:
        df_clean = df.copy()
        df_clean.drop_duplicates(subset=['transaction_id'], keep='first', inplace=True)
        df_clean['three_ds_verified'] = df_clean['three_ds_verified'].fillna(False)
        df_clean['ip_address'] = df_clean['ip_address'].fillna('Unknown')
        df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'])
        df_clean['settlement_date'] = pd.to_datetime(df_clean['settlement_date'], errors='coerce')
        df_clean['three_ds_verified'] = df_clean['three_ds_verified'].astype(bool)
        df_clean['is_international'] = df_clean['is_international'].astype(bool)
        text_cols_to_lower = ['status', 'payment_method', 'category', 'device_type']
        text_cols_to_upper = ['currency', 'country']
        for col in text_cols_to_lower:
            if col in df_clean.columns: df_clean[col] = df_clean[col].str.lower()
        for col in text_cols_to_upper:
            if col in df_clean.columns: df_clean[col] = df_clean[col].str.upper()
        df_clean['amount'] = df_clean['amount'].abs()
        return df_clean
    except Exception as e:
        print(f"ERROR: Error durante la limpieza de datos: {e}")
        return pd.DataFrame(columns=df.columns)


def detect_suspicious_transactions(df):
    """
    TODO: Implement fraud detection logic

    Identify suspicious transactions based on various criteria. Consider:
    - Unusually high amounts
    - Multiple failed attempts
    - High-risk countries or merchants
    - Unusual transaction patterns
    - Time-based anomalies
    - Multiple transactions in short time

    Args:
        df (pd.DataFrame): Cleaned transaction data

    Returns:
        tuple: (normal_df, suspicious_df) - DataFrames split by suspicion status
    """
    """
    Identifica transacciones sospechosas basadas en un conjunto de reglas de negocio.
    
    Aplica las siguientes reglas (basadas en EDA_Limpieza_Fraude.ipynb):
    - Montos inusualmente altos (superiores a AMOUNT_THRESHOLD).
    - Múltiples intentos fallidos (superiores a ATTEMPT_THRESHOLD).
    - Transacciones declinadas por motivos de seguridad (contienen SECURITY_KEYWORDS).
    - Transacciones internacionales de alto valor.
    
    Args:
        df (pd.DataFrame): DataFrame de transacciones limpias.

    Returns:
        tuple: (df_normal, df_suspicious) - DataFrames separados.
    """
    try:
        AMOUNT_THRESHOLD = 1000
        ATTEMPT_THRESHOLD = 3
        SECURITY_KEYWORDS = ['security', 'fraud', 'stolen', 'lost card']
        HIGH_FREQ_THRESHOLD = 5
        df_processed = df.copy()
        df_processed['suspicion_reason'] = None
        df_processed.loc[df_processed['amount'] > AMOUNT_THRESHOLD, 'suspicion_reason'] = 'Monto inusualmente alto'
        df_processed.loc[df_processed['attempt_number'] > ATTEMPT_THRESHOLD, 'suspicion_reason'] = 'Múltiples intentos fallidos'
        df_processed.loc[
            (df_processed['status'] == 'declined') & 
            (df_processed['response_message'].str.contains('|'.join(SECURITY_KEYWORDS), case=False, na=False)),
            'suspicion_reason'
        ] = 'Declinada por violación de seguridad'
        df_processed.loc[
            (df_processed['is_international'] == True) & (df_processed['amount'] > AMOUNT_THRESHOLD),
            'suspicion_reason'
        ] = 'Internacional de alto valor'
        user_tx_counts = df_processed['user_id'].value_counts()
        high_freq_users = user_tx_counts[user_tx_counts > HIGH_FREQ_THRESHOLD].index
        df_processed.loc[
            df_processed['user_id'].isin(high_freq_users),
            'suspicion_reason'
        ] = 'Patrón anómalo (alta frecuencia de usuario)'
        suspicious_mask = df_processed['suspicion_reason'].notnull()
        df_suspicious = df_processed[suspicious_mask]
        df_normal = df_processed[~suspicious_mask]
        df_normal = df_normal.drop(columns=['suspicion_reason'])
        return df_normal, df_suspicious
    except Exception as e:
        print(f"ERROR: Error durante la detección de sospechosas: {e}")
        return df, pd.DataFrame(columns=df.columns)

def process_batch(raw_file):
    """
    Process a batch of transactions through the ETL pipeline

    Args:
        raw_file (Path): Path to the raw transaction CSV file
    """
    try:
        # [CORRECCIÓN 1] Construimos la ruta S3 completa
        # Usamos la variable 'raw_file' (que es el argumento)
        full_s3_path = f"s3://{raw_file}"
        
        print(f"Reading data from Data Lake: {full_s3_path}")
        
        # [CORRECCIÓN 2] Usamos MINIO_STORAGE_OPTIONS (no MINIO_CONFIG)
        df_raw = pd.read_csv(full_s3_path, storage_options=MINIO_STORAGE_OPTIONS)
        print(f"Loaded {len(df_raw)} transactions")

        # --- Pasos 1 y 2 (Sin cambios en la lógica) ---
        print("Cleaning data...")
        df_clean = clean_data(df_raw)
        print(f"Cleaned {len(df_clean)} transactions")

        print("Detecting suspicious transactions...")
        df_normal, df_suspicious = detect_suspicious_transactions(df_clean)
        print(f"Found {len(df_suspicious)} suspicious transactions")
        print(f"Found {len(df_normal)} normal transactions")

        # --- Guardar resultados en MinIO S3 ---
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if len(df_normal) > 0:
            normal_s3_path = f"s3://{PROCESSED_BUCKET}/processed_{timestamp}.csv"
            # [CORRECCIÓN 3] Usamos MINIO_STORAGE_OPTIONS
            df_normal.to_csv(normal_s3_path, index=False, storage_options=MINIO_STORAGE_OPTIONS)
            print(f"Saved normal transactions to S3: {normal_s3_path}")

        if len(df_suspicious) > 0:
            suspicious_s3_path = f"s3://{SUSPICIOUS_BUCKET}/suspicious_{timestamp}.csv"
            # [CORRECCIÓN 4] Usamos MINIO_STORAGE_OPTIONS
            df_suspicious.to_csv(suspicious_s3_path, index=False, storage_options=MINIO_STORAGE_OPTIONS)
            print(f"WARNING: Saved suspicious transactions to S3: {suspicious_s3_path}")

        # [CAMBIO] TODO Fase 3: Aquí iría la carga al Data Warehouse
        # load_to_dwh(df_normal, db_engine) 
        
        print(f"Batch processing completed successfully")

    except NotImplementedError as e:
        print(f"WARNING: Skipping processing: {e}")
    except Exception as e:
        print(f"ERROR: Error processing batch: {e}")


def main():
    """Main loop - genera y procesa transacciones cada minuto"""
    print("="*60)
    print("Transaction Processing Pipeline (v2 - S3 Data Lake)")
    print("="*60)

    try:
        # [CAMBIO] Reemplazamos setup_folders por setup_minio_buckets
        setup_minio_buckets()
    except Exception as e:
        print("Pipeline detenido. No se pudo inicializar la infraestructura.")
        return

    print(f"\nStarting continuous processing (every {INTERVAL_SECONDS} seconds)")
    print("Press Ctrl+C to stop\n")

    batch_count = 0
    try:
        while True:
            batch_count += 1
            print(f"\n{'='*60}")
            print(f"BATCH #{batch_count}")
            print(f"{'='*60}")

            # 1. Genera nuevas transacciones y las guarda en S3
            s3_raw_file = generate_batch()

            # 2. Procesa el lote desde S3 y guarda resultados en S3
            if s3_raw_file:
                process_batch(s3_raw_file)

            # 3. Espera para el siguiente lote
            print(f"\nWaiting {INTERVAL_SECONDS} seconds until next batch...")
            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n\nPipeline stopped by user")
        print(f"Total batches processed: {batch_count}")


if __name__ == "__main__":
    main()
