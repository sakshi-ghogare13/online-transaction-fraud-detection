from logger import logger
import time
import joblib
import pandas as pd

from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    session,
    Response
)

from database import get_connection
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "fraud_detection_secret"

# Optional hardening for uploads
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

logger.info("Fraud detection app started")

# -----------------------------
# Load ML artifacts
# -----------------------------

model = joblib.load("model_artifacts/final_fraud_model.pkl")
scaler = joblib.load("model_artifacts/scaler.pkl")
feature_columns = joblib.load("model_artifacts/selected_features.pkl")
label_encoders = joblib.load("model_artifacts/label_encoders.pkl")

logger.info("Model, scaler, feature columns and label encoders loaded successfully")


# -----------------------------
# Helper Functions
# -----------------------------

def get_default_value(column_name):
    """
    Gives safe default values for model features that are not present
    in the single prediction form or uploaded CSV.
    """

    defaults = {
        "Time": int(time.time()) % 31536000,
        "Amount": 0.0,

        # Categorical defaults
        "Transaction_Type": "UPI",
        "Merchant_Category": "Shopping",
        "Device_Type": "Android",
        "City": "Pune",
        "Country": "India",
        "Day_Of_Week": 0,

        # Numerical / binary defaults
        "International_Transaction": 0,
        "New_Device_Login": 0,
        "Risk_Score": 0.0,
        "Failed_Login_Attempts": 0,
        "Previous_Transactions_24H": 0,
        "Unusual_Location": 0,
        "VPN_Used": 0,
        "Multiple_Cards_Used": 0,
        "Account_Age_Days": 365,
        "Transaction_Velocity": 1
    }

    return defaults.get(column_name, 0)


def fix_common_category_mismatch(column, value):
    """
    Fixes mismatch between form values and training values.
    Example: form may send Transfer, but training data has Bank Transfer.
    """

    value = str(value).strip()

    if column == "Transaction_Type" and value == "Transfer":
        value = "Bank Transfer"

    return value

def get_risk_level(risk_score):
    if risk_score >= 70:
        return "High Risk"
    elif risk_score >= 40:
        return "Medium Risk"
    else:
        return "Low Risk"


def prepare_model_input(input_data):
    """
    Converts user input into the exact format expected by the trained model.
    This prevents:
    - KeyError: missing columns not in index
    - ValueError: unseen labels
    - Wrong column order
    """

    # Add missing model features
    for column in feature_columns:
        if column not in input_data:
            input_data[column] = get_default_value(column)

    # Encode categorical columns safely
    for column, encoder in label_encoders.items():

        if column in input_data:

            value = fix_common_category_mismatch(column, input_data[column])

            if value not in encoder.classes_:
                allowed_values = ", ".join(map(str, encoder.classes_))

                logger.error(
                    f"Unknown label '{value}' for column '{column}'. "
                    f"Allowed values: {allowed_values}"
                )

                raise ValueError(
                    f"Invalid value '{value}' for {column}. "
                    f"Allowed values: {allowed_values}"
                )

            input_data[column] = encoder.transform([value])[0]

    input_df = pd.DataFrame([input_data])

    # Add any column that is still missing after DataFrame creation
    for column in feature_columns:
        if column not in input_df.columns:
            input_df[column] = get_default_value(column)

    # Keep only training columns and correct order
    input_df = input_df[feature_columns]

    return input_df


