"""
01_extractor_labora_uio.py
Scraper de vacantes desde la Bolsa Metropolitana de Empleo (ConQuito, Quito).

ESTADO (junio 2026):
    El dominio original labora.uio.ec YA NO EXISTE.
    La plataforma migró a: https://bolsaempleo.odoo.com
    REQUIERE LOGIN para acceder a las ofertas.

    Este script NO funciona actualmente porque el portal requiere
    autenticación. Opciones:
    1. Registrarse como candidato y usar las credenciales
    2. Descartar esta fuente (solo cubre Quito)
    3. Scraping con Playwright post-login (requiere credenciales)

    Por ahora el script está deshabilitado y muestra este mensaje.

Uso:
    python script/01_extractor_labora_uio.py
    python script/01_extractor_labora_uio.py --test
"""

import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    logging.warning(
        "SCRAPER DESCARTADO: Labora UIO (labora.uio.ec) ya no existe.\n"
        "  Migró a: https://bolsaempleo.odoo.com (Bolsa Metropolitana de Empleo, ConQuito)\n"
        "  RESULTADO DE EXPLORACIÓN (junio 2026):\n"
        "    - No es un job board público. Es un servicio de matching interno.\n"
        "    - Los candidatos registran su perfil y ConQuito los matchea con empresas.\n"
        "    - No hay listado de vacantes accesible, ni siquiera logueado.\n"
        "    - El backend Odoo (JSON-RPC) devuelve AccessError en todos los modelos.\n"
        "    - Solo cubre Quito.\n"
        "  DECISIÓN: Fuente descartada. No es viable para scraping."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
