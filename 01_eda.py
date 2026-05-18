import os
import pandas as pd
import matplotlib.pyplot as plt

# create images folder automatically 
os.makedirs("static/images", exist_ok=True)

#load dataset
data = pd.read_csv("dataset/creditcard.csv")

# basic info
print("\nFIRST 5 ROWS: ")
print(data.head())

print("\nDATASET INFO: ")
print(data.info())

print("\nMISSING VALUES: ")
print(data.isnull().sum())

print("\nCLASS DISTRIBUTION: ")
print(data["Class"].value_counts())


# 1. FRAUD VS LEGITIMATE

class_counts = data["Class"].value_counts()

plt.figure(figsize=(6, 4))

plt.bar(
    ["Legitimate", "Fraud"],
    class_counts.values
)

plt.title("Fraud vs Legitimate Transaction")
plt.xlabel("Transaction Type")
plt.ylabel("Counts")

plt.tight_layout()

plt.savefig(
    "static/images/class_distribution.png"
)

plt.close()


# 2. AMOUNT DISTRIBUTION

plt.figure(figsize=(7, 4))

plt.hist(
    data["Amount"],
    bins = 50
)

plt.title("Transaction Amount Distribution")
plt.xlabel("Amount")
plt.ylabel("Frequency")

plt.tight_layout()

plt.savefig(
    "static/images/amount_distribution.png"
)

plt.close()


# FRAUD AMOUNT ANALYSIS

fraud_data = data[data["Class"] == 1]

plt.figure(figsize=(7,4))

plt.hist(
    fraud_data["Amount"],
    bins=40
)

plt.title("Fraud Transaction Amount Distribution")
plt.xlabel("Amount")
plt.ylabel("Frequency")

plt.tight_layout()

plt.savefig(
    "static/images/fraud_amount_distribution.png"
)

plt.close()


# 3.TIME PATTERN ANALYSIS

plt.figure(figsize=(7,4))

plt.hist(
    data["Time"],
    bins=50
)

plt.title("Transaction Time Distribution")
plt.xlabel("Time")
plt.ylabel("Frequency")

plt.tight_layout()

plt.savefig(
    "static/images/time_distribution.png"
)

plt.close()

print("\n EDA graphs saved successfully")