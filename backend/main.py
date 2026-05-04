from fastapi import FastAPI, HTTPException
from dbConnection import db_connection
from typing import List
from models import (
    ProductCreate, ProductUpdate,
    ClientCreate, ClientUpdate, ClientResponse,
    SaleCreate, SaleResponse, ProductResponse, SaleProductResponse
)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],

)
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
        return {"count": cursor.fetchone()[0]} # pyright: ignore[reportOptionalSubscript]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()


@app.get("/products", response_model=List[ProductResponse])
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


@app.post("/products", response_model=ProductResponse)
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

        cursor.execute("SELECT * FROM vista_productos WHERE id_producto = %s;", (id_producto,))
        product = cursor.fetchone()
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found after insert")

        return {
            "id_producto":  product[0],
            "nombre":       product[1],
            "descripcion":  product[2],
            "precio":       float(product[3]),
            "stock_actual": product[4],
            "stock_minimo": product[5],
            "categoria":    product[6],
            "estado_stock": product[7],
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


@app.put("/products/{id}", response_model=ProductResponse)
async def update_product(id: int, data: ProductUpdate):
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()

    try:
        fields = []
        values = []

        for key, value in data.model_dump(exclude_unset=True).items():
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

        cursor.execute("SELECT * FROM vista_productos WHERE id_producto = %s;", (id,))
        product = cursor.fetchone()
        if product is None:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        return {
            "id_producto":  product[0],
            "nombre":       product[1],
            "descripcion":  product[2],
            "precio":       float(product[3]),
            "stock_actual": product[4],
            "stock_minimo": product[5],
            "categoria":    product[6],
            "estado_stock": product[7],
        }

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


@app.post("/sales")
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
            SELECT stock_actual, precio_general 
            FROM Producto 
            WHERE id_producto = %s;
        """, (item.id_producto,))

            producto = cursor.fetchone()

            if producto is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item.id_producto} does not exist"
                )

            stock_actual = producto[0]
            precio_real = float(producto[1])

            if stock_actual < item.cantidad:
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
                precio_real
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
        conn.autocommit=True
        cursor.close()
        conn.close()

@app.get("/stats")
async def get_stats():
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM Producto) AS total_productos,
                (SELECT COUNT(*) FROM Venta) AS total_ventas,
                (
                    SELECT COALESCE(SUM(cantidad * precio_venta), 0)
                    FROM Detalle_venta
                ) AS ingresos_totales;
        """)

        row = cursor.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Stats not found")

        return {
            "total_productos": row[0],
            "total_ventas": row[1],
            "ingresos_totales": float(row[2])
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
        cursor.execute("""
            WITH resumen AS (
                SELECT 
                    (SELECT COUNT(*) FROM Producto) AS total_productos,
                    (SELECT COUNT(*) FROM Cliente) AS total_clientes,
                    (SELECT COUNT(*) FROM Venta) AS total_ventas,
                    (SELECT COALESCE(SUM(cantidad * precio_venta), 0) FROM Detalle_venta) AS ingresos_totales
            ),
            top_productos AS (
                SELECT 
                    p.id_producto,
                    p.nombre,
                    SUM(dv.cantidad * dv.precio_venta) AS ingreso
                FROM Producto p
                JOIN Detalle_venta dv ON p.id_producto = dv.id_producto
                GROUP BY p.id_producto, p.nombre
                HAVING SUM(dv.cantidad * dv.precio_venta) > 0
                ORDER BY ingreso DESC
                LIMIT 5
            ),
            top_clientes AS (
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
                LIMIT 5
            ),
            ultimas_ventas AS (
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
                LIMIT 5
            ),
            alertas_stock AS (
                SELECT 
                    id_producto,
                    nombre,
                    stock_actual,
                    stock_minimo
                FROM Producto
                WHERE stock_actual <= stock_minimo
            )

            SELECT 
                (SELECT row_to_json(resumen) FROM resumen) AS resumen,
                (SELECT json_agg(top_productos) FROM top_productos) AS top_productos,
                (SELECT json_agg(top_clientes) FROM top_clientes) AS top_clientes,
                (SELECT json_agg(ultimas_ventas) FROM ultimas_ventas) AS ultimas_ventas,
                (SELECT json_agg(alertas_stock) FROM alertas_stock) AS alertas_stock;
        """)

        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="No data found")
        return {
            "resumen": row[0],
            "top_productos": row[1] or [],
            "top_clientes": row[2] or [],
            "ultimas_ventas": row[3] or [],
            "alertas_stock": row[4] or []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

@app.get("/clients", response_model=list[ClientResponse])
async def get_clients():
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id_cliente, nombre, apellido, telefono, correo, nit FROM Cliente;")

        return [
            ClientResponse(
                id_cliente=r[0],
                nombre=r[1],
                apellido=r[2],
                telefono=r[3],
                correo=r[4],
                nit=r[5]
            )
            for r in cursor.fetchall()
        ]

    finally:
        cursor.close()
        conn.close()


@app.get("/clients/{id}", response_model=ClientResponse)
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

        return ClientResponse(
            id_cliente=row[0],
            nombre=row[1],
            apellido=row[2],
            telefono=row[3],
            correo=row[4],
            nit=row[5]
        )

    finally:
        cursor.close()
        conn.close()


@app.post("/clients", status_code=201)
async def create_client(data: ClientCreate):
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
            data.nombre,
            data.apellido,
            data.telefono,
            data.correo,
            data.nit
        ))

        row = cursor.fetchone()
        conn.commit()

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
async def update_client(id: int, data: ClientUpdate):
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        fields = []
        values = []

        for key, value in data.model_dump(exclude_unset=True).items():
            fields.append(f"{key} = %s")
            values.append(value)

        if not fields:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        values.append(id)

        query = f"""
            UPDATE Cliente
            SET {', '.join(fields)}
            WHERE id_cliente = %s;
        """

        cursor.execute(query, tuple(values))

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

