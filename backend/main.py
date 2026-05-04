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
    

@app.get("/products")
async def get_products():
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

@app.get("/products/category/{category_name}")
async def get_products_by_category(category_name: str):
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
                p.precio_general,
                c.nombre as categoria
            FROM Producto p
            JOIN Categoria c ON p.id_categoria = c.id_categoria
            WHERE c.nombre = %s
        """

        cursor.execute(query, (category_name,))
        rows = cursor.fetchall()

        productos = []
        for row in rows:
            productos.append({
                "id": row[0],
                "nombre": row[1],
                "descripcion": row[2],
                "stock": row[3],
                "precio": float(row[4]),
                "categoria": row[5]
            })

        return {"productos": productos}

    except Exception as error:
        return {"error": str(error)}

    finally:
        cursor.close()
        conn.close()
        
@app.get("/sales")
async def get_ventas():
    conn = db_connection()

    if conn is None:
        return {"error": "db connection failed"}

    cursor = conn.cursor()

    try:
        query = """
            SELECT 
                v.id_venta,
                v.fecha,
                v.metodo_pago,
                c.id_cliente,
                c.nombre,
                c.apellido,
                e.id_empleado,
                e.nombre,
                e.apellido,
                p.id_producto,
                p.nombre,
                dv.cantidad,
                dv.precio_venta
            FROM Venta v
            JOIN Cliente c ON v.id_cliente = c.id_cliente
            JOIN Empleado e ON v.id_empleado = e.id_empleado
            JOIN Detalle_venta dv ON v.id_venta = dv.id_venta
            JOIN Producto p ON dv.id_producto = p.id_producto
            ORDER BY v.id_venta;
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        ventas = {}

        for row in rows:
            id_venta = row[0]

            if id_venta not in ventas:
                ventas[id_venta] = {
                    "id_venta": id_venta,
                    "fecha": row[1],
                    "metodo_pago": row[2],
                    "cliente": {
                        "id": row[3],
                        "nombre": row[4],
                        "apellido": row[5]
                    },
                    "empleado": {
                        "id": row[6],
                        "nombre": row[7],
                        "apellido": row[8]
                    },
                    "productos": [],
                    "total": 0
                }

            cantidad = row[11]
            precio = float(row[12])

            ventas[id_venta]["productos"].append({
                "id_producto": row[9],
                "nombre": row[10],
                "cantidad": cantidad,
                "precio_venta": precio
            })

            # 🔥 acumulamos total
            ventas[id_venta]["total"] += cantidad * precio

        return {"ventas": list(ventas.values())}

    except Exception as error:
        return {"error": str(error)}

    finally:
        cursor.close()
        conn.close()

@app.get("/products/minimun_stock")
async def get_productos_stock_ok_subquery():
    conn = db_connection()

    if conn is None:
        return {"error": "db connection failed"}

    cursor = conn.cursor()

    try:
        query = """
            SELECT 
                p.id_producto,
                p.nombre,
                p.stock_actual,
                p.stock_minimo,
                c.nombre AS categoria
            FROM Producto p
            JOIN Categoria c ON p.id_categoria = c.id_categoria
            WHERE p.id_producto IN (
                SELECT p2.id_producto
                FROM Producto p2
                WHERE p2.stock_actual > p2.stock_minimo
            );
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        productos = []
        for row in rows:
            productos.append({
                "id": row[0],
                "nombre": row[1],
                "stock_actual": row[2],
                "stock_minimo": row[3],
                "categoria": row[4]
            })

        return {"productos": productos}

    except Exception as error:
        return {"error": str(error)}

    finally:
        cursor.close()
        conn.close()

@app.get("/clients/top")
async def clientes_top():
    conn = db_connection()
    if conn is None:
        return {"error": "db connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                c.id_cliente,
                c.nombre,
                c.apellido,
                SUM(dv.cantidad * dv.precio_venta) AS total_gastado
            FROM Cliente c
            JOIN Venta v ON c.id_cliente = v.id_cliente
            JOIN Detalle_venta dv ON v.id_venta = dv.id_venta
            GROUP BY c.id_cliente
            HAVING SUM(dv.cantidad * dv.precio_venta) > (
                SELECT AVG(total_cliente)
                FROM (
                    SELECT SUM(dv2.cantidad * dv2.precio_venta) AS total_cliente
                    FROM Venta v2
                    JOIN Detalle_venta dv2 ON v2.id_venta = dv2.id_venta
                    GROUP BY v2.id_cliente
                ) sub
            );
        """)

        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "id_cliente": row[0],
                "nombre": row[1],
                "apellido": row[2],
                "total_gastado": float(row[3])
            })

        return result

    except Exception as error:
        return {"error": str(error)}

    finally:
        cursor.close()
        conn.close()

@app.get("/products/top-product_incomes")
async def top_productos_ingresos():
    conn = db_connection()
    if conn is None:
        return {"error": "db connection failed"}

    cursor = conn.cursor()
    try:
        cursor.execute("""
            WITH ventas_producto AS (
                SELECT 
                    dv.id_producto,
                    SUM(dv.cantidad * dv.precio_venta) AS ingreso_total
                FROM Detalle_venta dv
                GROUP BY dv.id_producto
            )

            SELECT 
                p.id_producto,
                p.nombre,
                p.descripcion,
                p.precio_general,
                vp.ingreso_total
            FROM ventas_producto vp
            JOIN Producto p ON vp.id_producto = p.id_producto
            ORDER BY vp.ingreso_total DESC
            LIMIT 10;
        """)

        rows = cursor.fetchall()

        return [
            {
                "id_producto": r[0],
                "nombre": r[1],
                "descripcion": r[2],
                "precio": float(r[3]),
                "ingreso_total": float(r[4])
            }
            for r in rows
        ]

    except Exception as error:
        return {"error": str(error)}

    finally:
        cursor.close()
        conn.close()