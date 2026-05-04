from fastapi import FastAPI, HTTPException
from dbConnection import db_connection
from models import ProductCreate, ProductUpdate, SaleCreate

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "API running"}


@app.get("/test")
async def test():
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT count(*) FROM producto")
        return {"count": cursor.fetchone()[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/productos")
async def get_productos():
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM vista_productos;")
        rows = cursor.fetchall()

        return [
            {
                "id_producto": r[0],
                "nombre": r[1],
                "descripcion": r[2],
                "precio": float(r[3]),
                "stock_actual": r[4],
                "stock_minimo": r[5],
                "categoria": r[6],
                "estado_stock": r[7]
            }
            for r in rows
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.get("/products/{id}")
async def get_product(id: int):
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM vista_productos WHERE id_producto = %s;", (id,))
        row = cursor.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        return {
            "id_producto": row[0],
            "nombre": row[1],
            "descripcion": row[2],
            "precio": float(row[3]),
            "stock_actual": row[4],
            "stock_minimo": row[5],
            "categoria": row[6],
            "estado_stock": row[7]
        }

    finally:
        cursor.close()
        conn.close()


@app.post("/products")
async def create_product(data: ProductCreate):
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Producto 
            (nombre, descripcion, stock_actual, stock_minimo, precio_general, id_categoria)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_producto;
        """, (
            data.nombre,
            data.descripcion,
            data.stock_actual,
            data.stock_minimo,
            data.precio,
            data.id_categoria
        ))

        id_producto = cursor.fetchone()[0]
        conn.commit()

        return {"message": "Producto creado", "id": id_producto}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


@app.put("/products/{id}")
async def update_product(id: int, data: ProductUpdate):
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()

    try:
        fields = []
        values = []

        for key, value in data.dict(exclude_unset=True).items():
            if key == "precio":
                fields.append("precio_general = %s")
            else:
                fields.append(f"{key} = %s")
            values.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        values.append(id)

        query = f"""
            UPDATE Producto
            SET {', '.join(fields)}
            WHERE id_producto = %s;
        """

        cursor.execute(query, tuple(values))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        conn.commit()
        return {"message": "Producto actualizado"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

@app.delete("/products/{id}")
async def delete_product(id: int):
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Producto WHERE id_producto = %s;", (id,))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        conn.commit()
        return {"message": "Producto eliminado"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


@app.post("/sale")
async def create_sale(data: SaleCreate):
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()

    try:
        conn.autocommit = False

        cursor.execute("""
            INSERT INTO Venta (id_cliente, id_empleado, metodo_pago)
            VALUES (%s, %s, %s)
            RETURNING id_venta;
        """, (data.id_cliente, data.id_empleado, data.metodo_pago))

        id_venta = cursor.fetchone()[0]

        for item in data.productos:

            cursor.execute("""
                SELECT stock_actual FROM Producto WHERE id_producto = %s;
            """, (item.id_producto,))

            stock = cursor.fetchone()

            if stock is None:
                raise HTTPException(status_code=404, detail=f"Producto {item.id_producto} no existe")

            if stock[0] < item.cantidad:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente para producto {item.id_producto}"
                )

            cursor.execute("""
                INSERT INTO Detalle_venta (id_venta, id_producto, cantidad, precio_venta)
                VALUES (%s, %s, %s, %s);
            """, (
                id_venta,
                item.id_producto,
                item.cantidad,
                item.precio
            ))

            cursor.execute("""
                UPDATE Producto
                SET stock_actual = stock_actual - %s
                WHERE id_producto = %s;
            """, (item.cantidad, item.id_producto))

        conn.commit()
        return {"message": "Venta creada", "id_venta": id_venta}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


@app.get("/stats")
async def get_stats():
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM Producto;")
        total_productos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Venta;")
        total_ventas = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COALESCE(SUM(cantidad * precio_venta), 0)
            FROM Detalle_venta;
        """)
        ingresos = float(cursor.fetchone()[0])

        return {
            "total_productos": total_productos,
            "total_ventas": total_ventas,
            "ingresos_totales": ingresos
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()