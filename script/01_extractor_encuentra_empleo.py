"""
01_extractor_encuentra_empleo.py
Extractor de vacantes desde Encuentra Empleo (Ministerio del Trabajo de Ecuador).
Portal de concursos de mérito y oposición del sector público.

Usa JSF AJAX calls directas (requests puro, sin Playwright).
Estructura descubierta inspeccionando el tráfico de red (junio 2026):
  - GET la página → obtener JSESSIONID + ViewState
  - POST JSF AJAX para abrir modal de vacantes por institución
  - POST JSF AJAX para paginar dentro del modal
  - Parsear respuesta XML con las vacantes

Uso:
    python script/01_extractor_encuentra_empleo.py
    python script/01_extractor_encuentra_empleo.py --test   # Solo 3 páginas
"""

import os
import sys
import json
import logging
import re
import time
import random
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

try:
    import requests
    from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
    import warnings
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except ImportError:
    logging.error("Faltan librerías. Ejecuta: pip install requests beautifulsoup4 lxml")
    sys.exit(1)


# ── Configuración ────────────────────────────────────────────
URL = "https://encuentraempleo.trabajo.gob.ec/socioEmpleo-war/paginas/procesos/busquedaOfertaPublica.jsf"
ROWS_PER_PAGE = 15  # Pedir 15 instituciones por página (máx del portal)
VACANTES_ROWS = 100  # Pedir hasta 100 vacantes por institución
DELAY_MIN = 1.0
DELAY_MAX = 2.5
TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    ),
    "Accept": "application/xml, text/xml, */*; q=0.01",
    "Accept-Language": "es-EC,es;q=0.9,en;q=0.8",
    "Faces-Request": "partial/ajax",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
}


def extraer_viewstate(html):
    """Extrae el javax.faces.ViewState del HTML/XML de respuesta."""
    # En respuestas AJAX (XML), el ViewState viene en un CDATA
    match = re.search(
        r'<update\s+id="javax\.faces\.ViewState"><!\[CDATA\[(.*?)\]\]></update>',
        html, re.DOTALL
    )
    if match:
        return match.group(1)

    # En la página HTML inicial
    match = re.search(
        r'name="javax\.faces\.ViewState"[^>]*value="([^"]*)"',
        html
    )
    if match:
        return match.group(1)

    return None


def parsear_tabla_instituciones(html):
    """
    Parsea la tabla de instituciones del HTML/XML de respuesta.
    Solo extrae filas reales del datatable de PrimeFaces (tbody con id que
    contiene '_data'). Filtra encabezados, labels de formulario y filas UI.
    Retorna lista de dicts con nombre, nuevas_vacantes.
    """
    soup = BeautifulSoup(html, "lxml")
    instituciones = []

    # Buscar el tbody del datatable de PrimeFaces
    tbody = soup.find("tbody", id=re.compile(r"itemsTable_data"))
    if tbody:
        rows = tbody.find_all("tr", recursive=False)
    else:
        rows = soup.find_all("tr")

    # Patrones que indican filas UI, no instituciones reales
    UI_PATTERNS = [
        "Institución", "Nuevas vacantes", "Buscar por",
        "Ordenar por", "Código del puesto", "Denominación",
    ]

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        nombre = cells[0].get_text(strip=True)
        if not nombre:
            continue

        # Filtrar filas de UI/encabezados
        if any(pat in nombre for pat in UI_PATTERNS):
            continue

        vacantes_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""

        # Extraer el data-ri (row index real de PrimeFaces) si existe
        row_index = row.get("data-ri")

        instituciones.append({
            "nombre": nombre,
            "vacantes_text": vacantes_text,
            "row_index": int(row_index) if row_index is not None else None,
        })

    return instituciones


