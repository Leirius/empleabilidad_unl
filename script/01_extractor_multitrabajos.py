"""
01_extractor_multitrabajos.py
Extractor de vacantes desde Multitrabajos Ecuador (grupo Bumeran).
Portal líder de empleo en Ecuador.

Usa la API interna JSON descubierta inspeccionando el tráfico de red (junio 2026):
  POST /api/avisos/searchV2?pageSize=20&page=0&sort=RECIENTES
  Header requerido: x-site-id: BMEC
  Body: {"query": "término", "filtros": []}

No requiere autenticación ni API key.

NOTA: El campo correcto para buscar es "query" (no "busqueda").
      Descubierto interceptando fetch() en el browser (2026-06-24).

Uso:
    python script/01_extractor_multitrabajos.py
    python script/01_extractor_multitrabajos.py --test   # Solo 3 carreras
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
API_URL = "https://www.multitrabajos.com/api/avisos/searchV2"
SITE_ID = "BMEC"  # Bumeran Ecuador (de /candidate/site.js → window.SITE_ID)

PAGE_SIZE = 20
MAX_PAGINAS = 5       # Máx 100 resultados por término (20 × 5)
DELAY_MIN = 1.5
DELAY_MAX = 3.0
TIMEOUT = 20

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "x-site-id": SITE_ID,
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
    "Origin": "https://www.multitrabajos.com",
    "Referer": "https://www.multitrabajos.com/empleos.html",
}


def cargar_catalogos():
    """Carga los catálogos de carreras y términos de búsqueda."""
    cat_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "catalogos.json"
    )
    with open(cat_path, "r", encoding="utf-8") as f:
        return json.load(f)


def buscar_multitrabajos(termino, max_paginas=MAX_PAGINAS):
    """
    Busca vacantes en Multitrabajos usando su API interna.
    Retorna lista de diccionarios con las vacantes encontradas.
    """
    resultados = []

    for pagina in range(max_paginas):
        params = {
            "pageSize": str(PAGE_SIZE),
            "page": str(pagina),
            "sort": "RELEVANTES",
        }
        payload = {
            "query": termino,
            "filtros": [],
        }

        try:
            resp = requests.post(
                API_URL,
                params=params,
                json=payload,
                headers=HEADERS,
                timeout=TIMEOUT,
            )

            if resp.status_code != 200:
                logging.warning(f"  HTTP {resp.status_code} para '{termino}' página {pagina}")
                break

            data = resp.json()
            avisos = data.get("content", [])
            total = data.get("total", 0)

            if not avisos:
                if pagina == 0:
                    logging.info(f"  Sin resultados para '{termino}'")
                break

            for aviso in avisos:
                # Construir URL del aviso
                aviso_id = aviso.get("id", "")
                aviso_url = f"https://www.multitrabajos.com/empleos/{aviso_id}.html" if aviso_id else ""

                resultados.append({
                    "id": str(aviso_id),
                    "title": aviso.get("titulo", ""),
                    "organization": aviso.get("empresa", ""),
                    "location": aviso.get("localizacion", ""),
                    "description_snippet": (aviso.get("detalle", "") or "")[:500],
                    "salary": "",  # No viene en el listado, solo indica salarioObligatorio
                    "url": aviso_url,
                    "date_posted": aviso.get("fechaPublicacion", ""),
                    "source": "Multitrabajos",
                    "job_type": aviso.get("tipoTrabajo", ""),
                    "modalidad": aviso.get("modalidadTrabajo", ""),
                    "num_vacantes": aviso.get("cantidadVacantes", 1),
                    "confidencial": aviso.get("confidencial", False),
                })

            logging.info(f"  Página {pagina + 1}: {len(avisos)} ofertas para '{termino}' (total: {total})")

            # Si ya obtuvimos todos los resultados disponibles, parar
            if (pagina + 1) * PAGE_SIZE >= total:
                break

            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        except requests.exceptions.Timeout:
            logging.warning(f"  Timeout para '{termino}' página {pagina}")
            break
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
            resultados = buscar_multitrabajos(kw)
            nuevos = 0

            for job in resultados:
                job_id = job.get("id", "")
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
    output_path = os.path.join(output_dir, f"multitrabajos_batch_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    logging.info(f"Extracción completada: {len(all_jobs)} vacantes únicas guardadas en {output_path}")


if __name__ == "__main__":
    main()
