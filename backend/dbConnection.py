import psycopg2 as psy
import os
import time


def db_connection(retries=10, delay=2):
    for attempt in range(1, retries + 1):
        try:
            print(f"Attempt {attempt} to connect to the DB")

            connection = psy.connect(
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                database=os.getenv("DB_NAME")
            )

            print("Successfull connection to the DB")
            return connection

        except Exception as error:
            print(f"Error in attempt {attempt}: {error}")

            if attempt == retries:
                print("Couldn't connect to the DB after many tries")
                return None

            time.sleep(delay)