def prepare_batch_input(data):
    """
    Prepares uploaded CSV data for batch prediction using the exact
    model feature columns.
    """

    data = data.copy()

    # Drop unwanted columns if present
    data = data.drop(
        columns=[
            "Transaction_ID",
            "Transaction_Date",
            "Is_Fraud"
        ],
        errors="ignore"
    )

    # Add missing columns with safe defaults
    for column in feature_columns:
        if column not in data.columns:
            data[column] = get_default_value(column)

    # Encode categorical columns safely
    for column, encoder in label_encoders.items():

        if column in data.columns:

            data[column] = data[column].astype(str).str.strip()

            if column == "Transaction_Type":
                data[column] = data[column].replace({
                    "Transfer": "Bank Transfer"
                })

            # Replace blank values with default
            data[column] = data[column].replace({
                "": get_default_value(column),
                "nan": get_default_value(column),
                "None": get_default_value(column)
            })

            unknown_values = sorted(
                set(data[column].astype(str)) - set(map(str, encoder.classes_))
            )

            if unknown_values:
                allowed_values = ", ".join(map(str, encoder.classes_))

                logger.error(
                    f"Unknown values in column '{column}': "
                    f"{unknown_values}. Allowed values: {allowed_values}"
                )

                raise ValueError(
                    f"Unknown values in column {column}: "
                    f"{', '.join(map(str, unknown_values))}. "
                    f"Allowed values: {allowed_values}"
                )

            data[column] = encoder.transform(data[column])

    # Keep only training columns and correct order
    input_df = data[feature_columns]

    return input_df, data


# -----------------------------
# Home
# -----------------------------

@app.route("/")
def home():
    return render_template("home.html")


# -----------------------------
# Login
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT * FROM users
            WHERE email=%s
            """,
            (email,)
        )

        user = cursor.fetchone()

        if user and check_password_hash(user["password"], password):

            if user["email"] == "sakshighogare1312@gmail.com":
                cursor.execute(
                    "UPDATE users SET role=%s WHERE email=%s",
                    ("admin", user["email"])
                )
                connection.commit()
                user["role"] = "admin"

            session["user_id"] = user["user_id"]
            session["username"] = user["username"]

            cursor.close()
            connection.close()

            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))

        cursor.close()
        connection.close()

        flash("Invalid email or password.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")

# -----------------------------
# Register
# -----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        # Make only your email admin
        role = "admin" if email == "sakshighogare1312@gmail.com" else "user"

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            connection.close()

            flash("Email already registered. Please login.", "error")
            return redirect(url_for("register"))

        cursor.execute(
            """
            INSERT INTO users(username, email, password, role)
            VALUES(%s, %s, %s, %s)
            """,
            (username, email, password, role)
        )

        connection.commit()

        cursor.close()
        connection.close()

        flash("Account created successfully. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# -----------------------------
# Dashboard
# -----------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    user_id = session["user_id"]

    cursor.execute(
        "SELECT COUNT(*) AS total FROM transactions WHERE user_id=%s",
        (user_id,)
    )
    total_transactions = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT COUNT(*) AS fraud
        FROM transactions
        WHERE user_id=%s AND prediction='Fraud'
        """,
        (user_id,)
    )
    fraud_detected = cursor.fetchone()["fraud"]

    cursor.execute(
        """
        SELECT COUNT(*) AS legitimate
        FROM transactions
        WHERE user_id=%s AND prediction='Legitimate'
        """,
        (user_id,)
    )
    legitimate = cursor.fetchone()["legitimate"]

    cursor.execute(
        """
        SELECT COUNT(*) AS high_risk
        FROM transactions
        WHERE user_id=%s AND risk_level='High Risk'
        """,
        (user_id,)
    )
    high_risk = cursor.fetchone()["high_risk"]

    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE user_id=%s
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (user_id,)
    )
    recent_transactions = cursor.fetchall()

    cursor.execute(
        """
        SELECT DATE(created_at) AS day,
               COUNT(*) AS total
        FROM transactions
        WHERE user_id=%s
        GROUP BY DATE(created_at)
        ORDER BY day ASC
        """,
        (user_id,)
    )
    trend_data = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "dashboard.html",
        total_transactions=total_transactions,
        fraud_detected=fraud_detected,
        legitimate=legitimate,
        high_risk=high_risk,
        recent_transactions=recent_transactions,
        trend_data=trend_data
    )


# -----------------------------
# Single Prediction
# -----------------------------

