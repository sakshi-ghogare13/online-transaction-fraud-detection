import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns 
import os

#create output folder

os.makedirs(
    "static/images",
    exist_ok=True
)

# load dataset
df = pd.read_csv(
    "dataset/synthetic_fraud_dataset.csv"
)

# basic info
print("\nDATASET INFO")
print(df.info())

print("\nFIRST 5 ROWS")
print(df.head())

print(df.isnull().sum())

print("\nDUPLICATES")
print(df.duplicated().sum())

print("\nFRAUD DISTRIBUTION")
print(df["Is_Fraud"].value_counts())


# Fraud distribution chart
plt.figure(figsize=(6,5))
sns.countplot(
    x="Is_Fraud",
    data=df
)

plt.title(
    "Fraud vs Legitimate Transactions"
)

plt.xticks(
    [0,1],
    ["Legitimate", "Fraud"]
)

plt.savefig(
    "static/images/class_distribution.png"
)

plt.close()


# amount distribution
plt.figure(figsize=(10,5))
sns.histplot(
    df["Amount"],
    bins=50,
    kde=True
)

plt.title(
    "Transaction Amount Distribution"
)

plt.savefig(
    "static/images/amount_distribution.png"
)

plt.close()


#Fraud Amount Distribution
fraud_df = df[
    df["Is_Fraud"] == 1
]

plt.figure(figsize=(10, 5))

sns.histplot(
    fraud_df["Amount"],
    bins=50,
    kde=True,
    color="red"
)

plt.title(
    "Fraud Transaction Amount Distribution"
)

plt.savefig(
    "static/images/fraud_amount_distribution.png"
)

plt.close()


# Time Distribution

plt.figure(figsize=(10, 5))

sns.histplot(
    df["Time"],
    bins=50,
    kde=True,
    color="green"
)

plt.title(
    "Transaction Time Distribution"
)

plt.savefig(
    "static/images/time_distribution.png"
)

plt.close()


# Correlation Heatmap

numeric_df = df.select_dtypes(
    include=["int64", "float64"]
)

plt.figure(figsize=(12, 8))

sns.heatmap(
    numeric_df.corr(),
    cmap="coolwarm"
)

plt.title(
    "Feature Correlation Heatmap"
)

plt.savefig(
    "static/images/correlation_heatmap.png"
)

plt.close()


# Summary
print("\nEDA Completed Successfully!")

print("\nGraphs saved in:")
print("static/images/")