@app.get("/sales/{id}", response_model=SaleResponse)
async def get_sale(id: int):
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                v.id_venta,
                v.fecha,
                v.metodo_pago,
                p.nombre,
                dv.cantidad,
                dv.precio_venta
            FROM Venta v
            JOIN Detalle_venta dv ON v.id_venta = dv.id_venta
            JOIN Producto p ON dv.id_producto = p.id_producto
            WHERE v.id_venta = %s;
        """, (id,))

        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="Venta no encontrada")

        total = 0.0
        productos = []

        for r in rows:
            subtotal = r[4] * float(r[5])
            total += subtotal

            productos.append(SaleProductResponse(
                producto=r[3],
                cantidad=r[4],
                precio=float(r[5]),
                subtotal=subtotal
            ))

        return SaleResponse(
            id_venta=rows[0][0],
            fecha=str(rows[0][1]),
            metodo_pago=rows[0][2],
            productos=productos,
            total=total
        )

    finally:
        cursor.close()
        conn.close()


@app.delete("/sales/{id}")
async def delete_sale(id: int):
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    try:
        conn.autocommit = False

        cursor.execute("""
            SELECT id_producto, cantidad
            FROM Detalle_venta
            WHERE id_venta = %s;
        """, (id,))
        items = cursor.fetchall()

        if not items:
            raise HTTPException(status_code=404, detail="Venta no encontrada")

        for item in items:
            cursor.execute("""
                UPDATE Producto
                SET stock_actual = stock_actual + %s
                WHERE id_producto = %s;
            """, (item[1], item[0]))

        cursor.execute("DELETE FROM Detalle_venta WHERE id_venta = %s;", (id,))
        cursor.execute("DELETE FROM Venta WHERE id_venta = %s;", (id,))

        conn.commit()
        return {"message": "Venta eliminada"}

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

@app.get("/sales", response_model=List[SaleResponse])
async def get_sales():
    conn = db_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                v.id_venta,
                v.fecha,
                v.metodo_pago,
                (
                    SELECT COALESCE(SUM(dv.cantidad * dv.precio_venta), 0)
                    FROM Detalle_venta dv
                    WHERE dv.id_venta = v.id_venta
                ) AS total
            FROM Venta v
            ORDER BY v.id_venta;
        """)

        ventas_rows = cursor.fetchall()

        if not ventas_rows:
            return []

        ventas = []

        for venta in ventas_rows:
            id_venta = venta[0]

            cursor.execute("""
                SELECT 
                    p.nombre,
                    dv.cantidad,
                    dv.precio_venta
                FROM Detalle_venta dv
                JOIN Producto p ON dv.id_producto = p.id_producto
                WHERE dv.id_venta = %s;
            """, (id_venta,))

            productos_rows = cursor.fetchall()

            productos = []
            for r in productos_rows:
                subtotal = r[1] * float(r[2])

                productos.append(SaleProductResponse(
                    producto=r[0],
                    cantidad=r[1],
                    precio=float(r[2]),
                    subtotal=subtotal
                ))

            ventas.append(SaleResponse(
                id_venta=id_venta,
                fecha=str(venta[1]),
                metodo_pago=venta[2],
                productos=productos,
                total=float(venta[3])
            ))

        return ventas

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()