@app.route("/predict", methods=["GET", "POST"])
def predict():

    result = None

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":

        try:
            logger.info("Prediction request received")

            amount = float(request.form["amount"])
            country = request.form["country"]
            device_type = request.form["device_type"]

            failed_login_attempts = 4 if amount > 20000 else 1
            previous_transactions_24h = 2 if amount > 20000 else 5
            unusual_location = 1 if country != "India" else 0
            vpn_used = 1 if country != "India" else 0
            multiple_cards_used = 1 if amount > 25000 else 0
            account_age_days = 60 if amount > 20000 else 600
            transaction_velocity = 12 if amount > 20000 else 3

            if device_type == "ATM" and amount > 15000:
                failed_login_attempts = 5
                transaction_velocity = 10

            # Features collected from form + auto-generated features
            input_data = {

                "Time": int(time.time()) % 31536000,
                "Amount": amount,
                "Transaction_Type": request.form["transaction_type"],
                "Merchant_Category": request.form["merchant_category"],
                "Device_Type": device_type,
                "City": request.form["city"],
                "Country": country,

                "Failed_Login_Attempts": failed_login_attempts,
                "Previous_Transactions_24H": previous_transactions_24h,
                "Unusual_Location": unusual_location,
                "VPN_Used": vpn_used,
                "Multiple_Cards_Used": multiple_cards_used,
                "Account_Age_Days": account_age_days,
                "Transaction_Velocity": transaction_velocity,

                "Day_Of_Week": pd.Timestamp.now().weekday(),
                "International_Transaction": 1 if country != "India" else 0,
                "New_Device_Login": 1 if amount > 20000 else 0,
                "Risk_Score": 0.0
            }

            input_df = prepare_model_input(input_data)
            input_scaled = scaler.transform(input_df)

            probability = model.predict_proba(input_scaled)[0]
            fraud_percentage = round(probability[1] * 100, 2)

            model_prediction = int(model.predict(input_scaled)[0])

            prediction_text = "Fraud" if model_prediction == 1 else "Legitimate"
            logger.info(f"Prediction result: {prediction_text}")

            risk_score = fraud_percentage
            risk_level = get_risk_level(risk_score)
            logger.info(f"Fraud probability: {risk_score}%")
            logger.info(f"Risk level: {risk_level}")

            result = {
                "prediction": (
                    "Fraud Transaction"
                    if prediction_text == "Fraud"
                    else "Genuine Transaction"
                ),
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_class": "high" if prediction_text == "Fraud" else "low",
                "box_class": (
                    "prediction-fraud"
                    if prediction_text == "Fraud"
                    else "prediction-safe"
                ),
                "icon": "⚠️" if prediction_text == "Fraud" else "✅",
                "message": (
                    "This transaction pattern looks suspicious."
                    if prediction_text == "Fraud"
                    else "This transaction appears safe."
                )
            }

            logger.info("Saving transaction to database")

            connection = get_connection()
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO transactions(
                    user_id,
                    amount,
                    prediction,
                    risk_score,
                    risk_level,
                    batch_id
                )
                VALUES(%s, %s, %s, %s, %s, %s)
                """,
                (
                    session["user_id"],
                    amount,
                    prediction_text,
                    risk_score,
                    risk_level,
                    None
                )
            )

            connection.commit()
            cursor.close()
            connection.close()

        except ValueError as e:
            logger.error(f"Prediction validation error: {e}")
            flash(str(e), "error")

        except Exception as e:
            logger.exception("Prediction failed")
            flash(f"Prediction failed: {e}", "error")

    return render_template("predict.html", result=result)


# -----------------------------
# Batch Prediction
# -----------------------------

@app.route("/batch-predict", methods=["GET", "POST"])
def batch_predict():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":

        try:
            logger.info("Batch prediction request received")

            file = request.files.get("file")

            if file is None or file.filename == "":
                logger.warning("No CSV file uploaded")
                flash("Please upload a CSV file.", "error")
                return redirect(url_for("batch_predict"))

            logger.info(f"Uploaded file: {file.filename}")

            data = pd.read_csv(file)
            logger.info("CSV file loaded successfully")

            input_df, clean_data = prepare_batch_input(data)

            input_scaled = scaler.transform(input_df)

            predictions = model.predict(input_scaled)
            probabilities = model.predict_proba(input_scaled)

            logger.info("Batch prediction completed")

            batch_id = "BATCH_" + str(int(time.time()))
            logger.info(f"Generated Batch ID: {batch_id}")

            results = []

            connection = get_connection()
            cursor = connection.cursor()

            for index, pred in enumerate(predictions):

                logger.info(f"Processing transaction {index + 1}")

                amount = float(clean_data.iloc[index]["Amount"])

                prediction_text = "Fraud" if int(pred) == 1 else "Legitimate"

                fraud_percentage = round(probabilities[index][1] * 100, 2)

                risk_score = fraud_percentage
                risk_level = get_risk_level(risk_score)

                logger.info(f"Prediction: {prediction_text}")
                logger.info(f"Risk Score: {risk_score}%")
                logger.info(f"Risk Level: {risk_level}")
                cursor.execute(
                    """
                    INSERT INTO transactions(
                        user_id,
                        amount,
                        prediction,
                        risk_score,
                        risk_level,
                        batch_id
                    )
                    VALUES(%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        session["user_id"],
                        amount,
                        prediction_text,
                        risk_score,
                        risk_level,
                        batch_id
                    )
                )

                results.append({
                    "Amount": amount,
                    "Prediction": prediction_text,
                    "Risk_Level": risk_level,
                    "Risk_Score": risk_score
                })

            connection.commit()
            logger.info("Batch transactions saved successfully")

            cursor.close()
            connection.close()
            logger.info("Database connection closed")

            flash("Batch prediction completed successfully.", "success")

            return render_template(
                "batch_predict.html",
                results=results
            )

        except ValueError as e:
            logger.error(f"Batch prediction validation error: {e}")
            flash(str(e), "error")
            return redirect(url_for("batch_predict"))

        except Exception as e:
            logger.exception("Batch prediction failed")
            flash(f"Batch prediction failed: {e}", "error")
            return redirect(url_for("batch_predict"))

    return render_template("batch_predict.html")


