/*
Script vistas Proyecto 2
Julián Divas - 24687
*/

CREATE VIEW vista_productos AS
SELECT 
    p.id_producto,
    p.nombre,
    p.descripcion,
    p.precio_general,
    p.stock_actual,
    p.stock_minimo,
    c.nombre AS categoria,
    CASE 
        WHEN p.stock_actual <= p.stock_minimo THEN 'Bajo'
        ELSE 'Disponible'
    END AS estado_stock
FROM Producto p
JOIN Categoria c ON p.id_categoria = c.id_categoria;