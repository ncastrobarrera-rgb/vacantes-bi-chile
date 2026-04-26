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

# Columnas que se insertan explícitamente al guardar una vacante.
# Excluimos las que SQLite rellena solas con su default:
# - estado (default 'nueva')
# - primera_vista, ultima_vista (default CURRENT_TIMESTAMP)
# - notas (queda NULL hasta que el usuario escriba algo)
COLUMNAS_INSERT = [
    "id", "titulo", "empresa", "categoria", "remote",
    "salario_min", "salario_max", "publicado_at",
    "applications_count", "url",
]

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

def guardar_vacantes(vacantes: list[dict]) -> set[str]:
    """Guarda vacantes en la base haciendo upsert idempotente.

    - Si el id NO existe → inserta la fila (queda con estado='nueva').
    - Si YA existe → actualiza solo applications_count y ultima_vista.
      Respeta el estado, primera_vista y notas que ya tuviera.

    Args:
        vacantes: lista de dicts. Cada dict debe tener al menos las keys
                  de COLUMNAS_INSERT. El valor None es válido para campos
                  opcionales (salario, etc).

    Returns:
        Set con los IDs de las vacantes que eran nuevas (no existían antes).
        Útil para marcarlas con 🆕 en el output.
    """
    if not vacantes:
        return set()

    ids_recibidos = {v["id"] for v in vacantes}

    with conectar() as conn:
        # 1. Detectar cuáles ya existían (antes del upsert).
        #    Necesitamos esto ahora porque después del INSERT no podríamos
        #    distinguir "recién insertada" de "actualizada".
        placeholders = ",".join("?" * len(ids_recibidos))
        existentes = {
            row[0]
            for row in conn.execute(
                f"SELECT id FROM vacantes WHERE id IN ({placeholders})",
                tuple(ids_recibidos),
            )
        }

        # 2. Upsert: INSERT con fallback a UPDATE en caso de conflicto.
        sql = f"""
            INSERT INTO vacantes ({", ".join(COLUMNAS_INSERT)})
            VALUES ({", ".join("?" * len(COLUMNAS_INSERT))})
            ON CONFLICT(id) DO UPDATE SET
                applications_count = excluded.applications_count,
                ultima_vista = CURRENT_TIMESTAMP
        """
        for v in vacantes:
            valores = tuple(v.get(col) for col in COLUMNAS_INSERT)
            conn.execute(sql, valores)

        conn.commit()

    return ids_recibidos - existentes

if __name__ == "__main__":
    init_db()