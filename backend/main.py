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

        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        id_producto = row[0]
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

        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        id_venta = row[0]

        for item in data.productos:

            cursor.execute("""
                SELECT stock_actual FROM Producto WHERE id_producto = %s;
            """, (item.id_producto,))

            stock = cursor.fetchone()

            if stock is None:
                raise HTTPException(status_code=404, detail=f"Product {item.id_producto} does not exist")

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
        return {"message": "Sale created", "id_venta": id_venta}

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
        row1 =  cursor.fetchone()
        if row1 is None:
            raise HTTPException(status_code=404, detail="Products not found")
        total_productos = row1[0]

        cursor.execute("SELECT COUNT(*) FROM Venta;")
        row2 =  cursor.fetchone()
        if row2 is None:
            raise HTTPException(status_code=404, detail="Sales not found")
        total_ventas = row2[0]

        cursor.execute("""
            SELECT COALESCE(SUM(cantidad * precio_venta), 0)
            FROM Detalle_venta;
        """)
        row3 = cursor.fetchone()
        if row3 is None:
            raise HTTPException(status_code=404, detail="Sale detail not found")
        ingresos = float(row3[0])

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


@app.get("/dashboard")
async def get_dashboard():
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()

    try:
        # Métricas generales
        cursor.execute("SELECT COUNT(*) FROM Producto;")
        row= cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Products not found")
        total_productos = row[0]

        cursor.execute("SELECT COUNT(*) FROM Cliente;")
        row2 = cursor.fetchone()
        if row2 is None:
            raise HTTPException(status_code=404, detail="Clients not found")
        total_clientes = row2[0]

        cursor.execute("SELECT COUNT(*) FROM Venta;")
        row3 = cursor.fetchone()
        if row3 is None:
            raise HTTPException(status_code=404, detail="Sales not found")
        total_ventas = row3[0]

        cursor.execute("""
            SELECT COALESCE(SUM(cantidad * precio_venta), 0)
            FROM Detalle_venta;
        """)
        row4 = cursor.fetchone()
        if row4 is None:
            raise HTTPException(status_code=404, detail="Sale detail not found")
        ingresos_totales = float(row4[0])

       # Productos que generan más ingresos
        cursor.execute("""
            SELECT 
                p.id_producto,
                p.nombre,
                SUM(dv.cantidad * dv.precio_venta) AS ingreso
            FROM Producto p
            JOIN Detalle_venta dv ON p.id_producto = dv.id_producto
            GROUP BY p.id_producto
            ORDER BY ingreso DESC
            LIMIT 5;
        """)

        top_productos = [
            {
                "id_producto": r[0],
                "nombre": r[1],
                "ingreso": float(r[2])
            }
            for r in cursor.fetchall()
        ]

        # Mejores clientes
        cursor.execute("""
            SELECT 
                c.id_cliente,
                c.nombre,
                c.apellido,
                SUM(dv.cantidad * dv.precio_venta) AS total
            FROM Cliente c
            JOIN Venta v ON c.id_cliente = v.id_cliente
            JOIN Detalle_venta dv ON v.id_venta = dv.id_venta
            GROUP BY c.id_cliente
            ORDER BY total DESC
            LIMIT 5;
        """)

        top_clientes = [
            {
                "id_cliente": r[0],
                "nombre": r[1],
                "apellido": r[2],
                "total_gastado": float(r[3])
            }
            for r in cursor.fetchall()
        ]

        # Últimas ventas
        cursor.execute("""
            SELECT 
                v.id_venta,
                v.fecha,
                c.nombre,
                c.apellido,
                SUM(dv.cantidad * dv.precio_venta) as total
            FROM Venta v
            JOIN Cliente c ON v.id_cliente = c.id_cliente
            JOIN Detalle_venta dv ON v.id_venta = dv.id_venta
            GROUP BY v.id_venta, c.nombre, c.apellido
            ORDER BY v.fecha DESC
            LIMIT 5;
        """)

        ultimas_ventas = [
            {
                "id_venta": r[0],
                "fecha": r[1],
                "cliente": f"{r[2]} {r[3]}",
                "total": float(r[4])
            }
            for r in cursor.fetchall()
        ]

        # Stock bajo
        cursor.execute("""
            SELECT 
                id_producto,
                nombre,
                stock_actual,
                stock_minimo
            FROM Producto
            WHERE stock_actual <= stock_minimo;
        """)

        alertas_stock = [
            {
                "id_producto": r[0],
                "nombre": r[1],
                "stock_actual": r[2],
                "stock_minimo": r[3]
            }
            for r in cursor.fetchall()
        ]

        return {
            "resumen": {
                "total_productos": total_productos,
                "total_clientes": total_clientes,
                "total_ventas": total_ventas,
                "ingresos_totales": ingresos_totales
            },
            "top_productos": top_productos,
            "top_clientes": top_clientes,
            "ultimas_ventas": ultimas_ventas,
            "alertas_stock": alertas_stock
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

@app.get("/clients")
async def get_clients():
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_cliente, nombre, apellido, telefono, correo, nit FROM Cliente;")

        return [
            {
                "id_cliente": r[0],
                "nombre": r[1],
                "apellido": r[2],
                "telefono": r[3],
                "correo": r[4],
                "nit": r[5]
            }
            for r in cursor.fetchall()
        ]

    finally:
        cursor.close()
        conn.close()

@app.get("/clients/{id}")
async def get_client(id: int):
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id_cliente, nombre, apellido, telefono, correo, nit
            FROM Cliente
            WHERE id_cliente = %s;
        """, (id,))

        row = cursor.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        return {
            "id_cliente": row[0],
            "nombre": row[1],
            "apellido": row[2],
            "telefono": row[3],
            "correo": row[4],
            "nit": row[5]
        }

    finally:
        cursor.close()
        conn.close()

@app.post("/clients")
async def create_client(data: dict):
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO Cliente (nombre, apellido, telefono, correo, nit)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_cliente;
        """, (
            data["nombre"],
            data["apellido"],
            data.get("telefono"),
            data.get("correo"),
            data.get("nit")
        ))

        conn.commit()
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Client not found")
        return {"id_cliente": row[0]}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

@app.put("/clients/{id}")
async def update_client(id: int, data: dict):
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE Cliente
            SET nombre=%s, apellido=%s, telefono=%s, correo=%s, nit=%s
            WHERE id_cliente=%s;
        """, (
            data["nombre"],
            data["apellido"],
            data.get("telefono"),
            data.get("correo"),
            data.get("nit"),
            id
        ))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Client not found")

        conn.commit()
        return {"message": "Client updated"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

@app.delete("/clients/{id}")
async def delete_client(id: int):
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Cliente WHERE id_cliente=%s;", (id,))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Client not found")

        conn.commit()
        return {"message": "Client deleted"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()