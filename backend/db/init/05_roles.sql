/*
  Script de roles y permisos
  Julián Divas - 24687
*/

-- Usuario principal
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'proy3') THEN
    CREATE USER proy3 WITH PASSWORD 'secret';
  END IF;
END
$$;

GRANT ALL PRIVILEGES ON DATABASE tienda TO proy3;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO proy3;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO proy3;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO proy3;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO proy3;

-- Creación de los usuarios roles definidos en el esquema de roles
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'administrador') THEN
    CREATE ROLE administrador;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'gerente_inventario') THEN
    CREATE ROLE gerente_inventario;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'cajero') THEN
    CREATE ROLE cajero;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'auditor') THEN
    CREATE ROLE auditor;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'recepcionista') THEN
    CREATE ROLE recepcionista;
  END IF;
END
$$;

-- Permisos para administrador
GRANT SELECT, INSERT, UPDATE, DELETE ON
    cliente, empleado, categoria, proveedor,
    producto, venta, detalle_venta, suministra
TO administrador;

GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO administrador;

-- Permisos para gerente de inventario
GRANT SELECT, INSERT, UPDATE, DELETE ON
    producto, categoria, proveedor, suministra
TO gerente_inventario;

GRANT SELECT ON empleado TO gerente_inventario;

GRANT USAGE, SELECT ON SEQUENCE
    producto_id_producto_seq,
    categoria_id_categoria_seq,
    proveedor_id_proveedor_seq
TO gerente_inventario;

REVOKE ALL ON cliente, venta, detalle_venta FROM gerente_inventario;

-- Permisos para el cajero
GRANT SELECT ON
    producto, cliente, empleado, categoria
TO cajero;

GRANT INSERT ON venta, detalle_venta TO cajero;

GRANT USAGE, SELECT ON SEQUENCE
    venta_id_venta_seq
TO cajero;

REVOKE ALL ON proveedor, suministra FROM cajero;
REVOKE UPDATE, DELETE ON venta, detalle_venta FROM cajero;

-- Permisos para el auditor
GRANT SELECT ON
    cliente, empleado, categoria, proveedor,
    producto, venta, detalle_venta, suministra
TO auditor;

-- Permisos para el recepcionista
GRANT SELECT, INSERT, UPDATE ON cliente TO recepcionista;

GRANT SELECT ON empleado TO recepcionista;

GRANT USAGE, SELECT ON SEQUENCE
    cliente_id_cliente_seq
TO recepcionista;

REVOKE ALL ON
    producto, categoria, proveedor,
    venta, detalle_venta, suministra
FROM recepcionista;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario   SERIAL PRIMARY KEY,
    username     VARCHAR(100) NOT NULL UNIQUE,
    password     TEXT NOT NULL,
    rol          VARCHAR(50)  NOT NULL
        CHECK (rol IN ('administrador', 'gerente_inventario',
                       'cajero', 'auditor', 'recepcionista')),
    activo       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

GRANT SELECT ON usuarios TO proy3;


-- Usuarios de Prueba
INSERT INTO usuarios (username, password, rol) VALUES
  ('admin_user', 'password123', 'administrador'),
  ('gerente_user', 'password123', 'gerente_inventario'),
  ('cajero_user', 'password123', 'cajero'),
  ('auditor_user', 'password123', 'auditor'),
  ('recepcionista_user', 'password123', 'recepcionista')
ON CONFLICT (username) DO NOTHING;