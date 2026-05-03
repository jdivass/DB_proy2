import psycopg2 as psy
import os

def db_connection():
    try:
        connection = psy.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )
        print("6 - conexión exitosa")
        return connection
    except Exception as error:
        print("7 - error conexión:", error)
        return None