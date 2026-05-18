import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# load dataset
data = pd.read_csv('dataset/creditcard.csv')


# original shape
print("\nORIGINAl DATASET SHAPE: ")
print(data.shape)
#ORIGINAl DATASET SHAPE: 
#(284807, 31)


# duplicate removel
duplicates =data.duplicated().sum()

print("\nTOTAL DUPLICATES: ")
print(duplicates)

data = data.drop_duplicates()

print("\nSHAPE AFTER REMOVING DUPLICATES: ")
print(data.shape)


# missing values

print("\nMISSING VALUES: ")
print(data.isnull().sum())


# feature and target

X = data.drop(
    "Class",
    axis=1
)

y = data["Class"]


# feature scaling

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

print("\nFEATURE SCALING COMPLETED")


# train_test Split

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled,
    y,
    test_size = 0.2,
    random_state = 42,
    stratify = y
)

print("\nTRAINING DATA SHAPE: ")
print(X_train.shape)

print("\nTESTING DATA SHAPE: ")
print(X_test.shape)


# fraud distribution

print("\nCLASS DISTIRBUTION: ")
print(y.value_counts())

print("\nPREPROCESSING COMPLETED SUCCESSFULLY")
