# Esquema de Roles de la Base de Datos

## 1. Rol de Administrador
Es el dueño de la tienda, en este caso tiene acceso libre a toda la información de la base de datos.

|Tabla | Permiso Select | Permiso Insert | Permiso update | Permiso Delete
|----|----|----|----|----|
|Cliente| Si | Si | Si | Si | 
|Empleado| Si | Si | Si | Si | 
|Categoria| Si | Si | Si | Si |
|Proveedor| Si | Si | Si | Si |
|Producto| Si | Si | Si | Si | 
|Venta| Si | Si | Si | Si |  
|DetalleVenta| Si | Si | Si | Si | 
|Suministra| Si | Si | Si | Si | 

## 2. Rol de Gerente de Inventario

Encargado de los productos que se tienen, sus categorías y manejo de proveedores. Sin acceso a ventas ni datos de clientes.

|Tabla | Permiso Select | Permiso Insert | Permiso update | Permiso Delete
|----|----|----|----|----|
|Empleado| Si | No | No | No | 
|Categoria| Si | Si | Si | Si |
|Proveedor| Si | Si | Si | Si |
|Producto| Si | Si | Si | Si | 
|Suministra| Si | Si | Si | Si | 

## 3. Rol de Cajero
Se encarga de atender a los clientes y registrar las ventas, por lo que solamente puede crear ventas y consultar la información necesaria para ello.

|Tabla | Permiso Select | Permiso Insert | Permiso update | Permiso Delete
|----|----|----|----|----|
|Venta| No | Si | No | No |  
|DetalleVenta| Si | No | Si | No | No |
| Producto | Si | No | No | No | No |
| Cliente | Si | No | No | No | No |
| Empleado | Si | No | No | No | No |
| Categoria | Si | No | No | No | No | 

## 4. Rol de Auditor
Dedicado únicamente a la lectura de información para revisar las ventas e inventario reportado, rol dedicado a la contabilidad de la empresa.

|Tabla | Permiso Select | Permiso Insert | Permiso update | Permiso Delete
|----|----|----|----|----|
|Cliente| Si | No | No | No | 
|Empleado| Si | No | No | No |
|Categoria| Si | No | No | No |
|Proveedor| Si | No | No | No |
|Producto| Si | No | No | No | 
|Venta| Si | No | No | No |
|DetalleVenta| Si | No | No | No |
|Suministra| Si | No | No | No | 

## 5. Rol de recepcionista
Atiende a los clientes por lo que se dedica únicamente a la gestión de la información de estos.
|Tabla | Permiso Select | Permiso Insert | Permiso update | Permiso Delete
|----|----|----|----|----|
|Cliente| Si | Si | Si | Si | 
|Empleado| Si | No | No | No |