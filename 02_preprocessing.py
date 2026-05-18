import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import (
    LabelEncoder,
    StandardScaler
)


# Create models folder
os.makedirs(
    "models",
    exist_ok=True
)

# Load Dataset
df = pd.read_csv(
    "dataset/synthetic_fraud_dataset.csv"
)

print("\nDataset Loaded Successfully!")


# Remove Duplicates
df = df.drop_duplicates()

print(
    f"\nDataset Shape After Removing Duplicates: "
    f"{df.shape}"
)


# Drop Unnecessary Columns
df = df.drop(
    columns=[
        "Transaction_ID",
        "Transaction_Date"
    ]
)


# Encode Categorical Columns
categorical_columns = [
    "Transaction_Type",
    "Merchant_Category",
    "Device_Type",
    "City",
    "Country"
]

label_encoders = {}

for column in categorical_columns:

    encoder = LabelEncoder()

    df[column] = encoder.fit_transform(
        df[column]
    )

    label_encoders[column] = encoder

print("\nCategorical Encoding Completed!")
joblib.dump(
    label_encoders,
    "models/label_encoders.pkl"
)

print("\nLabel Encoders Saved!")

# Features and Target
X = df.drop(
    "Is_Fraud",
    axis=1
)

y = df["Is_Fraud"]


# Save Feature Columns
feature_columns = X.columns.tolist()

joblib.dump(
    feature_columns,
    "models/feature_columns.pkl"
)

print("\nFeature Columns Saved!")


# Standard Scaling
scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

joblib.dump(
    scaler,
    "models/scaler.pkl"
)

print("\nScaler Saved!")


# Train Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# Save Processed Files
joblib.dump(
    X_train,
    "models/X_train.pkl"
)

joblib.dump(
    X_test,
    "models/X_test.pkl"
)

joblib.dump(
    y_train,
    "models/y_train.pkl"
)

joblib.dump(
    y_test,
    "models/y_test.pkl"
)

print("\nTrain-Test Data Saved!")


# Final Summary
print("\n========== PREPROCESSING COMPLETE ==========")

print(f"\nTraining Shape: {X_train.shape}")

print(f"Testing Shape: {X_test.shape}")

print("\nAll preprocessing files saved in:")
print("models/")