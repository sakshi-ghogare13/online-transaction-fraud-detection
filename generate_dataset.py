import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# ==============================
# Configuration
# ==============================

TOTAL_RECORDS = 500000
FRAUD_PERCENTAGE = 0.04

OUTPUT_FILE = "dataset/synthetic_fraud_dataset.csv"

np.random.seed(42)
random.seed(42)


# ==============================
# Create dataset folder
# ==============================

os.makedirs("dataset", exist_ok=True)


# ==============================
# Categories
# ==============================

transaction_types = [
    "UPI",
    "Credit Card",
    "Debit Card",
    "Bank Transfer",
    "Wallet",
    "ATM"
]

merchant_categories = [
    "Shopping",
    "Food",
    "Travel",
    "Bills",
    "Transfer",
    "Entertainment",
    "Healthcare",
    "Electronics",
    "Education"
]

device_types = [
    "Android",
    "iPhone",
    "Laptop",
    "ATM",
    "Tablet"
]

cities = [
    "Pune",
    "Mumbai",
    "Delhi",
    "Bangalore",
    "Hyderabad",
    "Chennai",
    "Kolkata",
    "Ahmedabad"
]

countries = [
    "India",
    "USA",
    "UK",
    "Canada",
    "Singapore",
    "Germany",
    "UAE",
    "Australia"
]


# ==============================
# Dataset Generation
# ==============================

fraud_count = int(TOTAL_RECORDS * FRAUD_PERCENTAGE)

records = []

start_date = datetime.now() - timedelta(days=365)

for i in range(TOTAL_RECORDS):

    is_fraud = 1 if i < fraud_count else 0

    transaction_date = start_date + timedelta(
        minutes=random.randint(1, 525600)
    )

    time_seconds = int(
        (transaction_date - start_date).total_seconds()
    )

    if is_fraud == 0:

        amount = round(
            max(50, np.random.normal(2500, 1500)),
            2
        )

        failed_login_attempts = random.randint(0, 2)

        previous_transactions_24h = random.randint(1, 8)

        unusual_location = random.choice([0, 0, 0, 1])

        vpn_used = random.choice([0, 0, 0, 1])

        multiple_cards_used = random.choice([0, 0, 0, 1])

        account_age_days = random.randint(120, 2500)

        transaction_velocity = random.randint(1, 5)

    else:

        amount = round(
            max(5000, np.random.normal(28000, 12000)),
            2
        )

        failed_login_attempts = random.randint(3, 10)

        previous_transactions_24h = random.randint(0, 2)

        unusual_location = 1

        vpn_used = random.choice([0, 1])

        multiple_cards_used = random.choice([0, 1])

        account_age_days = random.randint(1, 120)

        transaction_velocity = random.randint(8, 20)

    record = {

        "Transaction_ID": f"TXN{i + 1:08d}",

        "Time": time_seconds,

        "Transaction_Date": transaction_date.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "Amount": amount,

        "Transaction_Type": random.choice(
            transaction_types
        ),

        "Merchant_Category": random.choice(
            merchant_categories
        ),

        "Device_Type": random.choice(
            device_types
        ),

        "City": random.choice(cities),

        "Country": random.choice(countries),

        "Failed_Login_Attempts":
            failed_login_attempts,

        "Previous_Transactions_24H":
            previous_transactions_24h,

        "Unusual_Location":
            unusual_location,

        "VPN_Used":
            vpn_used,

        "Multiple_Cards_Used":
            multiple_cards_used,

        "Account_Age_Days":
            account_age_days,

        "Transaction_Velocity":
            transaction_velocity,

        "Is_Fraud":
            is_fraud
    }

    records.append(record)


# ==============================
# Save Dataset
# ==============================

df = pd.DataFrame(records)

df = df.sample(
    frac=1,
    random_state=42
).reset_index(drop=True)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==============================
# Summary
# ==============================

print("Dataset generated successfully!")

print("-------------------------------")

print(f"Total Records: {len(df)}")

print(f"Fraud Records: {df['Is_Fraud'].sum()}")

print(
    f"Legitimate Records: "
    f"{(df['Is_Fraud'] == 0).sum()}"
)

print(
    f"Fraud Percentage: "
    f"{round(df['Is_Fraud'].mean() * 100, 2)}%"
)

print(f"Saved at: {OUTPUT_FILE}")