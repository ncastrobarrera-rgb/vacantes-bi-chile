"""
CLI para cambiar el estado de una vacante en la base.

Uso:
    python src/marcar.py                   # lista vacantes activas con su índice
    python src/marcar.py <num> <estado>    # cambia estado de la vacante #num

Estados válidos: nueva, interesa, postulada, descartada, cerrada
"""

import sys
from datetime import datetime

from db import conectar


ESTADOS_VALIDOS = {"nueva", "interesa", "postulada", "descartada", "cerrada"}


def listar_activas() -> list[tuple]:
    """Vacantes que NO están descartadas/cerradas, en orden por fecha desc."""
    with conectar() as conn:
        return conn.execute(
            """
            SELECT id, titulo, estado, publicado_at
            FROM vacantes
            WHERE estado NOT IN ('descartada', 'cerrada')
            ORDER BY publicado_at DESC
            """
        ).fetchall()


def mostrar_lista(filas: list[tuple]) -> None:
    if not filas:
        print("⚠️  No hay vacantes activas.")
        return
    print(f"\n📋 Vacantes activas ({len(filas)}):\n")
    for i, (_vid, titulo, estado, publicado_at) in enumerate(filas, 1):
        fecha = (
            datetime.fromtimestamp(publicado_at).strftime("%Y-%m-%d")
            if publicado_at
            else "—"
        )
        print(f"  [{i:3d}] {fecha} | {estado:11s} | {titulo}")
    print()


def cambiar_estado(vid: str, estado_nuevo: str) -> int:
    with conectar() as conn:
        cur = conn.execute(
            "UPDATE vacantes SET estado = ?, ultima_vista = CURRENT_TIMESTAMP WHERE id = ?",
            (estado_nuevo, vid),
        )
        conn.commit()
        return cur.rowcount


def main() -> None:
    args = sys.argv[1:]

    # Modo lectura: sin argumentos → lista las vacantes
    if not args:
        mostrar_lista(listar_activas())
        print("Uso: python src/marcar.py <num> <estado>")
        print(f"Estados: {', '.join(sorted(ESTADOS_VALIDOS))}")
        return

    # Modo escritura: dos argumentos → marca la #num con el estado
    if len(args) != 2:
        print("❌ Uso: python src/marcar.py <num> <estado>")
        sys.exit(1)

    try:
        num = int(args[0])
    except ValueError:
        print(f"❌ El primer argumento debe ser un número, no '{args[0]}'")
        sys.exit(1)

    estado_nuevo = args[1].lower()
    if estado_nuevo not in ESTADOS_VALIDOS:
        print(f"❌ Estado inválido. Debe ser uno de: {', '.join(sorted(ESTADOS_VALIDOS))}")
        sys.exit(1)

    filas = listar_activas()
    if not 1 <= num <= len(filas):
        print(f"❌ Número fuera de rango. Hay {len(filas)} vacantes activas (1-{len(filas)}).")
        sys.exit(1)

    vid, titulo, estado_actual, _ = filas[num - 1]
    print(f"📝 {titulo}")
    print(f"   {estado_actual} → {estado_nuevo}")
    if cambiar_estado(vid, estado_nuevo) == 0:
        print(f"❌ No se pudo actualizar (id={vid})")
    else:
        print(f"✅ Listo.")


if __name__ == "__main__":
    main()