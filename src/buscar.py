"""
Buscador de vacantes BI/Datos en Chile usando Get on Board API.

Estrategia:
1. Hace varios queries (data, analista, BI, business intelligence)
2. Deduplica por job ID
3. Filtra por seniority junior + rango de salario CLP
4. Ordena por fecha de publicación (más reciente primero)
"""
from datetime import datetime
from typing import Any

import requests

# === Configuración ===
BASE_URL = "https://www.getonbrd.com/api/v0"
PAIS = "cl"
QUERIES = ["analista datos", "business intelligence", "data analyst", "BI"]
SALARIO_MIN_CLP = 800_000
SALARIO_MAX_CLP = 1_500_000
RESULTADOS_POR_PAGINA = 30


def buscar_por_query(query: str) -> list[dict[str, Any]]:
    """Llama a la API con un query y retorna los jobs."""
    url = f"{BASE_URL}/search/jobs"
    params = {
        "country_code": PAIS,
        "query": query,
        "per_page": RESULTADOS_POR_PAGINA,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json().get("data", [])
    except requests.RequestException as e:
        print(f"   ⚠️  Error con query '{query}': {e}")
        return []


def es_junior(job: dict[str, Any]) -> bool:
    """Filtro inverso: incluye la vacante salvo que el título indique
    senior, liderazgo o roles no aplicables a un junior."""
    titulo = job.get("attributes", {}).get("title", "").lower()
    excluir = [
        "senior", "sr.", " sr ", " sr,",
        "lead", "líder", "lider",
        "manager", "gerente", "director", "head", "jefe",
        "principal", "chief", "cto", "cio",
        "architect", "arquitecto",
        "specialist iii", "expert",
    ]
    return not any(p in titulo for p in excluir)


def cumple_salario(job: dict[str, Any]) -> bool:
    """True si: a) salario en rango, o b) no informa salario (lo dejamos pasar)."""
    attrs = job.get("attributes", {})
    s_min = attrs.get("min_salary")
    s_max = attrs.get("max_salary")
    if s_min is None and s_max is None:
        return True  # sin info → no descartamos
    if s_min and s_min > SALARIO_MAX_CLP:
        return False
    if s_max and s_max < SALARIO_MIN_CLP:
        return False
    return True


def empresa_desde_slug(job_id: str) -> str:
    """El slug del job tiene formato 'titulo-empresa-modalidad'.
    Hack: tomamos los segmentos del medio como aproximación de la empresa."""
    if not job_id:
        return "—"
    partes = job_id.split("-")
    if len(partes) >= 3:
        # Quita la última palabra si es 'remote' o 'remoto' o ciudad
        candidatas = partes[-4:-1] if partes[-1] in {"remote", "remoto"} else partes[-3:]
        return " ".join(candidatas).title()
    return "—"


def mostrar_job(job: dict[str, Any], idx: int) -> None:
    attrs = job.get("attributes", {})
    titulo = attrs.get("title", "Sin título")
    remote = "🏠 Remoto" if attrs.get("remote") else "🏢 Presencial/Híbrido"
    salario_min = attrs.get("min_salary")
    salario_max = attrs.get("max_salary")
    publicado = attrs.get("published_at")
    aplicantes = attrs.get("applications_count", 0)
    categoria = attrs.get("category_name", "—")
    url = job.get("links", {}).get("public_url", "")
    empresa = empresa_desde_slug(job.get("id", ""))

    fecha_str = "—"
    if publicado:
        fecha_str = datetime.fromtimestamp(publicado).strftime("%Y-%m-%d")

    print(f"\n[{idx}] {titulo}")
    print(f"    🏢 {empresa}")
    print(f"    📂 {categoria}  |  {remote}")
    print(f"    📅 {fecha_str}  |  👥 {aplicantes} postulantes")
    if salario_min and salario_max:
        print(f"    💰 ${int(salario_min):,} - ${int(salario_max):,} CLP")
    elif salario_min:
        print(f"    💰 desde ${int(salario_min):,} CLP")
    else:
        print(f"    💰 Salario no informado")
    print(f"    🔗 {url}")


def main() -> None:
    print(f"🔍 Buscando vacantes en Get on Board")
    print(f"   País:    {PAIS.upper()}")
    print(f"   Salario: ${SALARIO_MIN_CLP:,} - ${SALARIO_MAX_CLP:,} CLP")
    print(f"   Filtro:  juniors / analistas / sin experiencia\n")

    # 1. Recolectar de todos los queries y deduplicar
    vistos: dict[str, dict[str, Any]] = {}
    for q in QUERIES:
        print(f"   • Query '{q}'...")
        for job in buscar_por_query(q):
            job_id = job.get("id")
            if job_id and job_id not in vistos:
                vistos[job_id] = job

    print(f"\n📊 Total único:        {len(vistos)} vacantes")

    # 2. Filtrar por seniority + salario
    candidatas = [j for j in vistos.values() if es_junior(j) and cumple_salario(j)]
    print(f"📋 Cumplen criterios:  {len(candidatas)}")
    print("=" * 72)

    if not candidatas:
        print("\n⚠️  Ninguna vacante cumple los criterios actuales.")
        print("   Pista: revisa la lógica de es_junior() o relaja el rango de salario.")
        return

    # 3. Ordenar por más reciente
    candidatas.sort(
        key=lambda j: j.get("attributes", {}).get("published_at", 0),
        reverse=True,
    )

    # 4. Mostrar
    for i, job in enumerate(candidatas, 1):
        mostrar_job(job, i)

    print("\n" + "=" * 72)
    print(f"✅ Listo. {len(candidatas)} vacantes mostradas.\n")


if __name__ == "__main__":
    main()