# -----------------------------
# History
# -----------------------------

@app.route("/history")
def history():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    )

    transactions = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "history.html",
        transactions=transactions
    )


# -----------------------------
# Export History
# -----------------------------

@app.route("/export-history")
def export_history():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    )

    transactions = cursor.fetchall()

    cursor.close()
    connection.close()

    def generate_csv():

        headers = [
            "Transaction ID",
            "Amount",
            "Prediction",
            "Risk Score",
            "Risk Level",
            "Created At"
        ]

        lines = [",".join(headers)]

        for row in transactions:
            lines.append(
                ",".join(
                    map(
                        str,
                        [
                            row["transaction_id"],
                            row["amount"],
                            row["prediction"],
                            row["risk_score"],
                            row["risk_level"],
                            row["created_at"]
                        ]
                    )
                )
            )

        return "\n".join(lines)

    return Response(
        generate_csv(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=prediction_history.csv"
        }
    )


# -----------------------------
# Admin
# -----------------------------

@app.route("/admin")
def admin():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE user_id=%s
        """,
        (session["user_id"],)
    )

    current_user = cursor.fetchone()

    if current_user["role"] != "admin":

        cursor.close()
        connection.close()

        flash("Access denied.", "error")
        return redirect(url_for("dashboard"))

    cursor.execute("SELECT COUNT(*) AS total_users FROM users")
    total_users = cursor.fetchone()["total_users"]

    cursor.execute("SELECT COUNT(*) AS total_predictions FROM transactions")
    total_predictions = cursor.fetchone()["total_predictions"]

    cursor.execute(
        """
        SELECT COUNT(*) AS total_fraud
        FROM transactions
        WHERE prediction='Fraud'
        """
    )
    total_fraud = cursor.fetchone()["total_fraud"]

    cursor.execute(
        """
        SELECT t.*, u.username, u.email
        FROM transactions t
        JOIN users u
        ON t.user_id = u.user_id
        ORDER BY t.created_at DESC
        LIMIT 5
        """
    )

    latest_predictions = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin.html",
        total_users=total_users,
        total_predictions=total_predictions,
        total_fraud=total_fraud,
        latest_predictions=latest_predictions
    )


# -----------------------------
# Logout
# -----------------------------

@app.route("/logout")
def logout():

    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))


# -----------------------------
# Run Flask
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)
