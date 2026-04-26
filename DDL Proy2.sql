
/*
Script DDL Proyecto 2
Julián Divas - 24687
*/

create table Cliente (
    id_cliente serial primary key,
    nombre varchar(100) not null,
    apellido varchar(100) not null,
    telefono varchar(20) not null,
    correo varchar(150) not null unique,
    nit varchar(50)
);

create table Empleado (
    id_empleado serial primary key,
    nombre varchar(100) not null,
    apellido varchar(100) not null,
    puesto varchar(100) not null,
    telefono varchar(20) not null,
    correo varchar(150) not null unique,
    fecha_contratacion date not null
);

create table Categoria (
    id_categoria serial primary key,
    nombre varchar(100) not null,
    descripcion text
);

create table Proveedor (
    id_proveedor serial primary key,
    nombre varchar(150) not null,
    correo varchar(150) not null unique,
    direccion text not null,
    telefono varchar(20) not null
);

create table Producto (
    id_producto serial primary key,
    nombre varchar(150) not null,
    descripcion text,
    stock_actual integer not null,
    stock_minimo integer not null,
    precio_general numeric(10,2) not null,
    id_categoria integer not null,
    constraint fk_producto_categoria
        foreign key (id_categoria)
        references Categoria(id_categoria)
);

create table Venta (
    id_venta serial primary key,
    id_cliente integer not null,
    id_empleado integer not null,
    fecha timestamp not null default current_timestamp,
    metodo_pago varchar(50) not null,
    constraint fk_venta_cliente
        foreign key (id_cliente)
        references Cliente(id_cliente),
    constraint fk_venta_empleado
        foreign key (id_empleado)
        references Empleado(id_empleado)
);

create table Detalle_venta (
    id_venta integer not null,
    id_producto integer not null,
    cantidad integer not null,
    precio_venta numeric(10,2) not null,
    primary key (id_venta, id_producto),
    constraint fk_detalle_venta
        foreign key (id_venta)
        references Venta(id_venta),
    constraint fk_detalle_producto
        foreign key (id_producto)
        references Producto(id_producto)
);

create table Suministra (
    id_proveedor integer not null,
    id_producto integer not null,
    precio numeric(10,2) not null,
    fecha_ultima_compra date,
    primary key (id_proveedor, id_producto),
    constraint fk_suministra_proveedor
        foreign key (id_proveedor)
        references Proveedor(id_proveedor),
    constraint fk_suministra_producto
        foreign key (id_producto)
        references Producto(id_producto)
);
