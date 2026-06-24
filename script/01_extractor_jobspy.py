"""
01_extractor_jobspy.py
Extractor de Indeed y Google Jobs para Ecuador usando python-jobspy.
JobSpy (github.com/speedyapply/JobSpy) scrapea múltiples portales en paralelo.

LinkedIn NO se incluye aquí porque la API de Fantastic Jobs
(01_extractor_linkedin.py) provee datos mucho más ricos: coordenadas GPS,
habilidades extraídas por IA, salarios inferidos, metadata de empresa, etc.

Si se necesita LinkedIn como fallback gratuito (sin la riqueza de la API),
cambiar SITES a ["linkedin", "indeed", "google"] y descomentar
linkedin_fetch_description=True.

Instalación:
    pip install python-jobspy

Uso:
    python script/01_extractor_jobspy.py
    python script/01_extractor_jobspy.py --test   # Solo 3 carreras
"""

import os
import sys
import json
import logging
import time
import random
import math
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

try:
    from jobspy import scrape_jobs
except ImportError:
    logging.error(
        "Falta la librería 'python-jobspy'. Ejecuta: pip install python-jobspy"
    )
    sys.exit(1)


# ── Configuración ────────────────────────────────────────────
# Indeed + Google Jobs (LinkedIn se maneja con la API de Fantastic Jobs)
# Para incluir LinkedIn como fallback: SITES = ["linkedin", "indeed", "google"]
SITES = ["indeed", "google"]
LOCATION = "Ecuador"
COUNTRY_INDEED = "Ecuador"
RESULTS_PER_SEARCH = 50
HOURS_OLD = 720  # 30 días
DELAY_MIN = 2.0
DELAY_MAX = 4.0


def cargar_catalogos():
    cat_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "catalogos.json"
    )
    with open(cat_path, "r", encoding="utf-8") as f:
        return json.load(f)


def buscar_jobspy(termino, carrera):
    """
    Busca vacantes usando python-jobspy para un término dado.
    Retorna lista de diccionarios.
    """
    resultados = []

    try:
        # Para Google Jobs, necesitamos un search term específico
        google_term = f"{termino} empleos en Ecuador"

        jobs_df = scrape_jobs(
            site_name=SITES,
            search_term=termino,
            google_search_term=google_term,
            location=LOCATION,
            results_wanted=RESULTS_PER_SEARCH,
            hours_old=HOURS_OLD,
            country_indeed=COUNTRY_INDEED,
            # linkedin_fetch_description=True,  # Descomentar si se agrega LinkedIn a SITES
            verbose=0,  # Solo errores
        )

        if jobs_df is not None and len(jobs_df) > 0:
            for _, row in jobs_df.iterrows():
                job = {
                    "title": str(row.get("title", "")),
                    "organization": str(row.get("company", "")),
                    "location": str(row.get("location", "")),
                    "city": str(row.get("city", "")),
                    "state": str(row.get("state", "")),
                    "country": str(row.get("country", "")),
                    "url": str(row.get("job_url", "")),
                    "source": str(row.get("site", "")),
                    "date_posted": str(row.get("date_posted", "")),
                    "job_type": "" if str(row.get("job_type", "")) == "nan" else str(row.get("job_type", "")),
                    "is_remote": bool(row.get("is_remote", False)),
                    "salary_min": None if (v := row.get("min_amount")) is None or (isinstance(v, float) and math.isnan(v)) else float(v),
                    "salary_max": None if (v := row.get("max_amount")) is None or (isinstance(v, float) and math.isnan(v)) else float(v),
                    "salary_interval": "" if str(row.get("interval", "")) == "nan" else str(row.get("interval", "")),
                    "salary_currency": "" if str(row.get("currency", "")) == "nan" else str(row.get("currency", "")),
                    "description_snippet": str(row.get("description", ""))[:500],
                    "carrera_origen": carrera,
                    "termino_busqueda": termino,
                }
                resultados.append(job)

    except Exception as e:
        logging.warning(f"Error JobSpy para '{termino}': {e}")

    return resultados


def main():
    modo_test = "--test" in sys.argv

    catalogos = cargar_catalogos()
    terminos_carrera = catalogos["terminos_por_carrera"]

    if modo_test:
        carreras_seleccionadas = {k: v for k, v in list(terminos_carrera.items())[:3]}
        logging.info(f"MODO TEST: Procesando {len(carreras_seleccionadas)} carreras")
    else:
        carreras_seleccionadas = terminos_carrera

    all_jobs = []
    seen_urls = set()

    for carrera, terminos in carreras_seleccionadas.items():
        logging.info(f"--- Carrera: {carrera} ({len(terminos)} términos) ---")

        for kw in terminos:
            resultados = buscar_jobspy(kw, carrera)
            nuevos = 0

            for job in resultados:
                job_url = job.get("url", "")
                if job_url and job_url not in seen_urls:
                    seen_urls.add(job_url)
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
    output_path = os.path.join(output_dir, f"jobspy_batch_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2, default=str)

    logging.info(f"Extracción completada: {len(all_jobs)} vacantes únicas en {output_path}")


if __name__ == "__main__":
    main()
