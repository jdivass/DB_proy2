from fastapi import FastAPI
from dbConnection import db_connection

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/test")
async def test():
    conn = db_connection()
    if (conn != None):
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1")
            row = cursor.fetchone()
            value = row[0]
        except Exception as error:
            return {"error": str(error)}
        finally:
            cursor.close()
            conn.close()
        return {"select": value}
    else:
        return {"error": "db connection failed"}
