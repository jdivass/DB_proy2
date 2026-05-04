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
            cursor.execute("SELECT count(*) from producto")
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
    
    
@app.get("/productos")
async def get_productos():
    conn = db_connection()

    if conn is None:
        return {"error": "db connection failed"}

    cursor = conn.cursor()

    try:
        query = """
        SELECT 
            p.id_producto,
            p.nombre,
            p.descripcion,
            p.stock_actual,
            p.stock_minimo,
            p.precio_general,
            c.nombre AS categoria,
            pr.nombre AS proveedor,
            s.precio AS precio_compra
        FROM Producto p
        JOIN Categoria c ON p.id_categoria = c.id_categoria
        LEFT JOIN Suministra s ON p.id_producto = s.id_producto
        LEFT JOIN Proveedor pr ON s.id_proveedor = pr.id_proveedor
        ORDER BY p.id_producto;
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        productos = []

        for row in rows:
            producto = {
                "id": row[0],
                "nombre": row[1],
                "descripcion": row[2],
                "stock_actual": row[3],
                "stock_minimo": row[4],
                "precio_general": float(row[5]),
                "categoria": row[6],
                "proveedor": row[7],
                "precio_compra": float(row[8]) if row[8] else None
            }
            productos.append(producto)

        return productos

    except Exception as error:
        return {"error": str(error)}

    finally:
        cursor.close()
        conn.close()
