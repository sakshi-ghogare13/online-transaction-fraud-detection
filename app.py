from datetime import datetime 
import joblib
import pandas as pd
# add these imports
import time
import csv
from flask import Response
from flask import Flask, render_template, request, flash, redirect, url_for,session

from database import get_connection
from werkzeug.security import generate_password_hash, check_password_hash

model = joblib.load("models/fraud_model.pkl")
scaler = joblib.load("models/scaler.pkl")
feature_columns = joblib.load("models/feature_columns.pkl")

app = Flask(__name__)

app.secret_key = "fraud_detection_secret"

# Optional hardening for uploads
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


@app.route("/")
def home():
    return render_template("home.html")
# -----------------------------
# Home / Login
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

        cursor.close()
        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["user_id"]

            session["username"] = user["username"]

            flash(
                "Login successful.",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid email or password.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
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
            (username, email, password, "user")
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


@app.route("/predict", methods=["GET", "POST"])
def predict():

    result = None

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":

        amount = float(request.form["amount"])

        input_data = {
            col: 0
            for col in feature_columns
        }

        input_data["Amount"] = amount

        if "Time" in input_data:
            input_data["Time"] = int(time.time()) % 172800

        input_df = pd.DataFrame([input_data])

        input_df = input_df[feature_columns]

        input_scaled = scaler.transform(input_df)

        model_prediction = int(
            model.predict(input_scaled)[0]
        )

        risk_score = 72 if model_prediction == 1 else 18

        prediction_text = (
            "Fraud"
            if risk_score >= 60
            else "Legitimate"
        )

        risk_level = (
            "High Risk"
            if risk_score >= 60
            else "Low Risk"
        )

        result = {

            "prediction":
                "Fraud Transaction"
                if prediction_text == "Fraud"
                else "Genuine Transaction",

            "risk_score":
                risk_score,

            "risk_level":
                risk_level,

            "risk_class":
                "high"
                if prediction_text == "Fraud"
                else "low",

            "box_class":
                "prediction-fraud"
                if prediction_text == "Fraud"
                else "prediction-safe",

            "icon":
                "⚠️"
                if prediction_text == "Fraud"
                else "✅",

            "message":
                "This transaction looks suspicious."
                if prediction_text == "Fraud"
                else "This transaction appears safe."
        }

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

    return render_template(
        "predict.html",
        result=result
    )

# -----------------------------
# Batch Predict
# -----------------------------

@app.route("/batch-predict", methods=["GET", "POST"])
def batch_predict():

    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":

        file = request.files.get("file")

        if file is None or file.filename == "":
            flash("Please upload a CSV file.", "error")
            return redirect(url_for("batch_predict"))

        data = pd.read_csv(file)

        missing_columns = [
            col for col in feature_columns
            if col not in data.columns
        ]

        if missing_columns:
            flash("Missing columns: " + ", ".join(missing_columns), "error")
            return redirect(url_for("batch_predict"))

        input_df = data[feature_columns]
        input_scaled = scaler.transform(input_df)

        predictions = model.predict(input_scaled)

        batch_id = "BATCH_" + str(int(time.time()))

        results = []

        connection = get_connection()
        cursor = connection.cursor()

        for index, pred in enumerate(predictions):

            amount = float(data.iloc[index]["Amount"])

            prediction_text = "Fraud" if int(pred) == 1 else "Legitimate"

            risk_score = 72 if prediction_text == "Fraud" else 18

            risk_level = "High Risk" if prediction_text == "Fraud" else "Low Risk"

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
                "Time": data.iloc[index]["Time"],
                "Amount": amount,
                "Prediction": prediction_text,
                "Risk_Level": risk_level,
                "Risk_Score": risk_score
            })

        connection.commit()
        cursor.close()
        connection.close()

        flash("Batch prediction completed successfully.", "success")

        return render_template(
            "batch_predict.html",
            results=results
        )

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

        data = []

        headers = [
            "Transaction ID",
            "Amount",
            "Prediction",
            "Risk Score",
            "Risk Level",
            "Created At"
        ]

        data.append(headers)

        for row in transactions:

            data.append([
                row["transaction_id"],
                row["amount"],
                row["prediction"],
                row["risk_score"],
                row["risk_level"],
                row["created_at"]
            ])

        output = ""

        for line in data:
            output += ",".join(map(str, line)) + "\n"

        return output

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

        flash(
            "Access denied.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    cursor.execute(
        "SELECT COUNT(*) AS total_users FROM users"
    )
    total_users = cursor.fetchone()["total_users"]

    cursor.execute(
        "SELECT COUNT(*) AS total_predictions FROM transactions"
    )
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