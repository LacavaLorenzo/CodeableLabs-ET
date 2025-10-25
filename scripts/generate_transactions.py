import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta


def generate_transactions(n=10000):
    """
    Genera dataset de transacciones coherente con:
    - Users: user_id de 1 a 10000
    - Companies: merchant_id de 1 a 1000
    """
    fake = Faker()
    np.random.seed(2025)

    transactions = []
    start_date = datetime.now() - timedelta(days=90)

    # Tipos de métodos de pago coherentes
    payment_methods = {
        "credit_card": ["Visa", "Mastercard", "American Express", "Diners Club"],
        "debit_card": ["Visa Debit", "Mastercard Debit", "Maestro"],
        "bank_transfer": ["SPEI", "TEF", "PIX", "PSE", "Transferencia"],
        "ewallet": ["PayPal", "MercadoPago", "Rappi Pay", "Clip"]
    }

    # Monedas por país
    currency_by_country = {
        "MX": "MXN",
        "BR": "BRL",
        "CO": "COP",
        "AR": "ARS",
        "CL": "CLP",
        "PE": "PEN"
    }

    for i in range(n):
        # IDs coherentes con los otros datasets
        user_id = np.random.randint(1, 10001)  # 1-10000
        merchant_id = np.random.randint(1, 1001)  # 1-1000

        # País (misma distribución que users y companies)
        country = np.random.choice(
            ["MX", "BR", "CO", "AR", "CL", "PE"],
            p=[0.30, 0.25, 0.15, 0.15, 0.10, 0.05]
        )

        # Moneda basada en el país
        currency = currency_by_country.get(country, "USD")

        # Posibilidad de transacciones internacionales (USD)
        if np.random.random() < 0.15:  # 15% transacciones en USD
            currency = "USD"

        # Timestamp dentro de los últimos 90 días
        timestamp = start_date + \
            timedelta(seconds=np.random.randint(0, 90*24*3600))

        # Tipo de método de pago
        payment_type = np.random.choice(
            ["credit_card", "debit_card", "bank_transfer", "ewallet"],
            p=[0.40, 0.30, 0.20, 0.10]
        )

        # Provider específico según el tipo
        payment_provider = np.random.choice(payment_methods[payment_type])

        # Monto de transacción (distribución exponencial más realista)
        amount = round(np.random.exponential(50), 2)

        # Asegurar monto mínimo
        if amount < 1:
            amount = round(np.random.uniform(1, 10), 2)

        # Estado de la transacción
        status = np.random.choice(
            ["approved", "declined", "pending", "refunded", "cancelled"],
            p=[0.82, 0.10, 0.03, 0.03, 0.02]
        )

        # Código de respuesta según el estado
        if status == "approved":
            response_code = "00"
            response_message = "Transaction approved"
        elif status == "declined":
            response_code = np.random.choice(["05", "51", "54", "61", "65"])
            response_message = np.random.choice([
                "Insufficient funds",
                "Expired card",
                "Invalid card",
                "Exceeds withdrawal limit",
                "Security violation"
            ])
        elif status == "pending":
            response_code = "pending"
            response_message = "Pending authorization"
        else:
            response_code = np.random.choice(["refund", "cancelled"])
            response_message = f"Transaction {status}"

        if np.random.random() < 0.002:
            amount = round(np.random.uniform(15000, 50000), 2)

        # Fees y comisiones
        if status == "approved":
            if payment_type in ["credit_card", "debit_card"]:
                fee_percentage = round(np.random.uniform(2.5, 3.5), 2)
            elif payment_type == "ewallet":
                fee_percentage = round(np.random.uniform(3.0, 4.5), 2)
            else:  # bank_transfer
                fee_percentage = round(np.random.uniform(1.0, 2.0), 2)

            transaction_fee = round(amount * fee_percentage / 100, 2)
            net_amount = round(amount - transaction_fee, 2)
        else:
            fee_percentage = 0
            transaction_fee = 0
            net_amount = 0

        # Información adicional
        device_type = np.random.choice(
            ["mobile", "desktop", "tablet", "api"],
            p=[0.55, 0.30, 0.10, 0.05]
        )

        transaction = {
            "transaction_id": f"TXN{str(i+1).zfill(8)}",
            "user_id": user_id,
            "merchant_id": merchant_id,
            "amount": amount,
            "currency": currency,
            "status": status,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "payment_method": payment_type,
            "payment_provider": payment_provider,
            "country": country,
            "response_code": response_code,
            "response_message": response_message,
            "fee_percentage": fee_percentage,
            "transaction_fee": transaction_fee,
            "net_amount": net_amount,
            "device_type": device_type,
            "ip_address": fake.ipv4(),
            "user_agent": fake.user_agent() if device_type != "api" else "API/1.0",
            "attempt_number": 1 if status != "declined" else np.random.randint(1, 4),
            "processing_time_ms": np.random.randint(100, 3000),
            "three_ds_verified": np.random.choice([True, False], p=[0.70, 0.30]) if payment_type in ["credit_card", "debit_card"] else None,
            "installments": np.random.choice([1, 3, 6, 12], p=[0.70, 0.15, 0.10, 0.05]) if payment_type == "credit_card" and status == "approved" else 1,
            "category": np.random.choice([
                "retail", "food_beverage", "services", "tech", "entertainment",
                "travel", "utilities", "other"
            ]),
            "is_international": currency == "USD" and country != "US",
            "settlement_date": (timestamp + timedelta(days=np.random.randint(1, 3))).strftime("%Y-%m-%d") if status == "approved" else None
        }

        transactions.append(transaction)

    df = pd.DataFrame(transactions)

    # Introducir algunos nulos de manera intencional
    null_indices = np.random.choice(
        df.index, size=int(n * 0.005), replace=False)
    df.loc[null_indices, "currency"] = None

    null_indices = np.random.choice(
        df.index, size=int(n * 0.01), replace=False)
    df.loc[null_indices, "ip_address"] = None

    return df


if __name__ == "__main__":
    df = generate_transactions(1000)
    time = datetime.now().strftime("%m%d_%H%M%S")
    filename = f"./transactions/transactions_{time}.csv"
    df.to_csv(filename, index=False)
