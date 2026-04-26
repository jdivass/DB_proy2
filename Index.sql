/*
Script índices Proyecto 2
Julián Divas - 24687
*/
create index idx_producto_categoria
on Producto(id_categoria);

create index idx_venta_fecha
on Venta(fecha);