def parsear_vacantes_modal(xml_response):
    """
    Parsea las vacantes del XML de respuesta JSF cuando se abre el modal.
    La respuesta JSF AJAX tiene formato:
    <partial-response><changes><update id="..."><![CDATA[...HTML...]]></update></changes></partial-response>
    """
    vacantes = []

    # Extraer el contenido HTML del CDATA en la respuesta XML
    updates = re.findall(
        r'<update\s+id="[^"]*"><!\[CDATA\[(.*?)\]\]></update>',
        xml_response, re.DOTALL
    )

    for update_html in updates:
        soup = BeautifulSoup(update_html, "lxml")
        rows = soup.find_all("tr")

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 5:
                continue

            codigo = cells[0].get_text(strip=True)
            denominacion = cells[1].get_text(strip=True)
            num_vacantes = cells[2].get_text(strip=True)
            rmu = cells[3].get_text(strip=True)
            ubicacion = cells[4].get_text(strip=True)

            # Filtrar encabezados y filas vacías
            if not denominacion:
                continue
            if codigo.upper().startswith("CÓDIGO") or denominacion.upper().startswith("DENOMINACIÓN"):
                continue

            # Extraer etapa si hay más columnas
            etapa = ""
            if len(cells) > 6:
                etapa = cells[6].get_text(strip=True)

            vacantes.append({
                "codigo_puesto": codigo,
                "title": denominacion,
                "num_vacantes": num_vacantes,
                "salary": rmu,
                "location": ubicacion,
                "etapa": etapa,
            })

    return vacantes


