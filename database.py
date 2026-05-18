import mysql.connector

def get_connection():

    connection = mysql.connector.connect(
        host = "localhost",
        user = "root",
        password = "lotus",
        database = "fraud_detection_db"
    )

    return connection
    