import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier


#-------------------------
# Load dataset
#-------------------------
data = pd.read_csv("dataset/creditcard.csv")

# Remove duplicates
data = data.drop_duplicates()


#---------------------------
# Feature and Target
#---------------------------

X = data.drop("Class", axis=1)
y = data["Class"]


#--------------------------
# Standardization
#--------------------------

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)


#----------------------
# Train Test Split
#----------------------

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled,
    y,
    test_size = 0.2,
    random_state = 42,
    stratify = y
)

#----------------------
# Model Selection
#----------------------
models = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42
    ),

    "Decision Tree": DecisionTreeClassifier(
        class_weight="balanced",
        random_state=42
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
 }

best_model = None
best_model_name = ""
best_f1 = 0


#-------------------------------
# Train and Evaluate Models
#-------------------------------

for name, model in models.items():
    print("\n=======================")
    print("Training:", name)
    print("=======================")

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print(classification_report(y_test, y_pred))
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("ROC-AUC Score:", roc_auc_score(y_test, y_prob))

    report = classification_report(
        y_test,
        y_pred,
        output_dict=True,
        zero_division=0
    )

    fraud_f1 = report["1"]["f1-score"]

    if fraud_f1 > best_f1:
        best_f1 = fraud_f1
        best_model = model
        best_model_name = name


# -------------------------------
# Save Best Model
# -------------------------------

os.makedirs("models", exist_ok=True)

joblib.dump(best_model, "models/fraud_model.pkl")
joblib.dump(scaler, "models/scaler.pkl")
joblib.dump(list(X.columns), "models/feature_columns.pkl")

print("\nBest Model:", best_model_name)
print("Best Fraud F1-score:", best_f1)
print("Model, scaler, and feature columns saved successfully!")