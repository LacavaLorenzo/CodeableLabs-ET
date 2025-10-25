import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta


def generate_users(n=10000):
    """Genera dataset de usuarios simulados para fintech latinoamericana"""
    fake = Faker(["es_MX", "pt_BR", "es_CO", "es_AR", "es_CL"])
    np.random.seed(2025)

    users = []

    for i in range(n):
        country = np.random.choice(["MX", "BR", "CO", "AR", "CL", "PE"], p=[
                                   0.30, 0.25, 0.15, 0.15, 0.10, 0.05])

        # Configurar locale según país
        if country == "BR":
            fake = Faker("pt_BR")
        elif country == "MX":
            fake = Faker("es_MX")
        elif country == "CO":
            fake = Faker("es_CO")
        elif country == "AR":
            fake = Faker("es_AR")
        else:
            fake = Faker("es_CL")

        # Fecha de registro (últimos 2 años)
        registration_date = datetime.now() - timedelta(days=np.random.randint(0, 730))

        # Estado de cuenta con distribución realista
        account_status = np.random.choice(
            ["active", "inactive", "suspended", "pending_verification"],
            p=[0.75, 0.15, 0.05, 0.05]
        )

        # Nivel de verificación KYC
        kyc_level = np.random.choice(
            ["basic", "intermediate", "advanced", "none"],
            p=[0.40, 0.35, 0.20, 0.05]
        )

        # Límite de transacciones según KYC
        if kyc_level == "advanced":
            transaction_limit = np.random.randint(50000, 100000)
        elif kyc_level == "intermediate":
            transaction_limit = np.random.randint(10000, 50000)
        elif kyc_level == "basic":
            transaction_limit = np.random.randint(1000, 10000)
        else:
            transaction_limit = 500

        user = {
            "user_id": 1 + i,
            "email": fake.email(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "phone": fake.phone_number(),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=75).strftime("%Y-%m-%d"),
            "country": country,
            "city": fake.city(),
            "address": fake.address().replace("\n", ", "),
            "postal_code": fake.postcode(),
            "registration_date": registration_date.strftime("%Y-%m-%d %H:%M:%S"),
            "account_status": account_status,
            "kyc_level": kyc_level,
            "kyc_verified": kyc_level != "none",
            "transaction_limit_daily": transaction_limit,
            "preferred_currency": np.random.choice(["USD", "MXN", "BRL", "COP", "ARS", "CLP"]),
            "risk_score": round(np.random.uniform(0, 100), 2),
            "total_transactions": np.random.randint(0, 500) if account_status == "active" else np.random.randint(0, 50),
            "total_volume": round(np.random.uniform(0, 50000), 2) if account_status == "active" else round(np.random.uniform(0, 5000), 2),
            "last_login": (datetime.now() - timedelta(days=np.random.randint(0, 60))).strftime("%Y-%m-%d %H:%M:%S") if account_status == "active" else None,
            "has_active_card": np.random.choice([True, False], p=[0.70, 0.30]),
            "payment_methods_count": np.random.randint(1, 5),
            "referral_code": fake.uuid4()[:8].upper(),
            "is_merchant": np.random.choice([True, False], p=[0.10, 0.90]),
            "merchant_category": np.random.choice(["retail", "services", "food", "tech", "other", None], p=[0.03, 0.02, 0.02, 0.01, 0.02, 0.90])
        }

        users.append(user)

    df = pd.DataFrame(users)

    # Introducir algunos datos faltantes de manera intencional
    null_indices = np.random.choice(
        df.index, size=int(n * 0.02), replace=False)
    df.loc[null_indices, "phone"] = None

    null_indices = np.random.choice(
        df.index, size=int(n * 0.01), replace=False)
    df.loc[null_indices, "postal_code"] = None

    return df


if __name__ == "__main__":
    df = generate_users(10000)
    df.to_csv("./data/users.csv", index=False)
