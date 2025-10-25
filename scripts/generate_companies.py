import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta


def generate_companies(n=1000):
    """Genera dataset de empresas/merchants para fintech latinoamericana"""
    fake = Faker(["es_MX", "pt_BR", "es_CO", "es_AR", "es_CL"])
    np.random.seed(2025)

    companies = []

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

        # Categoría del negocio
        category = np.random.choice(
            ["retail", "food_beverage", "services", "tech", "healthcare",
             "education", "entertainment", "travel", "automotive", "other"],
            p=[0.25, 0.20, 0.15, 0.10, 0.08, 0.07, 0.05, 0.04, 0.03, 0.03]
        )

        # Tamaño de la empresa
        company_size = np.random.choice(
            ["micro", "small", "medium", "large"],
            p=[0.40, 0.35, 0.20, 0.05]
        )

        # Fecha de registro (últimos 3 años)
        registration_date = datetime.now() - timedelta(days=np.random.randint(0, 1095))

        # Estado del merchant
        merchant_status = np.random.choice(
            ["active", "inactive", "suspended", "pending_review"],
            p=[0.80, 0.10, 0.05, 0.05]
        )

        # Volumen de transacciones según tamaño
        if company_size == "large":
            monthly_volume = round(np.random.uniform(500000, 5000000), 2)
            transaction_count = np.random.randint(5000, 50000)
        elif company_size == "medium":
            monthly_volume = round(np.random.uniform(100000, 500000), 2)
            transaction_count = np.random.randint(1000, 5000)
        elif company_size == "small":
            monthly_volume = round(np.random.uniform(10000, 100000), 2)
            transaction_count = np.random.randint(100, 1000)
        else:
            monthly_volume = round(np.random.uniform(1000, 10000), 2)
            transaction_count = np.random.randint(10, 100)

        # Comisión según categoría y tamaño
        if company_size == "large":
            commission_rate = round(np.random.uniform(1.5, 2.5), 2)
        elif company_size == "medium":
            commission_rate = round(np.random.uniform(2.5, 3.5), 2)
        else:
            commission_rate = round(np.random.uniform(3.5, 5.0), 2)

        company = {
            "merchant_id": 1 + i,
            "company_name": fake.company(),
            "legal_name": fake.company() + " " + np.random.choice(["S.A.", "S.R.L.", "LTDA", "Inc.", "Corp."]),
            "tax_id": fake.uuid4()[:12].upper().replace("-", ""),
            "email": fake.company_email(),
            "phone": fake.phone_number(),
            "website": fake.url() if np.random.random() > 0.3 else None,
            "country": country,
            "city": fake.city(),
            "address": fake.address().replace("\n", ", "),
            "postal_code": fake.postcode(),
            "category": category,
            "subcategory": f"{category}_{np.random.randint(1, 10)}",
            "company_size": company_size,
            "registration_date": registration_date.strftime("%Y-%m-%d %H:%M:%S"),
            "merchant_status": merchant_status,
            "kyc_verified": np.random.choice([True, False], p=[0.85, 0.15]),
            "pci_compliant": np.random.choice([True, False], p=[0.75, 0.25]),
            "commission_rate": commission_rate,
            "settlement_frequency": np.random.choice(["daily", "weekly", "biweekly", "monthly"], p=[0.10, 0.30, 0.40, 0.20]),
            "preferred_currency": np.random.choice(["USD", "MXN", "BRL", "COP", "ARS", "CLP"]),
            "monthly_volume": monthly_volume if merchant_status == "active" else round(monthly_volume * 0.1, 2),
            "monthly_transactions": transaction_count if merchant_status == "active" else int(transaction_count * 0.1),
            "average_ticket": round(monthly_volume / transaction_count, 2) if transaction_count > 0 else 0,
            "chargeback_rate": round(np.random.uniform(0, 2.5), 2),
            "risk_score": round(np.random.uniform(0, 100), 2),
            "has_api_integration": np.random.choice([True, False], p=[0.60, 0.40]),
            "accepted_payment_methods": np.random.randint(2, 6),
            "last_transaction_date": (datetime.now() - timedelta(days=np.random.randint(0, 30))).strftime("%Y-%m-%d") if merchant_status == "active" else None,
            "account_manager": fake.name() if company_size in ["medium", "large"] else None,
            "contract_type": np.random.choice(["standard", "premium", "enterprise"], p=[0.70, 0.20, 0.10])
        }

        companies.append(company)

    df = pd.DataFrame(companies)

    null_indices = np.random.choice(
        df.index, size=int(n * 0.03), replace=False)
    df.loc[null_indices, "website"] = None

    null_indices = np.random.choice(
        df.index, size=int(n * 0.01), replace=False)
    df.loc[null_indices, "postal_code"] = None

    return df


if __name__ == "__main__":
    df = generate_companies(1000)
    df.to_csv("./data/companies.csv", index=False)
