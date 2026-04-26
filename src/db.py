"""
Módulo de persistencia con SQLite para vacantes-bi-chile.

Provee funciones para inicializar la base de datos local (vacantes.db).
En pasos posteriores se agregarán funciones para guardar y consultar
vacantes (upsert idempotente, filtros por estado, etc).
"""

import sqlite3
from pathlib import Path

# Path absoluto al archivo de la base de datos.
# __file__ es la ruta de este archivo (src/db.py).
# .resolve() la convierte en absoluta.
# .parent.parent sube dos niveles: src/ → raíz del proyecto.
# Resultado: <raíz_proyecto>/vacantes.db
DB_PATH = Path(__file__).resolve().parent.parent / "vacantes.db"

# Schema de la tabla principal.
# IF NOT EXISTS hace que la sentencia sea idempotente:
# si la tabla ya existe, no falla ni la recrea.
SCHEMA_VACANTES = """
CREATE TABLE IF NOT EXISTS vacantes (
    id                  TEXT PRIMARY KEY,
    titulo              TEXT NOT NULL,
    empresa             TEXT,
    categoria           TEXT,
    remote              INTEGER,
    salario_min         INTEGER,
    salario_max         INTEGER,
    publicado_at        INTEGER,
    applications_count  INTEGER,
    url                 TEXT,
    estado              TEXT DEFAULT 'nueva',
    primera_vista       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_vista        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notas               TEXT
);
"""


def conectar() -> sqlite3.Connection:
    """Abre una conexión a la base de datos.

    Si el archivo vacantes.db no existe, sqlite3.connect() lo crea
    automáticamente. Quien llame a esta función es responsable de
    cerrar la conexión (idealmente con `with`).
    """
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Inicializa la base de datos creando las tablas si no existen.

    Es idempotente: se puede ejecutar muchas veces sin problemas.
    """
    print(f"📦 Inicializando base de datos en:")
    print(f"   {DB_PATH}")
    with conectar() as conn:
        conn.execute(SCHEMA_VACANTES)
        conn.commit()
    print("✅ Base de datos lista. Tabla 'vacantes' creada (o ya existía).")


if __name__ == "__main__":
    init_db()