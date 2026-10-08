-- Esquema de Sergio para PostgreSQL. Ejecutar dentro de reportes_ventas.
CREATE TABLE IF NOT EXISTS categorias (
    id_categoria INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE CHECK (btrim(nombre) <> '')
);

CREATE TABLE IF NOT EXISTS productos (
    id_producto INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL CHECK (btrim(nombre) <> ''),
    id_categoria INTEGER NOT NULL REFERENCES categorias(id_categoria) ON DELETE RESTRICT,
    UNIQUE (nombre, id_categoria)
);

CREATE TABLE IF NOT EXISTS ventas (
    id_venta BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha DATE NOT NULL,
    id_producto INTEGER NOT NULL REFERENCES productos(id_producto) ON DELETE RESTRICT,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(12,2) NOT NULL
        CHECK (precio_unitario >= 0 AND precio_unitario < 'Infinity'::numeric),
    lote_hash VARCHAR(64) NOT NULL CHECK (lote_hash ~ '^[0-9a-f]{64}$'),
    fila_origen INTEGER NOT NULL CHECK (fila_origen >= 2),
    UNIQUE (lote_hash, fila_origen)
);

CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(id_categoria);
CREATE INDEX IF NOT EXISTS idx_ventas_producto ON ventas(id_producto);
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha);
