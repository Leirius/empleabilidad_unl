"""
01_extractor_computrabajo.py
Scraper de vacantes desde CompuTrabajo Ecuador.
Usa requests + BeautifulSoup (sin Playwright/Selenium).

CompuTrabajo no tiene API pública. Este scraper parsea el HTML del listado.
La URL de búsqueda sigue el patrón: ec.computrabajo.com/trabajo-de-{slug}

Uso:
    python script/01_extractor_computrabajo.py
    python script/01_extractor_computrabajo.py --test   # Solo 3 carreras
"""

import os
import sys
import json
import logging
import time
import re
import random
from datetime import datetime
from urllib.parse import urljoin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    logging.error("Faltan librerías. Ejecuta: pip install requests beautifulsoup4 lxml")
    sys.exit(1)


# ── Configuración ────────────────────────────────────────────
BASE_URL = "https://ec.computrabajo.com"
MAX_PAGINAS = 5
DELAY_MIN = 2.5
DELAY_MAX = 5.0
TIMEOUT = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-EC,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.com/",
    "DNT": "1",
}


def cargar_catalogos():
    cat_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "catalogos.json"
    )
    with open(cat_path, "r", encoding="utf-8") as f:
        return json.load(f)


def limpiar_texto(texto):
    """Limpia espacios extra y saltos de línea."""
    if not texto:
        return ""
    return " ".join(str(texto).strip().split())


def scrape_computrabajo(termino, max_paginas=MAX_PAGINAS):
    """
    Scrapea vacantes de CompuTrabajo para un término de búsqueda.
    Retorna lista de diccionarios.
    """
    resultados = []
    slug = termino.replace(" ", "-").lower()

    for pagina in range(1, max_paginas + 1):
        url = f"{BASE_URL}/trabajo-de-{slug}"
        if pagina > 1:
            url += f"?p={pagina}"

        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

            if resp.status_code == 404:
                break
            if resp.status_code != 200:
                logging.warning(f"HTTP {resp.status_code} para '{termino}' página {pagina}")
                break

            soup = BeautifulSoup(resp.text, "lxml")

            # Buscar tarjetas de ofertas
            # CompuTrabajo usa <article> con clase js-o o similar
            tarjetas = soup.find_all("article", class_=re.compile(r"box_offer|offerList|js-o", re.I))
            if not tarjetas:
                # Fallback: buscar por estructura alternativa
                tarjetas = soup.select("article")

            if not tarjetas:
                logging.info(f"  Sin tarjetas en página {pagina} para '{termino}'")
                break

            for tarjeta in tarjetas:
                try:
                    # Título: está en <h2> > <a class="js-o-link fc_base">
                    titulo_el = tarjeta.find("h2")
                    if titulo_el:
                        link_el = titulo_el.find("a", href=True)
                    else:
                        link_el = tarjeta.find("a", href=True)

                    titulo = ""
                    if titulo_el:
                        # Extraer solo el texto del link, no los tags
                        if link_el:
                            titulo = limpiar_texto(link_el.get_text())
                        else:
                            titulo = limpiar_texto(titulo_el.get_text())
                    # Limpiar "Postulado Vista" del título
                    titulo = re.sub(r'\s*(Postulado|Vista)\s*', ' ', titulo, flags=re.I).strip()

                    href = link_el["href"] if link_el else ""
                    link = urljoin(BASE_URL, href) if href else ""

                    if not titulo or len(titulo) < 3:
                        continue

                    # Estructura real de CompuTrabajo (verificada junio 2026):
                    # <p class="dFlex vm_fx fs16 fc_base mt5"> → contiene empresa en <a class="fc_base t_ellipsis">
                    # <p class="fs16 fc_base mt5"> (sin dFlex) → contiene ubicación en <span class="mr10">
                    # <p class="fs13 fc_aux mt15"> → fecha relativa ("Hace X días")
                    parrafos = tarjeta.find_all("p")

                    empresa = ""
                    ubicacion = ""
                    fecha = ""

                    for p in parrafos:
                        clases = p.get("class", [])
                        clases_str = " ".join(clases) if clases else ""

                        if "dFlex" in clases_str:
                            # Párrafo de empresa
                            empresa_link = p.find("a", class_=re.compile(r"t_ellipsis|fc_base", re.I))
                            if empresa_link:
                                empresa = limpiar_texto(empresa_link.get_text())
                        elif "fs16" in clases_str and "dFlex" not in clases_str:
                            # Párrafo de ubicación
                            span_ubic = p.find("span", class_="mr10")
                            if span_ubic:
                                ubicacion = limpiar_texto(span_ubic.get_text())
                            else:
                                ubicacion = limpiar_texto(p.get_text())
                        elif "fs13" in clases_str and "fc_aux" in clases_str:
                            # Párrafo de fecha
                            fecha = limpiar_texto(p.get_text())

                    # Salario (tag opcional)
                    salario_el = tarjeta.find(class_=re.compile(r"salary|salario|tag", re.I))
                    salario = limpiar_texto(salario_el.get_text()) if salario_el else ""

                    resultados.append({
                        "title": titulo,
                        "organization": empresa,
                        "location": ubicacion,
                        "salary": salario,
                        "url": link,
                        "date_posted": fecha,
                        "source": "CompuTrabajo",
                        "description_snippet": "",
                    })

                except Exception:
                    continue

            logging.info(f"  Página {pagina}: {len(tarjetas)} ofertas para '{termino}'")
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        except requests.exceptions.Timeout:
            logging.warning(f"Timeout en página {pagina} para '{termino}'")
            break
        except Exception as e:
            logging.error(f"Error scraping '{termino}' página {pagina}: {e}")
            break

    return resultados


def main():
    load_dotenv_if_available()

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
            resultados = scrape_computrabajo(kw)
            nuevos = 0

            for job in resultados:
                job_url = job.get("url", "")
                if job_url and job_url not in seen_urls:
                    seen_urls.add(job_url)
                    job["carrera_origen"] = carrera
                    job["termino_busqueda"] = kw
                    all_jobs.append(job)
                    nuevos += 1

            if resultados:
                logging.info(f"  '{kw}': {len(resultados)} resultados, {nuevos} nuevos")

    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(os.path.dirname(script_dir), "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"computrabajo_batch_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    logging.info(f"Extracción completada: {len(all_jobs)} vacantes únicas en {output_path}")


def load_dotenv_if_available():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


if __name__ == "__main__":
    main()
