# Empleabilidad UNL

Pipeline ETL para el Observatorio de Empleabilidad de la Universidad Nacional de Loja (UNL).

## Objetivo

Capturar, procesar y analizar vacantes laborales del mercado ecuatoriano para medir la empleabilidad de las 40 carreras de la UNL. El sistema extrae datos de 6 portales de empleo, los unifica en un schema estandarizado y genera indicadores por carrera, ciudad, habilidades y salario.

## Stack tecnológico

- **Python 3.10+**: Extracción de datos (APIs y web scraping)
- **R 4.4+**: Procesamiento, limpieza analítica y visualización (tidyverse, sf, jsonlite, digest)
- **RStudio**: IDE principal (proyecto `.Rproj` con Python integrado)

## Estructura del proyecto

```
empleabilidad_unl/
├── script/                        # Scripts de extracción y procesamiento
│   ├── 01_extractor_linkedin.py       # LinkedIn via Fantastic Jobs API
│   ├── 01_extractor_jobspy.py         # Indeed + Google Jobs via python-jobspy
│   ├── 01_extractor_computrabajo.py   # CompuTrabajo (scraping)
│   ├── 01_extractor_multitrabajos.py  # Multitrabajos (API interna)
│   ├── 01_extractor_jooble.py         # Jooble (API interna + tls_client)
│   ├── 01_extractor_encuentra_empleo.py # EncuentraEmpleo (JSF AJAX)
│   ├── 02_procesamiento_inicial.R     # Unificación multi-fuente + NLP
│   └── extract_catalogs.py            # Utilidad para generar catálogos
├── config/
│   └── catalogos.json                 # 40 carreras UNL, habilidades, ciudades
├── data/                              # NO se sube a GitHub
│   ├── raw/                           # JSONs crudos por fuente y fecha
│   ├── processed/                     # df_vacantes_limpio.rds/.csv
│   └── mapa_cantones_ecuador.rds      # Shapefile 221 cantones (sf)
├── documents/                         # Brief del cliente y documentación
├── archive/                           # Código legacy
├── .env                               # API keys (NO se sube a GitHub)
├── requirements.txt                   # Dependencias Python
└── empleabilidad_unl.Rproj
```

## Fuentes de datos

| Fuente | Script | Método | Costo | Estado |
|--------|--------|--------|-------|--------|
| LinkedIn | `01_extractor_linkedin.py` | API Fantastic Jobs (RapidAPI) | ~$45/mes | ✅ Funcional |
| Indeed + Google Jobs | `01_extractor_jobspy.py` | python-jobspy (scraping) | $0 | ✅ Funcional |
| CompuTrabajo | `01_extractor_computrabajo.py` | Web scraping (requests + BS4) | $0 | ✅ Funcional |
| Multitrabajos | `01_extractor_multitrabajos.py` | API interna JSON (x-site-id: BMEC) | $0 | ✅ Funcional |
| Jooble | `01_extractor_jooble.py` | API interna + tls_client (bypass CF) | $0 | ✅ Funcional |
| Encuentra Empleo | `01_extractor_encuentra_empleo.py` | JSF AJAX (requests puro) | $0 | ✅ Funcional |

Costo total estimado: **~$45/mes** (solo LinkedIn API).

## Procesamiento (02_procesamiento_inicial.R)

El script R unifica las 6 fuentes en un dataframe estandarizado de 26 columnas:

- **Lectura**: Detecta la fuente por nombre de archivo, usa solo el batch más reciente por fuente
- **Estandarización**: Mapea los campos distintos de cada fuente a un schema común
- **Ubicación**: Normaliza ciudades/provincias usando diccionario oficial de 221 cantones del Ecuador (shapefile `mapa_cantones_ecuador.rds`)
- **Fechas**: Parsea formatos ISO, dd-mm-yyyy, y relativos ("Hace 2 días", "Más de 30 días")
- **Habilidades**: Extrae habilidades hard/soft de la descripción usando catálogo (LinkedIn ya trae IA)
- **Matching carreras**: Asigna carreras UNL afines por NLP (word boundaries + mínimo 2 hits para evitar falsos positivos)
- **Deduplicación**: Nivel 1 (hash exacto título+empresa+fecha) + Nivel 2 (normalización cross-source)
- **Output**: `data/processed/df_vacantes_limpio.rds` y `.csv`

