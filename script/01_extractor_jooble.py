"""
01_extractor_jooble.py
Extractor de vacantes desde Jooble Ecuador.
Usa el endpoint interno ec.jooble.org/api/serp/jobs (descubierto via
inspección de tráfico de red + repo github.com/TodorovicSrdjan/jooble-scraper).

Para bypasear Cloudflare usa tls_client (misma técnica que python-jobspy,
ver github.com/speedyapply/JobSpy/blob/main/jobspy/util.py).

NOTA: Jooble es un agregador — puede haber duplicados con CompuTrabajo,
Indeed, etc. La deduplicación se maneja en la fase de procesamiento en R.

Uso:
    python script/01_extractor_jooble.py
    python script/01_extractor_jooble.py --test   # Solo 3 carreras de prueba
"""

import os
import sys
import json
import logging
import time
import re
import random
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# tls_client emula el TLS fingerprint de Chrome (bypasea Cloudflare)
# Misma técnica usada por python-jobspy (speedyapply/JobSpy)
try:
    import tls_client
    HAS_TLS = True
except ImportError:
    HAS_TLS = False

try:
    import requests
except ImportError:
    logging.error("Falta la librería 'requests'. Ejecuta: pip install requests")
    sys.exit(1)


# ── Configuración ────────────────────────────────────────────
# Endpoint interno de Jooble (NO la API partner que no funciona para Ecuador)
# Referencia: github.com/TodorovicSrdjan/jooble-scraper → constants.py
JOOBLE_URL = "https://ec.jooble.org/api/serp/jobs"

# Parámetros de la API interna (valores de constants.py del repo)
DATE_ANY = 7        # Sin filtro de fecha
DATE_1_DAY = 8
DATE_3_DAYS = 2
DATE_7_DAYS = 3

MAX_PAGINAS = 3
DELAY_MIN = 1.5
DELAY_MAX = 3.0
TIMEOUT = 20

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-EC,es;q=0.9,en;q=0.8",
    "Origin": "https://ec.jooble.org",
    "Referer": "https://ec.jooble.org/",
}


def crear_sesion():
    """
    Crea una sesión HTTP. Usa tls_client si está disponible (bypasea Cloudflare),
    con fallback a requests (que probablemente será bloqueado por Cloudflare).
    """
    if HAS_TLS:
        session = tls_client.Session(
            client_identifier="chrome_120",
            random_tls_extension_order=True
        )
        logging.info("Usando tls_client (TLS fingerprint de Chrome)")
        return session
    else:
        logging.warning(
            "tls_client no instalado — Cloudflare probablemente bloqueará.\n"
            "  Instalar con: pip install tls-client"
        )
        return requests.Session()


def cargar_catalogos():
    """Carga los catálogos de carreras y términos de búsqueda."""
    cat_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "catalogos.json"
    )
    with open(cat_path, "r", encoding="utf-8") as f:
        return json.load(f)


def limpiar_html(texto):
    """Limpia tags HTML del texto."""
    if not texto:
        return ""
    texto = re.sub(r'<[^>]+>', '', str(texto))
    texto = texto.replace('&nbsp', ' ').replace('&amp;', '&')
    return " ".join(texto.strip().split())


def buscar_jooble(session, termino, region="", max_paginas=MAX_PAGINAS):
    """
    Busca vacantes en Jooble Ecuador usando el endpoint interno /api/serp/jobs.
    Retorna lista de diccionarios con las vacantes encontradas.
    """
    resultados = []

    for pagina in range(1, max_paginas + 1):
        payload = {
            "search": termino,
            "region": region,
            "date": DATE_ANY,
            "page": pagina,
        }

        try:
            if HAS_TLS:
                # tls_client usa una interfaz ligeramente diferente
                resp = session.post(
                    JOOBLE_URL,
                    json=payload,
                    headers=HEADERS,
                )
            else:
                resp = session.post(
                    JOOBLE_URL,
                    json=payload,
                    headers=HEADERS,
                    timeout=TIMEOUT
                )

            if resp.status_code == 403:
                logging.warning(f"  403 Forbidden para '{termino}' — Cloudflare bloqueó")
                break

            if resp.status_code != 200:
                logging.warning(f"  HTTP {resp.status_code} para '{termino}' página {pagina}")
                break

            try:
                data = resp.json()
            except (ValueError, AttributeError):
                logging.warning(f"  Respuesta no JSON para '{termino}' — posible challenge HTML")
                break

            jobs = data.get("jobs", [])

            if not jobs:
                if pagina == 1:
                    logging.info(f"  Sin resultados para '{termino}'")
                break

            for job in jobs:
                company = job.get("company", {})
                location = job.get("location", {})

                resultados.append({
                    "id": str(job.get("uid", job.get("id", ""))),
                    "title": limpiar_html(job.get("position", "")),
                    "organization": company.get("name", "") if isinstance(company, dict) else str(company),
                    "location": location.get("name", "") if isinstance(location, dict) else str(location),
                    "salary": str(job.get("salary", "")),
                    "url": job.get("url", ""),
                    "description_snippet": limpiar_html(job.get("content", ""))[:500],
                    "date_posted": str(job.get("dateCaption", "")),
                    "source": "Jooble",
                    "job_type": str(job.get("jobType", "")),
                    "is_remote": job.get("isRemoteJob", False),
                })

            logging.info(f"  Página {pagina}: {len(jobs)} ofertas para '{termino}'")

            if len(jobs) < 20:
                break

            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        except Exception as e:
            logging.error(f"  Error buscando '{termino}': {e}")
            break

    return resultados


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    modo_test = "--test" in sys.argv

    session = crear_sesion()

    catalogos = cargar_catalogos()
    terminos_carrera = catalogos["terminos_por_carrera"]

    if modo_test:
        carreras_seleccionadas = {k: v for k, v in list(terminos_carrera.items())[:3]}
        logging.info(f"MODO TEST: Procesando {len(carreras_seleccionadas)} carreras")
    else:
        carreras_seleccionadas = terminos_carrera

    all_jobs = []
    seen_ids = set()

    for carrera, terminos in carreras_seleccionadas.items():
        logging.info(f"--- Carrera: {carrera} ({len(terminos)} términos) ---")

        for kw in terminos:
            resultados = buscar_jooble(session, kw)
            nuevos = 0

            for job in resultados:
                job_id = job.get("id") or job.get("url", "")
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    job["carrera_origen"] = carrera
                    job["termino_busqueda"] = kw
                    all_jobs.append(job)
                    nuevos += 1

            if resultados:
                logging.info(f"  '{kw}': {len(resultados)} resultados, {nuevos} nuevos")

            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(os.path.dirname(script_dir), "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"jooble_batch_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    logging.info(f"Extracción completada: {len(all_jobs)} vacantes únicas guardadas en {output_path}")


if __name__ == "__main__":
    main()
