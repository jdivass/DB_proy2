import psycopg2 as psy
import os
from dotenv import dotenv_values

def db_connection():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.normpath(os.path.join(base_dir, "..", ".env"))

    config = dotenv_values(env_path, encoding="utf-8")

    try:
        connection = psy.connect(
            dbname=config.get("DB_NAME"),
            user=config.get("DB_USER"),
            password=config.get("DB_PASSWORD"),
            host=config.get("DB_HOST"),
            port=config.get("DB_PORT"),
        )
        return connection
    except Exception as error:
        print("7 - error conexión:", error)
        return None