### Schema de salida

| Columna | Descripción |
|---------|-------------|
| `id_unico` | Hash MD5 (título + empresa + fecha) |
| `fecha_extraccion` | Fecha de ejecución del pipeline |
| `fecha_publicacion` | Fecha de publicación normalizada |
| `fuente` | Portal de origen |
| `titulo_puesto` | Nombre del cargo |
| `empresa` | Nombre de la empresa |
| `ubicacion_ciudad` | Cantón normalizado |
| `provincia` | Provincia (24 del Ecuador) |
| `modalidad` | Presencial / Híbrido / Remoto |
| `habilidades_hard` | Habilidades técnicas extraídas |
| `habilidades_soft` | Habilidades blandas extraídas |
| `salario_min` / `salario_max` | Rango salarial en USD |
| `experiencia_min` | Años de experiencia requeridos |
| `requiere_maestria` | TRUE/FALSE |
| `carreras_afines` | Carreras UNL matcheadas (puede ser múltiple) |
| `descripcion_raw` | Texto original de la vacante |
| `url_oferta` | Link directo a la oferta |
| `lat` / `lng` | Coordenadas GPS (solo LinkedIn) |

## Configuración

1. Clonar el repositorio
2. Crear archivo `.env`:
   ```
   RAPIDAPI_KEY="tu_api_key"
   RAPIDAPI_HOST_LINKEDIN="linkedin-job-search-api.p.rapidapi.com"
   ```
3. Instalar dependencias Python: `pip install -r requirements.txt`
4. Instalar paquetes R: `install.packages(c("tidyverse", "jsonlite", "here", "digest", "sf"))`
5. Abrir `empleabilidad_unl.Rproj` en RStudio

## Flujo de trabajo

```
1. EXTRACCIÓN (Python)          2. PROCESAMIENTO (R)         3. ANÁLISIS (R)
   01_extractor_*.py               02_procesamiento_          03_analisis.R
   → data/raw/*.json               inicial.R                  (pendiente)
                                   → data/processed/
   6 fuentes × 40 carreras         df_vacantes_limpio.rds
   ~200 términos de búsqueda       508+ vacantes únicas
```

### Ejecución rápida (modo test, 3 carreras)

```bash
python script/01_extractor_linkedin.py --test
python script/01_extractor_jobspy.py --test
python script/01_extractor_computrabajo.py --test
python script/01_extractor_multitrabajos.py --test
python script/01_extractor_jooble.py --test
python script/01_extractor_encuentra_empleo.py --test
Rscript script/02_procesamiento_inicial.R
```

### Ejecución completa (40 carreras)

```bash
python script/01_extractor_linkedin.py
python script/01_extractor_jobspy.py
python script/01_extractor_computrabajo.py
python script/01_extractor_multitrabajos.py
python script/01_extractor_jooble.py
python script/01_extractor_encuentra_empleo.py
Rscript script/02_procesamiento_inicial.R
```

## Progreso del proyecto

- [x] **Fase 1 — Extracción**: 6 extractores funcionales y probados
- [x] **Fase 2 — Procesamiento**: Unificación multi-fuente, NLP, matching carreras, deduplicación
- [ ] **Fase 3 — Análisis**: Rankings por carrera, mapas de calor, dashboards de habilidades
- [ ] **Fase 4 — Despliegue**: Docker, ejecución mensual automatizada

## Cliente

Universidad Nacional de Loja (UNL) — Observatorio de Empleabilidad
Contacto técnico: Cristian Ortiz
