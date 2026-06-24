"""
01_extractor_linkedin.py
Extractor de vacantes de LinkedIn via Fantastic Jobs API (RapidAPI).
Endpoint: linkedin-job-search-api.p.rapidapi.com/active-jb

La API provee datos enriquecidos por IA que no se obtienen con scraping:
  - Coordenadas GPS (lats_derived, lngs_derived) para mapas de calor
  - Habilidades extraídas (ai_key_skills)
  - Salarios inferidos (ai_salary_value)
  - Metadata de empresa (headcount, industry, size)
  - Nivel de seniority, modalidad de trabajo, beneficios

Requiere: RAPIDAPI_KEY en archivo .env

Uso:
    python script/01_extractor_linkedin.py
    python script/01_extractor_linkedin.py --test   # Solo 3 carreras
"""

import os
import sys
import json
import logging
import time
import random
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

try:
    import requests
except ImportError:
    logging.error("Falta la librería 'requests'. Ejecuta: pip install requests")
    sys.exit(1)


# ── Configuración ────────────────────────────────────────────
API_HOST = "linkedin-job-search-api.p.rapidapi.com"
ENDPOINT = "/active-jb"
LIMIT_PER_REQUEST = 20
TIME_FRAME = "1m"      # Último mes
DELAY_MIN = 1.0
DELAY_MAX = 2.5
TIMEOUT = 20


def cargar_catalogos():
    """Carga los catálogos de carreras y términos de búsqueda."""
    cat_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "catalogos.json"
    )
    with open(cat_path, "r", encoding="utf-8") as f:
        return json.load(f)


def buscar_linkedin(api_key, termino):
    """
    Busca vacantes en LinkedIn via Fantastic Jobs API.
    Retorna lista de diccionarios con las vacantes encontradas.
    """
    url = f"https://{API_HOST}{ENDPOINT}"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": API_HOST,
    }
    params = {
        "title": termino,
        "location": "Ecuador",
        "limit": str(LIMIT_PER_REQUEST),
        "time_frame": TIME_FRAME,
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)

        if resp.status_code == 429:
            logging.warning(f"  Rate limit alcanzado para '{termino}' — esperando 60s")
            time.sleep(60)
            return []

        if resp.status_code != 200:
            logging.warning(f"  HTTP {resp.status_code} para '{termino}': {resp.text[:200]}")
            return []

        data = resp.json()
        if isinstance(data, list):
            return data
        return []

    except Exception as e:
        logging.error(f"  Error buscando '{termino}': {e}")
        return []


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        logging.error(
            "Falta la variable RAPIDAPI_KEY en el archivo .env\n"
            "  Obtener en: https://rapidapi.com/fantastic-jobs-fantastic-jobs-default/api/linkedin-job-search-api"
        )
        return

    modo_test = "--test" in sys.argv

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
            resultados = buscar_linkedin(api_key, kw)
            nuevos = 0

            for job in resultados:
                job_id = job.get("id") or job.get("url", "")
                if job_id and str(job_id) not in seen_ids:
                    seen_ids.add(str(job_id))
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
    output_path = os.path.join(output_dir, f"linkedin_batch_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    logging.info(f"Extracción completada: {len(all_jobs)} vacantes únicas guardadas en {output_path}")


if __name__ == "__main__":
    main()