def main():
    modo_test = "--test" in sys.argv

    session = requests.Session()
    session.headers.update({
        "User-Agent": HEADERS["User-Agent"],
        "Accept-Language": HEADERS["Accept-Language"],
    })

    # ── Paso 1: Cargar página inicial para obtener JSESSIONID + ViewState ──
    logging.info("Cargando página inicial de Encuentra Empleo...")
    try:
        resp = session.get(URL, timeout=TIMEOUT)
        if resp.status_code != 200:
            logging.error(f"Error cargando página: HTTP {resp.status_code}")
            return
    except Exception as e:
        logging.error(f"Error conectando: {e}")
        return

    viewstate = extraer_viewstate(resp.text)
    if not viewstate:
        logging.error("No se pudo extraer ViewState de la página inicial")
        return

    logging.info(f"  JSESSIONID obtenido. ViewState: {viewstate[:50]}...")

    # Contar total de registros
    match = re.search(r'Total:\s*(\d+)\s*registros', resp.text)
    total = int(match.group(1)) if match else 0
    logging.info(f"  Total: {total} instituciones registradas")

    all_jobs = []
    pagina = 0
    max_paginas = 3 if modo_test else 999
    instituciones_total = 0

    # ── Paso 2: Iterar páginas de instituciones ──
    while pagina < max_paginas:
        first = pagina * ROWS_PER_PAGE

        if pagina > 0:
            # Paginar la tabla principal
            logging.info(f"--- Cargando página {pagina + 1} (offset {first}) ---")
            data = {
                "javax.faces.partial.ajax": "true",
                "javax.faces.source": "formBuscaPublica:itemsTable",
                "javax.faces.partial.execute": "formBuscaPublica:itemsTable",
                "javax.faces.partial.render": "formBuscaPublica:itemsTable",
                "formBuscaPublica:itemsTable": "formBuscaPublica:itemsTable",
                "formBuscaPublica:itemsTable_pagination": "true",
                "formBuscaPublica:itemsTable_first": str(first),
                "formBuscaPublica:itemsTable_rows": str(ROWS_PER_PAGE),
                "formBuscaPublica:itemsTable_skipChildren": "true",
                "formBuscaPublica:itemsTable_encodeFeature": "true",
                "formBuscaPublica": "formBuscaPublica",
                "formBuscaPublica:j_idt19": "",  # Campo búsqueda institución
                "javax.faces.ViewState": viewstate,
            }

            try:
                resp = session.post(URL, data=data, headers=HEADERS, timeout=TIMEOUT)
                new_vs = extraer_viewstate(resp.text)
                if new_vs:
                    viewstate = new_vs
            except Exception as e:
                logging.error(f"Error paginando: {e}")
                break

            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        # Parsear instituciones de esta página
        page_html = resp.text
        instituciones = parsear_tabla_instituciones(page_html)

        if not instituciones:
            logging.info("  No hay más instituciones. Fin.")
            break

        logging.info(f"  Encontradas {len(instituciones)} instituciones en página {pagina + 1}")

        # ── Paso 3: Para cada institución, abrir modal de vacantes ──
        for i, inst in enumerate(instituciones):
            # Usar el data-ri real de PrimeFaces si está disponible
            row_index = inst.get("row_index")
            if row_index is None:
                row_index = i  # Fallback al índice del loop

            logging.info(f"  [{instituciones_total + 1}] {inst['nombre']}: {inst['vacantes_text']}")

            # Hacer la llamada AJAX para abrir el modal de vacantes
            # El source es: formBuscaPublica:itemsTable:{ROW}:j_idt36
            source_id = f"formBuscaPublica:itemsTable:{row_index}:j_idt36"
            data = {
                "javax.faces.partial.ajax": "true",
                "javax.faces.source": source_id,
                "javax.faces.partial.execute": source_id,
                "javax.faces.partial.render": "vacantesModal",
                source_id: source_id,
                "javax.faces.ViewState": viewstate,
            }

            try:
                resp = session.post(URL, data=data, headers=HEADERS, timeout=TIMEOUT)

                new_vs = extraer_viewstate(resp.text)
                if new_vs:
                    viewstate = new_vs

                # Parsear vacantes de la primera página del modal
                vacantes = parsear_vacantes_modal(resp.text)

                # Paginar dentro del modal si hay más vacantes
                # El modal muestra 5 por defecto, pedimos páginas adicionales
                vacantes_offset = 5
                max_modal_pages = 10  # Máx 50 vacantes por institución
                while len(vacantes) >= vacantes_offset and vacantes_offset < max_modal_pages * 5:
                    modal_data = {
                        "javax.faces.partial.ajax": "true",
                        "javax.faces.source": "vacantesMpForm:vacantesTableMp",
                        "javax.faces.partial.execute": "vacantesMpForm:vacantesTableMp",
                        "javax.faces.partial.render": "vacantesMpForm:vacantesTableMp",
                        "vacantesMpForm:vacantesTableMp": "vacantesMpForm:vacantesTableMp",
                        "vacantesMpForm:vacantesTableMp_pagination": "true",
                        "vacantesMpForm:vacantesTableMp_first": str(vacantes_offset),
                        "vacantesMpForm:vacantesTableMp_rows": "5",
                        "vacantesMpForm:vacantesTableMp_skipChildren": "true",
                        "vacantesMpForm:vacantesTableMp_encodeFeature": "true",
                        "vacantesMpForm": "vacantesMpForm",
                        "javax.faces.ViewState": viewstate,
                    }
                    resp2 = session.post(URL, data=modal_data, headers=HEADERS, timeout=TIMEOUT)
                    new_vs2 = extraer_viewstate(resp2.text)
                    if new_vs2:
                        viewstate = new_vs2
                    nuevas = parsear_vacantes_modal(resp2.text)
                    if not nuevas:
                        break
                    vacantes.extend(nuevas)
                    vacantes_offset += 5
                    time.sleep(0.3)

                for v in vacantes:
                    v["organization"] = inst["nombre"]
                    v["source"] = "EncuentraEmpleo"
                    v["url"] = URL
                    v["date_posted"] = datetime.now().strftime("%Y-%m-%d")
                    all_jobs.append(v)

                if vacantes:
                    logging.info(f"    → {len(vacantes)} vacantes extraídas")

            except Exception as e:
                logging.warning(f"    Error: {e}")

            instituciones_total += 1
            time.sleep(random.uniform(0.5, 1.5))

        pagina += 1

        if first + ROWS_PER_PAGE >= total:
            logging.info("  Última página alcanzada.")
            break

    # ── Guardar resultados ──
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(os.path.dirname(script_dir), "data", "raw")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"encuentra_empleo_batch_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, ensure_ascii=False, indent=2)

    logging.info(f"Extracción completada: {len(all_jobs)} vacantes de {instituciones_total} instituciones")
    logging.info(f"Guardado en: {output_path}")
    logging.info("NOTA: El matching con carreras UNL se hace en la fase de procesamiento en R")


if __name__ == "__main__":
    main()
