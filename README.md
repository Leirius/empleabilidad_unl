# Empleabilidad UNL

Pipeline ETL para el Observatorio de Empleabilidad de la Universidad Nacional de Loja (UNL).

## Objetivo

Capturar, procesar y analizar vacantes laborales del mercado ecuatoriano para medir la empleabilidad de las 40 carreras de la UNL. El sistema extrae datos de múltiples portales de empleo, los normaliza y genera indicadores por carrera, ciudad y habilidades demandadas.

## Stack tecnológico

- **Python**: Extracción de datos (APIs y web scraping)
- **R**: Procesamiento, limpieza analítica y visualización (tidyverse, sf, jsonlite)
- **RStudio**: IDE principal (proyecto `.Rproj` con Python integrado)

## Estructura del proyecto

```
empleabilidad_unl/
├── script/           # Scripts de extracción (Python) y procesamiento (R)
├── config/           # Catálogos y configuración (carreras, habilidades, ciudades)
├── data/             # Datos crudos y procesados (NO se sube a GitHub)
│   ├── raw/          # JSON/CSV descargados de las APIs/scraping
│   └── processed/    # Datos limpios y listos para análisis
├── documents/        # Documentación del proyecto y brief del cliente
├── archive/          # Código legacy y archivos de referencia
├── .env              # API keys (NO se sube a GitHub)
├── requirements.txt  # Dependencias de Python
└── empleabilidad_unl.Rproj
```

## Fuentes de datos

| Fuente | Script | Método | Estado |
|--------|--------|--------|--------|
| LinkedIn | `01_extractor_linkedin.py` | API Fantastic Jobs (RapidAPI) | Funcional |
| Indeed + Google Jobs | `01_extractor_jobspy.py` | python-jobspy (scraping directo) | Funcional |
| CompuTrabajo | `01_extractor_computrabajo.py` | Web scraping (requests + BS4) | Funcional |
| Multitrabajos | `01_extractor_multitrabajos.py` | API interna JSON (x-site-id: BMEC) | Bug: filtro keyword |
| Encuentra Empleo | `01_extractor_encuentra_empleo.py` | JSF AJAX (requests puro) | Bug: modal no cambia |
| Jooble | `01_extractor_jooble.py` | API interna + tls_client (bypass Cloudflare) | Funcional |
| Labora UIO | `01_extractor_labora_uio.py` | — | Descartado (no es job board) |

## Configuración

1. Clonar el repositorio
2. Crear archivo `.env` con la API key de RapidAPI (para LinkedIn):
   ```
   RAPIDAPI_KEY="tu_api_key"
   ```
3. Instalar dependencias Python: `pip install -r requirements.txt`
4. Abrir `empleabilidad_unl.Rproj` en RStudio

## Flujo de trabajo

1. **Extracción** (Python): Scripts `01_*.py` descargan datos a `data/raw/`
2. **Procesamiento** (R): Scripts `02_*.R` limpian, deduplican y normalizan
3. **Análisis** (R): Scripts `03_*.R` generan indicadores y visualizaciones

## Cliente

Universidad Nacional de Loja (UNL) - Observatorio de Empleabilidad
