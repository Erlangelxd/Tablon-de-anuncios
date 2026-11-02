PRAGMA foreign_keys = ON;

CREATE TABLE usuarios (
    id INTEGER NOT NULL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'usuario',
    fecha_registro DATETIME NOT NULL
);

CREATE TABLE categorias (
    id INTEGER NOT NULL PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    fecha_creacion DATETIME NOT NULL
);

CREATE TABLE anuncios (
    id INTEGER NOT NULL PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    contenido TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT 1,
    fecha_publicacion DATETIME NOT NULL,
    usuario_id INTEGER NOT NULL,
    categoria_id INTEGER NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
    FOREIGN KEY (categoria_id) REFERENCES categorias (id)
);

CREATE INDEX ix_anuncios_usuario_id ON anuncios (usuario_id);
CREATE INDEX ix_anuncios_categoria_id ON anuncios (categoria_id);
CREATE INDEX ix_anuncios_fecha_publicacion ON anuncios (fecha_publicacion);
