"""
Dashboard CLI con estadísticas del pipeline de búsqueda.

Uso:
    python src/dashboard.py
"""

from datetime import datetime, timedelta

from db import conectar


def calcular_stats() -> dict:
    with conectar() as conn:
        por_estado = dict(
            conn.execute(
                "SELECT estado, COUNT(*) FROM vacantes GROUP BY estado"
            ).fetchall()
        )
        # Nuevas en las últimas 24h
        hace_24h = (datetime.now() - timedelta(hours=24)).isoformat(sep=" ")
        nuevas_24h = conn.execute(
            "SELECT COUNT(*) FROM vacantes WHERE primera_vista >= ?",
            (hace_24h,),
        ).fetchone()[0]
        # Activas = no descartadas ni cerradas
        activas = conn.execute(
            "SELECT COUNT(*) FROM vacantes "
            "WHERE estado NOT IN ('descartada', 'cerrada')"
        ).fetchone()[0]
    return {
        "por_estado": por_estado,
        "nuevas_24h": nuevas_24h,
        "activas": activas,
    }


def main() -> None:
    s = calcular_stats()
    pe = s["por_estado"]
    print()
    print("📊 Tu pipeline de búsqueda")
    print("─" * 32)
    print(f"  Vacantes activas:       {s['activas']:>4}")
    print(f"  🆕 Nuevas (últimas 24h): {s['nuevas_24h']:>4}")
    print()
    print("  Por estado:")
    print(f"    📥 nueva:        {pe.get('nueva', 0):>4}")
    print(f"    ⭐ interesa:     {pe.get('interesa', 0):>4}")
    print(f"    📤 postulada:    {pe.get('postulada', 0):>4}")
    print(f"    ❌ descartada:   {pe.get('descartada', 0):>4}")
    print(f"    🔒 cerrada:      {pe.get('cerrada', 0):>4}")
    print()


if __name__ == "__main__":
    main()