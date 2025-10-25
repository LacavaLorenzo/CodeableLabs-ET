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
    # YOUR CODE HERE
    # Example structure:
    # df_clean = df.copy()
    # ... your cleaning logic ...
    # return df_clean

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
    # YOUR CODE HERE
    # Example structure:
    # df['is_suspicious'] = False
    # ... your detection logic ...
    # suspicious_df = df[df['is_suspicious'] == True]
    # normal_df = df[df['is_suspicious'] == False]
    # return normal_df, suspicious_df

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
