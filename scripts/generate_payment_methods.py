import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta


def generate_payment_methods(n=5000):
    """
    Genera dataset de métodos de pago coherente con:
    - Users: user_id de 1 a 10000
    - Transactions: payment_method y payment_provider
    """
    fake = Faker()
    np.random.seed(2025)

    payment_methods = []

    # Tipos de métodos de pago coherentes con transactions
    method_types = {
        "credit_card": {
            "providers": ["Visa", "Mastercard", "American Express", "Diners Club"],
            "probabilities": [0.45, 0.35, 0.15, 0.05]
        },
        "debit_card": {
            "providers": ["Visa Debit", "Mastercard Debit", "Maestro"],
            "probabilities": [0.50, 0.40, 0.10]
        },
        "bank_transfer": {
            "providers": ["SPEI", "TEF", "PIX", "PSE", "Transferencia"],
            "probabilities": [0.25, 0.20, 0.30, 0.15, 0.10]
        },
        "ewallet": {
            "providers": ["PayPal", "MercadoPago", "Rappi Pay", "Clip"],
            "probabilities": [0.30, 0.35, 0.20, 0.15]
        }
    }

    for i in range(n):
        # Asignar a un user_id existente (1-10000)
        user_id = np.random.randint(1, 10001)

        # País (misma distribución que users, companies y transactions)
        country = np.random.choice(
            ["MX", "BR", "CO", "AR", "CL", "PE"],
            p=[0.30, 0.25, 0.15, 0.15, 0.10, 0.05]
        )

        # Tipo de método de pago (misma distribución que transactions)
        payment_type = np.random.choice(
            ["credit_card", "debit_card", "bank_transfer", "ewallet"],
            p=[0.40, 0.30, 0.20, 0.10]
        )

        # Provider según el tipo (coherente con transactions)
        provider = np.random.choice(
            method_types[payment_type]["providers"],
            p=method_types[payment_type]["probabilities"]
        )

        # Fecha de registro (últimos 2 años)
        registration_date = datetime.now() - timedelta(days=np.random.randint(0, 730))

        # Estado del método de pago
        status = np.random.choice(
            ["active", "inactive", "expired", "blocked"],
            p=[0.75, 0.15, 0.07, 0.03]
        )

        # Generar detalles específicos según el tipo
        if payment_type in ["credit_card", "debit_card"]:
            # Últimos 4 dígitos de la tarjeta
            last_four = str(np.random.randint(1000, 9999))
            # Fecha de expiración (1-5 años en el futuro o pasado si expirado)
            if status == "expired":
                expiry_date = (datetime.now() - timedelta(days=np.random.randint(1, 365))).strftime("%m/%y")
            else:
                expiry_date = (datetime.now() + timedelta(days=np.random.randint(30, 1825))).strftime("%m/%y")
            token = fake.uuid4()
            details = f"****{last_four}"
            is_default = np.random.choice([True, False], p=[0.30, 0.70])
        elif payment_type == "bank_transfer":
            # Últimos 4 dígitos de cuenta bancaria
            last_four = str(np.random.randint(1000, 9999))
            expiry_date = None
            token = fake.uuid4()
            details = f"****{last_four}"
            is_default = np.random.choice([True, False], p=[0.25, 0.75])
        else:  # ewallet
            last_four = None
            expiry_date = None
            token = fake.uuid4()
            details = fake.email()
            is_default = np.random.choice([True, False], p=[0.20, 0.80])

        # Uso del método de pago
        if status == "active":
            transactions_count = np.random.randint(1, 200)
            total_amount = round(np.random.uniform(100, 50000), 2)
            last_used = (datetime.now() - timedelta(days=np.random.randint(0, 60))).strftime("%Y-%m-%d %H:%M:%S")
        else:
            transactions_count = np.random.randint(0, 50)
            total_amount = round(np.random.uniform(0, 5000), 2)
            last_used = (datetime.now() - timedelta(days=np.random.randint(61, 365))).strftime("%Y-%m-%d %H:%M:%S") if transactions_count > 0 else None

        payment_method = {
            "payment_method_id": 1 + i,
            "user_id": user_id,
            "payment_type": payment_type,
            "provider": provider,
            "masked_details": details,
            "last_four_digits": last_four,
            "token": token,
            "status": status,
            "is_default": is_default,
            "registration_date": registration_date.strftime("%Y-%m-%d %H:%M:%S"),
            "expiry_date": expiry_date,
            "last_used": last_used,
            "transactions_count": transactions_count,
            "total_amount_processed": total_amount,
            "verification_status": np.random.choice(["verified", "pending", "failed"], p=[0.85, 0.10, 0.05]),
            "country": country,
            "issuer_bank": fake.company() if payment_type in ["credit_card", "debit_card", "bank_transfer"] else None,
            "billing_address": fake.address().replace("\n", ", ") if payment_type in ["credit_card", "debit_card"] else None,
            "cvv_verified": np.random.choice([True, False], p=[0.90, 0.10]) if payment_type in ["credit_card", "debit_card"] else None,
            "three_ds_enabled": np.random.choice([True, False], p=[0.70, 0.30]) if payment_type in ["credit_card", "debit_card"] else None,
            "failed_attempts": np.random.randint(0, 5) if status == "blocked" else 0,
            "risk_score": round(np.random.uniform(0, 100), 2)
        }

        payment_methods.append(payment_method)

    df = pd.DataFrame(payment_methods)

    # Introducir algunos datos faltantes de manera intencional
    null_indices = np.random.choice(
        df.index, size=int(n * 0.02), replace=False)
    df.loc[null_indices, "last_used"] = None

    null_indices = np.random.choice(
        df.index, size=int(n * 0.01), replace=False)
    df.loc[null_indices, "billing_address"] = None

    return df


if __name__ == "__main__":
    df = generate_payment_methods(5000)
    df.to_csv("./data/payment_methods.csv", index=False)
    print(f"\n✓ Generated {len(df)} payment methods in data/payment_methods.csv")
    print(f"\nDataset summary:")
    print(f"  - Payment types: {df['payment_type'].value_counts().to_dict()}")
    print(f"  - Top providers:")
    for ptype in ["credit_card", "debit_card", "bank_transfer", "ewallet"]:
        print(f"    {ptype}: {df[df['payment_type']==ptype]['provider'].value_counts().to_dict()}")
    print(f"  - Status distribution: {df['status'].value_counts().to_dict()}")
    print(f"  - Countries: {df['country'].value_counts().to_dict()}")
    print(f"  - Default payment methods: {df['is_default'].sum()}")
    print(f"  - Average transactions per method: {df['transactions_count'].mean():.2f}")
    print(f"  - Total amount processed: ${df['total_amount_processed'].sum():,.2f}")
