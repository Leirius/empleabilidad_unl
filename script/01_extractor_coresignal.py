"""
01_extractor_coresignal.py
Extractor de vacantes desde Coresignal Base Jobs API.
Fuente alternativa a Fantastic Jobs para datos de LinkedIn + Indeed + Glassdoor.

API docs: https://docs.coresignal.com/jobs-api/base-jobs-api
Base URL: https://api.coresignal.com/cdapi/v2
Endpoints:
  POST /v2/job_base/search/filter   → Search (1 search credit) → retorna IDs
  GET  /v2/job_base/collect/{id}    → Collect (1 collect credit) → retorna registro completo

ESTADO ACTUAL: No funcional — free trial expirado (julio 2025).
Cuenta: equipo "Epn.edu", owner Dilan Andrade (dilan.andrade@epn.edu.ec).
Para activar: contratar plan Starter ($49/mo) o solicitar nuevo trial.

Uso:
    python script/01_extractor_coresignal.py
    python script/01_extractor_coresignal.py --test   # Solo 3 carreras
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
    logging.error("Falta 'requests'. Ejecuta: pip install requests")
    sys.exit(1)


# ── Configuración ────────────────────────────────────────────
def cargar_scraping_config():
    cfg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "scraping_config.json"
    )
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f).get("coresignal", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

_cfg = cargar_scraping_config()
BASE_URL = "https://api.coresignal.com/cdapi/v2"
DELAY_MIN = _cfg.get("delay_min", 0.5)
DELAY_MAX = _cfg.get("delay_max", 1.5)
TIMEOUT = _cfg.get("timeout", 30)
MAX_RESULTS_PER_SEARCH = _cfg.get("max_results_per_search", 50)


def cargar_catalogos():
    """Carga los catálogos de carreras y términos de búsqueda."""
    cat_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "catalogos.json"
    )
    with open(cat_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verificar_creditos(api_key):
    """Verifica si hay créditos disponibles antes de ejecutar."""
    headers = {"apikey": api_key, "Accept": "application/json"}

    # Intentar endpoint de créditos (no documentado oficialmente)
    for endpoint in ["/v2/credits", "/v2/user/credits"]:
        try:
            resp = requests.get(
                f"https://api.coresignal.com/cdapi{endpoint}",
                headers=headers, timeout=15
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass

    return None


def buscar_ids(api_key, termino, country="Ecuador"):
    """
    Busca IDs de vacantes en Coresignal.
    POST /v2/job_base/search/filter → retorna lista de IDs (1 search credit).
    """
    headers = {
        "apikey": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "country": country,
        "title": termino,
        "deleted": False,
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/job_base/search/filter",
            headers=headers,
            json=payload,
            timeout=TIMEOUT,
        )

        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                return data[:MAX_RESULTS_PER_SEARCH]
            return []

        elif resp.status_code == 402:
            logging.error(f"  ❌ 402 Insufficient credits — free trial expirado o sin plan activo")
            logging.error(f"  Contactar a Dilan Andrade (dilan.andrade@epn.edu.ec) para activar plan")
            return None  # None = error fatal, no seguir

        elif resp.status_code == 401:
            logging.error(f"  ❌ 401 No autorizado — verificar CORESIGNAL_API_KEY en .env")
            return None

        else:
            logging.warning(f"  HTTP {resp.status_code}: {resp.text[:200]}")
            return []

    except Exception as e:
        logging.error(f"  Error buscando '{termino}': {e}")
        return []


def collect_job(api_key, job_id):
    """
    Obtiene el registro completo de una vacante.
    GET /v2/job_base/collect/{job_id} → retorna dict (1 collect credit).
    """
    headers = {
        "apikey": api_key,
        "Accept": "application/json",
    }

    try:
        resp = requests.get(
            f"{BASE_URL}/job_base/collect/{job_id}",
            headers=headers,
            timeout=TIMEOUT,
        )

        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 402:
            logging.error(f"  ❌ 402 sin créditos de Collect")
            return None
        else:
            logging.warning(f"  Collect {job_id}: HTTP {resp.status_code}")
            return {}

    except Exception as e:
        logging.warning(f"  Error collect {job_id}: {e}")
        return {}


def normalizar_job(raw, carrera, termino):
    """Normaliza un registro crudo de Coresignal al formato del pipeline."""
    if not raw or not isinstance(raw, dict):
        return None

    return {
        "id": str(raw.get("id", "")),
        "title": raw.get("title", ""),
        "organization": raw.get("company_name", ""),
        "location": raw.get("location", ""),
        "url": raw.get("url", ""),
        "date_posted": raw.get("created", raw.get("last_updated", "")),
        "description_snippet": raw.get("description", ""),
        "salary": raw.get("salary", ""),
        "job_type": raw.get("employment_type", ""),
        "seniority": raw.get("seniority", ""),
        "source": "Coresignal",
        "source_original": raw.get("source", ""),
        "external_url": raw.get("external_url", ""),
        "company_url": raw.get("company_url", ""),
        "country": raw.get("country", ""),
        "carrera_origen": carrera,
        "termino_busqueda": termino,
    }


def main():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    api_key = os.getenv("CORESIGNAL_API_KEY")
    if not api_key:
        logging.error("Falta CORESIGNAL_API_KEY en .env")
        sys.exit(1)

    modo_test = "--test" in sys.argv

    # Verificar créditos primero
    logging.info("Verificando créditos de Coresignal...")
    creditos = verificar_creditos(api_key)
    if creditos:
        logging.info(f"  Créditos: {creditos}")

    catalogos = cargar_catalogos()
    terminos_carrera = catalogos["terminos_por_carrera"]

    if modo_test:
        carreras_seleccionadas = {k: v for k, v in list(terminos_carrera.items())[:3]}
        logging.info(f"MODO TEST: Procesando {len(carreras_seleccionadas)} carreras")
    else:
        carreras_seleccionadas = terminos_carrera

    all_jobs = []
    seen_ids = set()
    creditos_agotados = False

    for carrera, terminos in carreras_seleccionadas.items():
        if creditos_agotados:
            break

        logging.info(f"--- Carrera: {carrera} ({len(terminos)} términos) ---")

        for kw in terminos:
            if creditos_agotados:
                break

            # Paso 1: Search → obtener IDs
            ids = buscar_ids(api_key, kw)

            if ids is None:
                # Error fatal (402/401)
                creditos_agotados = True
                break

            if not ids:
                continue

            logging.info(f"  '{kw}': {len(ids)} IDs encontrados")

            # Paso 2: Collect → obtener registros completos
            nuevos = 0
            for job_id in ids:
                str_id = str(job_id)
                if str_id in seen_ids:
                    continue

                raw = collect_job(api_key, job_id)
                if raw is None:
                    # 402 — sin créditos
                    creditos_agotados = True
                    break
                if not raw:
                    continue

                job = normalizar_job(raw, carrera, kw)
                if job:
                    seen_ids.add(str_id)
                    all_jobs.append(job)
                    nuevos += 1

                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

            if nuevos:
                logging.info(f"    → {nuevos} nuevos registros recolectados")

            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(os.path.dirname(script_dir), "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"coresignal_batch_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    logging.info(f"Extracción completada: {len(all_jobs)} vacantes únicas en {output_path}")

    if creditos_agotados:
        logging.warning("⚠️ Extracción interrumpida por falta de créditos")
        logging.warning("  Para activar: contactar a Dilan Andrade o contratar plan Starter ($49/mo)")


if __name__ == "__main__":
    main()
