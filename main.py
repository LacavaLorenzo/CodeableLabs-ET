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


# Configuration
TRANSACTIONS_FOLDER = Path("./transactions")
PROCESSED_FOLDER = Path("./processed")
SUSPICIOUS_FOLDER = Path("./suspicious")
INTERVAL_SECONDS = 60  # Generate transactions every 1 minute
TRANSACTIONS_PER_BATCH = 100  # Number of transactions to generate each time


def setup_folders():
    """Create necessary folders if they don't exist"""
    TRANSACTIONS_FOLDER.mkdir(exist_ok=True)
    PROCESSED_FOLDER.mkdir(exist_ok=True)
    SUSPICIOUS_FOLDER.mkdir(exist_ok=True)
    print(f"Folders initialized:")
    print(f"  - Data Lake: {TRANSACTIONS_FOLDER}")
    print(f"  - Processed: {PROCESSED_FOLDER}")
    print(f"  - Suspicious: {SUSPICIOUS_FOLDER}")


def generate_batch():
    """Generate a batch of fake transactions and save to data lake"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = TRANSACTIONS_FOLDER / f"transactions_{timestamp}.csv"

    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Generating {TRANSACTIONS_PER_BATCH} transactions...")
    df = generate_transactions(TRANSACTIONS_PER_BATCH)
    df.to_csv(filename, index=False)
    print(f"Saved to: {filename}")

    return filename


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
        # 1. Crear una copia para evitar advertencias de SettingWithCopyWarning
        df_clean = df.copy()

        # 2. Eliminar duplicados (Requisito de la prueba)
        # Nos basamos en 'transaction_id' como clave única.
        df_clean.drop_duplicates(subset=['transaction_id'], keep='first', inplace=True)

        # 3. Manejar valores nulos (según nuestro diagnóstico)
        df_clean['three_ds_verified'] = df_clean['three_ds_verified'].fillna(False)
        df_clean['ip_address'] = df_clean['ip_address'].fillna('Unknown')

        # 4. Validar y convertir tipos de datos (Fechas)
        # 'errors=coerce' convierte los nulos (de transacciones 'declined') en NaT (Not a Time).
        df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'])
        df_clean['settlement_date'] = pd.to_datetime(df_clean['settlement_date'], errors='coerce')

        # 5. Validar y convertir tipos de datos (Booleanos)
        df_clean['three_ds_verified'] = df_clean['three_ds_verified'].astype(bool)
        df_clean['is_international'] = df_clean['is_international'].astype(bool)

        # 6. Estandarizar formatos de texto (Requisito de la prueba)
        text_cols_to_lower = ['status', 'payment_method', 'category', 'device_type']
        text_cols_to_upper = ['currency', 'country']

        for col in text_cols_to_lower:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].str.lower()
                
        for col in text_cols_to_upper:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].str.upper()

        return df_clean

    except Exception as e:
        print(f"ERROR: Error durante la limpieza de datos: {e}")
        # Retornar un dataframe vacío si la limpieza falla
        return pd.DataFrame(columns=df.columns)

    raise NotImplementedError("clean_data() function needs to be implemented")


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
        # 0. Definir umbrales y listas de riesgo
        AMOUNT_THRESHOLD = 1000  # Umbral para montos "inusualmente altos"
        ATTEMPT_THRESHOLD = 3    # Más de 3 intentos fallidos es sospechoso
        SECURITY_KEYWORDS = ['security', 'fraud', 'stolen', 'lost card'] # Palabras clave de fraude

        # 1. Crear una copia para trabajar
        df_processed = df.copy()
        
        # 2. Crear la columna de razón (inicia vacía)
        df_processed['suspicion_reason'] = None

        # --- Aplicación de Reglas ---
        # Usamos .loc para asignar la razón de forma eficiente

        # Regla 1: Montos Inusualmente Altos
        df_processed.loc[
            df_processed['amount'] > AMOUNT_THRESHOLD, 
            'suspicion_reason'
        ] = 'Monto inusualmente alto'

        # Regla 2: Múltiples Intentos Fallidos
        df_processed.loc[
            df_processed['attempt_number'] > ATTEMPT_THRESHOLD, 
            'suspicion_reason'
        ] = 'Múltiples intentos fallidos'

        # Regla 3: Declinadas por Seguridad
        df_processed.loc[
            (df_processed['status'] == 'declined') & 
            (df_processed['response_message'].str.contains('|'.join(SECURITY_KEYWORDS), case=False, na=False)),
            'suspicion_reason'
        ] = 'Declinada por violación de seguridad'

        # Regla 4: Internacionales de Alto Riesgo
        df_processed.loc[
            (df_processed['is_international'] == True) & 
            (df_processed['amount'] > AMOUNT_THRESHOLD),
            'suspicion_reason'
        ] = 'Internacional de alto valor'

        # 3. Separar los DataFrames
        suspicious_mask = df_processed['suspicion_reason'].notnull()
        df_suspicious = df_processed[suspicious_mask]
        df_normal = df_processed[~suspicious_mask]

        # Opcional: Eliminar la columna 'suspicion_reason' del df_normal si no se quiere
        df_normal = df_normal.drop(columns=['suspicion_reason'])

        return df_normal, df_suspicious

    except Exception as e:
        print(f"ERROR: Error durante la detección de sospechosas: {e}")
        # Si falla la detección, asumimos que todo es normal para no detener el pipeline
        # pero devolvemos un df sospechoso vacío.
        return df, pd.DataFrame(columns=df.columns)

    raise NotImplementedError("detect_suspicious_transactions() function needs to be implemented")


def process_batch(raw_file):
    """
    Process a batch of transactions through the ETL pipeline

    Args:
        raw_file (Path): Path to the raw transaction CSV file
    """
    try:
        # Read raw data from data lake
        print(f"Reading data from: {raw_file}")
        df_raw = pd.read_csv(raw_file)
        print(f"Loaded {len(df_raw)} transactions")

        # Step 1: Clean the data
        print("Cleaning data...")
        df_clean = clean_data(df_raw)
        print(f"Cleaned {len(df_clean)} transactions")

        # Step 2: Detect suspicious transactions
        print("Detecting suspicious transactions...")
        df_normal, df_suspicious = detect_suspicious_transactions(df_clean)
        print(f"Found {len(df_suspicious)} suspicious transactions")
        print(f"Found {len(df_normal)} normal transactions")

        # Save processed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if len(df_normal) > 0:
            normal_file = PROCESSED_FOLDER / f"processed_{timestamp}.csv"
            df_normal.to_csv(normal_file, index=False)
            print(f"Saved normal transactions to: {normal_file}")

        if len(df_suspicious) > 0:
            suspicious_file = SUSPICIOUS_FOLDER / f"suspicious_{timestamp}.csv"
            df_suspicious.to_csv(suspicious_file, index=False)
            print(f"WARNING: Saved suspicious transactions to: {suspicious_file}")

        print(f"Batch processing completed successfully")

    except NotImplementedError as e:
        print(f"WARNING: Skipping processing: {e}")
    except Exception as e:
        print(f"ERROR: Error processing batch: {e}")


def main():
    """Main loop - generates and processes transactions every minute"""
    print("="*60)
    print("Transaction Processing Pipeline")
    print("="*60)

    setup_folders()

    print(f"\nStarting continuous processing (every {INTERVAL_SECONDS} seconds)")
    print("Press Ctrl+C to stop\n")

    batch_count = 0

    try:
        while True:
            batch_count += 1
            print(f"\n{'='*60}")
            print(f"BATCH #{batch_count}")
            print(f"{'='*60}")

            # Generate new transactions
            raw_file = generate_batch()

            # Process the batch
            process_batch(raw_file)

            # Wait for next interval
            print(f"\nWaiting {INTERVAL_SECONDS} seconds until next batch...")
            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n\nPipeline stopped by user")
        print(f"Total batches processed: {batch_count}")


if __name__ == "__main__":
    main()
