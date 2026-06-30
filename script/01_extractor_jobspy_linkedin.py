"""
01_extractor_jobspy_linkedin.py
Extractor de vacantes de LinkedIn usando python-jobspy (scraping gratuito).

Este script usa JobSpy SOLO con LinkedIn como fuente.
Es una alternativa GRATUITA a la API de Fantastic Jobs cuando:
  - Se agotan los créditos del plan Basic (250 jobs/mes)
  - Se necesita un respaldo sin costo
  - Se quiere comparar datos entre fuentes

DIFERENCIA con 01_extractor_linkedin.py (Fantastic Jobs API):
  - Fantastic Jobs: 71 campos, incluye IA (skills, education, salary inferido),
    metadata empresa (headcount, industry), coordenadas GPS → MUCHO más rico
  - Este script: ~20 campos básicos (título, empresa, ubicación, descripción,
    salario si viene, tipo, remote) → suficiente para el análisis base

DIFERENCIA con 01_extractor_jobspy.py (Indeed + Google Jobs):
  - Ese script usa sites=["indeed", "google"]
  - Este script usa sites=["linkedin"] exclusivamente
  - Son independientes para evitar conflictos de rate limiting

Uso:
    python script/01_extractor_jobspy_linkedin.py
    python script/01_extractor_jobspy_linkedin.py --test   # Solo 3 carreras
"""

import os
import sys
import json
import logging
import time
import math
import random
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
def cargar_scraping_config():
    cfg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "scraping_config.json"
    )
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f).get("jobspy_linkedin", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

_cfg = cargar_scraping_config()
RESULTS_PER_SEARCH = _cfg.get("results_per_search", 100)
HOURS_OLD = _cfg.get("hours_old", 720)  # 30 días
DELAY_MIN = _cfg.get("delay_min", 3.0)  # Más delay que Indeed/Google
DELAY_MAX = _cfg.get("delay_max", 6.0)
FETCH_DESCRIPTION = _cfg.get("fetch_description", True)


def cargar_catalogos():
    cat_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "catalogos.json"
    )
    with open(cat_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parsear_location(location_str, city_raw, state_raw, country_raw):
    """
    Parsea city/state/country desde el string combinado de location
    cuando los campos individuales vienen vacíos.
    """
    city = city_raw if city_raw and city_raw not in ("nan", "None", "") else ""
    state = state_raw if state_raw and state_raw not in ("nan", "None", "") else ""
    country = country_raw if country_raw and country_raw not in ("nan", "None", "") else ""

    if city and country:
        return city, state, country

    if not location_str or location_str in ("nan", "None", ""):
        return city, state, country

    parts = [p.strip() for p in location_str.split(",") if p.strip()]

    if len(parts) >= 3:
        if not city:
            city = parts[0]
        if not state:
            state = parts[1]
        if not country:
            country = parts[2]
    elif len(parts) == 2:
        if not city:
            city = parts[0]
        if not country:
            country = parts[1]
    elif len(parts) == 1:
        if not country and parts[0].lower() in ("ec", "ecuador"):
            country = parts[0]
        elif not city:
            city = parts[0]

    if country.upper() in ("EC",):
        country = "Ecuador"

    return city, state, country


def buscar_linkedin(termino, carrera):
    """
    Busca vacantes en LinkedIn usando python-jobspy.
    Retorna lista de diccionarios normalizados.
    """
    resultados = []

    try:
        jobs_df = scrape_jobs(
            site_name=["linkedin"],
            search_term=termino,
            location="Ecuador",
            results_wanted=RESULTS_PER_SEARCH,
            hours_old=HOURS_OLD,
            linkedin_fetch_description=FETCH_DESCRIPTION,
            verbose=0,
        )

        if jobs_df is not None and len(jobs_df) > 0:
            for _, row in jobs_df.iterrows():
                loc_str = str(row.get("location", ""))
                city, state, country = parsear_location(
                    loc_str,
                    str(row.get("city", "")),
                    str(row.get("state", "")),
                    str(row.get("country", "")),
                )

                job = {
                    "title": str(row.get("title", "")),
                    "organization": str(row.get("company", "")),
                    "location": loc_str,
                    "city": city,
                    "state": state,
                    "country": country,
                    "url": str(row.get("job_url", "")),
                    "source": "LinkedIn-JobSpy",
                    "date_posted": str(row.get("date_posted", "")),
                    "job_type": "" if str(row.get("job_type", "")) == "nan" else str(row.get("job_type", "")),
                    "is_remote": bool(row.get("is_remote", False)),
                    "salary_min": None if (v := row.get("min_amount")) is None or (isinstance(v, float) and math.isnan(v)) else float(v),
                    "salary_max": None if (v := row.get("max_amount")) is None or (isinstance(v, float) and math.isnan(v)) else float(v),
                    "salary_interval": "" if str(row.get("interval", "")) == "nan" else str(row.get("interval", "")),
                    "salary_currency": "" if str(row.get("currency", "")) == "nan" else str(row.get("currency", "")),
                    "description_snippet": str(row.get("description", "")),
                    "job_level": "" if str(row.get("job_level", "")) == "nan" else str(row.get("job_level", "")),
                    "job_function": "" if str(row.get("job_function", "")) == "nan" else str(row.get("job_function", "")),
                    "company_industry": "" if str(row.get("company_industry", "")) == "nan" else str(row.get("company_industry", "")),
                    "company_num_employees": None if (v := row.get("company_num_employees")) is None or (isinstance(v, float) and math.isnan(v)) else int(v),
                    "skills": str(row.get("skills", "")) if str(row.get("skills", "")) != "nan" else "",
                    "carrera_origen": carrera,
                    "termino_busqueda": termino,
                }
                resultados.append(job)

    except Exception as e:
        logging.warning(f"Error JobSpy-LinkedIn para '{termino}': {e}")

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
            resultados = buscar_linkedin(kw, carrera)
            nuevos = 0

            for job in resultados:
                job_url = job.get("url", "")
                if job_url and job_url not in seen_urls:
                    seen_urls.add(job_url)
                    all_jobs.append(job)
                    nuevos += 1

            if resultados:
                logging.info(f"  '{kw}': {len(resultados)} resultados, {nuevos} nuevos")

            # Delay más largo para LinkedIn (evitar bloqueo)
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(os.path.dirname(script_dir), "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"jobspy_linkedin_batch_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2, default=str)

    logging.info(f"Extracción completada: {len(all_jobs)} vacantes únicas en {output_path}")


if __name__ == "__main__":
    main()
