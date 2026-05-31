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
    "Entertainment",
    "Healthcare",
    "Electronics",
    "Education",
    "Crypto",
    "Gaming",
    "Insurance",
    "Utilities",
    "Investment"
]

device_types = [
    "Android",
    "iPhone",
    "Laptop",
    "ATM",
    "Tablet"
]

india_cities = [
    "Pune",
    "Mumbai",
    "Delhi",
    "Bangalore",
    "Hyderabad",
    "Chennai",
    "Kolkata",
    "Ahmedabad"
]

foreign_locations = {
    "USA": ["New York", "Chicago", "San Francisco"],
    "UK": ["London", "Manchester"],
    "Canada": ["Toronto", "Vancouver"],
    "Singapore": ["Singapore"],
    "Germany": ["Berlin", "Munich"],
    "UAE": ["Dubai", "Abu Dhabi"],
    "Australia": ["Sydney", "Melbourne"]
}

high_risk_merchants = [
    "Crypto",
    "Gaming",
    "Electronics",
    "Investment"
]


# ==============================
# Helper Function
# ==============================

def calculate_risk_score(
    amount,
    failed_login_attempts,
    unusual_location,
    vpn_used,
    multiple_cards_used,
    account_age_days,
    transaction_velocity,
    international_transaction,
    new_device_login,
    merchant_category
):
    score = 0

    if amount > 50000:
        score += 20
    elif amount > 15000:
        score += 10

    score += failed_login_attempts * 4
    score += transaction_velocity * 3

    if unusual_location:
        score += 15

    if vpn_used:
        score += 10

    if multiple_cards_used:
        score += 10

    if account_age_days < 60:
        score += 15
    elif account_age_days < 180:
        score += 8

    if international_transaction:
        score += 15

    if new_device_login:
        score += 12

    if merchant_category in high_risk_merchants:
        score += 10

    return min(score, 100)


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

    hour = transaction_date.hour
    day_of_week = transaction_date.weekday()
    is_weekend = 1 if day_of_week in [5, 6] else 0
    is_night_transaction = 1 if hour >= 23 or hour <= 5 else 0

    transaction_type = random.choice(transaction_types)
    merchant_category = random.choice(merchant_categories)
    device_type = random.choice(device_types)

    # ==============================
    # Realistic Location Logic
    # ==============================

    if is_fraud == 0:
        city = random.choice(india_cities)
        country = "India"
    else:
        if random.random() < 0.55:
            city = random.choice(india_cities)
            country = "India"
        else:
            country = random.choice(list(foreign_locations.keys()))
            city = random.choice(foreign_locations[country])

    international_transaction = 0 if country == "India" else 1

    # ==============================
    # Legitimate Transactions
    # ==============================

    if is_fraud == 0:

        amount = round(
            max(20, np.random.lognormal(mean=7.7, sigma=0.8)),
            2
        )

        # Some genuine high-value transactions
        if random.random() < 0.04:
            amount = round(
                random.uniform(30000, 150000),
                2
            )

        failed_login_attempts = random.choices(
            [0, 1, 2, 3],
            weights=[70, 20, 8, 2]
        )[0]

        previous_transactions_24h = random.randint(1, 12)

        unusual_location = random.choices(
            [0, 1],
            weights=[85, 15]
        )[0]

        vpn_used = random.choices(
            [0, 1],
            weights=[88, 12]
        )[0]

        multiple_cards_used = random.choices(
            [0, 1],
            weights=[90, 10]
        )[0]

        account_age_days = random.randint(90, 3000)

        transaction_velocity = random.choices(
            [1, 2, 3, 4, 5, 6, 7],
            weights=[25, 25, 20, 12, 8, 6, 4]
        )[0]

        new_device_login = random.choices(
            [0, 1],
            weights=[85, 15]
        )[0]

    # ==============================
    # Fraudulent Transactions
    # ==============================

    else:

        fraud_pattern = random.choice([
            "high_amount",
            "small_card_testing",
            "new_account",
            "velocity_attack",
            "foreign_transaction",
            "stealth_fraud"
        ])

        if fraud_pattern == "high_amount":
            amount = round(random.uniform(25000, 200000), 2)
            failed_login_attempts = random.randint(3, 8)
            transaction_velocity = random.randint(6, 18)
            account_age_days = random.randint(1, 180)

        elif fraud_pattern == "small_card_testing":
            amount = round(random.uniform(50, 1000), 2)
            failed_login_attempts = random.randint(1, 4)
            transaction_velocity = random.randint(10, 25)
            account_age_days = random.randint(1, 400)

        elif fraud_pattern == "new_account":
            amount = round(random.uniform(2000, 40000), 2)
            failed_login_attempts = random.randint(2, 7)
            transaction_velocity = random.randint(4, 15)
            account_age_days = random.randint(1, 45)

        elif fraud_pattern == "velocity_attack":
            amount = round(random.uniform(500, 15000), 2)
            failed_login_attempts = random.randint(1, 5)
            transaction_velocity = random.randint(15, 30)
            account_age_days = random.randint(30, 700)

        elif fraud_pattern == "foreign_transaction":
            amount = round(random.uniform(5000, 100000), 2)
            failed_login_attempts = random.randint(2, 6)
            transaction_velocity = random.randint(5, 20)
            account_age_days = random.randint(1, 500)

            country = random.choice(list(foreign_locations.keys()))
            city = random.choice(foreign_locations[country])
            international_transaction = 1

        else:
            # Stealth fraud: looks almost normal
            amount = round(random.uniform(500, 8000), 2)
            failed_login_attempts = random.randint(0, 3)
            transaction_velocity = random.randint(2, 8)
            account_age_days = random.randint(100, 1200)

        unusual_location = random.choices(
            [0, 1],
            weights=[25, 75]
        )[0]

        vpn_used = random.choices(
            [0, 1],
            weights=[45, 55]
        )[0]

        multiple_cards_used = random.choices(
            [0, 1],
            weights=[50, 50]
        )[0]

        previous_transactions_24h = random.randint(0, 20)

        new_device_login = random.choices(
            [0, 1],
            weights=[30, 70]
        )[0]

    # ==============================
    # Risk Score
    # ==============================

    risk_score = calculate_risk_score(
        amount,
        failed_login_attempts,
        unusual_location,
        vpn_used,
        multiple_cards_used,
        account_age_days,
        transaction_velocity,
        international_transaction,
        new_device_login,
        merchant_category
    )

    # ==============================
    # Record
    # ==============================

    record = {
        "Transaction_ID": f"TXN{i + 1:08d}",
        "Time": time_seconds,
        "Transaction_Date": transaction_date.strftime("%Y-%m-%d %H:%M:%S"),
        "Hour": hour,
        "Day_Of_Week": day_of_week,
        "Is_Weekend": is_weekend,
        "Is_Night_Transaction": is_night_transaction,
        "Amount": amount,
        "Transaction_Type": transaction_type,
        "Merchant_Category": merchant_category,
        "Device_Type": device_type,
        "City": city,
        "Country": country,
        "International_Transaction": international_transaction,
        "Failed_Login_Attempts": failed_login_attempts,
        "Previous_Transactions_24H": previous_transactions_24h,
        "Unusual_Location": unusual_location,
        "VPN_Used": vpn_used,
        "Multiple_Cards_Used": multiple_cards_used,
        "New_Device_Login": new_device_login,
        "Account_Age_Days": account_age_days,
        "Transaction_Velocity": transaction_velocity,
        "Risk_Score": risk_score,
        "Is_Fraud": is_fraud
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

print("High-level dataset generated successfully!")
print("----------------------------------------")
print(f"Total Records: {len(df)}")
print(f"Fraud Records: {df['Is_Fraud'].sum()}")
print(f"Legitimate Records: {(df['Is_Fraud'] == 0).sum()}")
print(f"Fraud Percentage: {round(df['Is_Fraud'].mean() * 100, 2)}%")
print(f"Saved at: {OUTPUT_FILE}")

print("\nClass Distribution:")
print(df["Is_Fraud"].value_counts())

print("\nAverage Values by Class:")
print(
    df.groupby("Is_Fraud")[
        [
            "Amount",
            "Failed_Login_Attempts",
            "Transaction_Velocity",
            "Account_Age_Days",
            "Risk_Score"
        ]
    ].mean()
)