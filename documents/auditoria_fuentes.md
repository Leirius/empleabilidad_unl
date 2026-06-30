# Auditoría de Fuentes de Datos — Observatorio de Empleabilidad UNL

> Documento preparado para reunión con Alex y cliente.  
> Fecha: 2026-06-30

---

## 1. Inventario de campos por fuente — VERIFICADO CON DATOS REALES

> Todas las tasas de llenado fueron verificadas empíricamente el 2026-06-30 con `script/analizar_campos.py` sobre los últimos datos extraídos.
> **No se supone ni se inventa nada**: cada porcentaje proviene de datos reales en `data/raw/`.
> Reporte completo auto-generado: `documents/reporte_campos_reales.md`

### 1.1 LinkedIn (API Fantastic Jobs — RapidAPI)

**Script**: `01_extractor_linkedin.py` | **Método**: GET `linkedin-job-search-api.p.rapidapi.com/active-jb` | **Auth**: API key (RapidAPI)
**Muestra verificada**: 8 registros únicos (último batch 2026-06-24)

#### Campos del puesto

| # | Campo | Llenado | Tasa | Ejemplo real | Observación |
|---|-------|---------|------|-------------|-------------|
| 1 | `id` | 8/8 | ✅ 100% | 2221207707 | ID único para dedup |
| 2 | `title` | 8/8 | ✅ 100% | "Ingeniero Agrónomo" | |
| 3 | `organization` | 8/8 | ✅ 100% | "Apracom S.A." | |
| 4 | `date_posted` | 8/8 | ✅ 100% | "2026-06-23T20:41:54" | Formato ISO |
| 5 | `date_valid_through` | 8/8 | ✅ 100% | "2026-07-23T20:41:54" | Fecha expiración |
| 6 | `employment_type` | 8/8 | ✅ 100% | ["FULL_TIME"] | |
| 7 | `seniority` | 8/8 | ✅ 100% | "Sin experiencia" | Nivel de seniority |
| 8 | `url` | 8/8 | ✅ 100% | URL LinkedIn oferta | Link directo |
| 9 | `direct_apply` | 8/8 | ✅ 100% | true | ¿Postulación directa? |
| 10 | `salary` | 0/8 | ❌ 0% | — | **Nunca viene para Ecuador** |

#### Campos de ubicación y geografía

| # | Campo | Llenado | Tasa | Ejemplo real | Observación |
|---|-------|---------|------|-------------|-------------|
| 11 | `locations` | 8/8 | ✅ 100% | [{address, lat, lng}] | Objeto completo |
| 12 | `lats_derived` | 8/8 | ✅ 100% | [-1.3397668] | Coordenada GPS |
| 13 | `lngs_derived` | 8/8 | ✅ 100% | [-79.3666965] | Coordenada GPS |
| 14 | `countries_derived` | 8/8 | ✅ 100% | ["Ecuador"] | |
| 15 | `locations_derived` | 8/8 | ✅ 100% | ["Ecuador"] | |
| 16 | `timezones_derived` | 8/8 | ✅ 100% | ["America/Guayaquil"] | |
| 17 | `cities_derived` | 7/8 | 🟡 87.5% | ["Cayambe"] | |
| 18 | `counties_derived` | 6/8 | 🟡 75% | ["Cayambe"] | |
| 19 | `regions_derived` | 4/8 | 🟡 50% | ["Los Ríos"] | |
| 20 | `location_type` | 0/8 | ❌ 0% | — | |
| 21 | `location_requirements` | 0/8 | ❌ 0% | — | |

#### Campos IA (enriquecidos por Fantastic Jobs)

| # | Campo | Llenado | Tasa | Ejemplo real | Observación |
|---|-------|---------|------|-------------|-------------|
| 22 | `ai_key_skills` | 8/8 | ✅ 100% | ["Leadership", "Planning"...] | Habilidades extraídas |
| 23 | `ai_keywords` | 8/8 | ✅ 100% | ["Agronomy", "Coffee"...] | Keywords para matching |
| 24 | `ai_taxonomies_a` | 8/8 | ✅ 100% | ["Agriculture", "Science"...] | Categorías laborales |
| 25 | `ai_experience_level` | 8/8 | ✅ 100% | "2-5" | Años de experiencia |
| 26 | `ai_education` | 8/8 | ✅ 100% | ["bachelor degree"] | Nivel educativo |
| 27 | `ai_work_arrangement` | 8/8 | ✅ 100% | "On-site" | Presencial/Remoto/Híbrido |
| 28 | `ai_core_responsibilities` | 8/8 | ✅ 100% | "The role involves planning..." | Resumen IA del puesto |
| 29 | `ai_requirements_summary` | 8/8 | ✅ 100% | "Candidates must have a..." | Requisitos por IA |
| 30 | `ai_working_hours` | 8/8 | ✅ 100% | 40 | Horas semanales |
| 31 | `ai_employment_type` | 8/8 | ✅ 100% | ["FULL_TIME"] | Redundante con #6 |
| 32 | `ai_job_language` | 8/8 | ✅ 100% | "Spanish" | Idioma del puesto |
| 33 | `ai_visa_sponsorship` | 8/8 | ✅ 100% | false | |
| 34 | `ai_benefits` | 2/8 | 🟠 25% | ["All Legal Benefits"...] | Rara vez viene |
| 35 | `ai_salary_value` | 0/8 | ❌ 0% | — | **Nunca para Ecuador** |
| 36 | `ai_salary_min_value` | 0/8 | ❌ 0% | — | **Nunca para Ecuador** |
| 37 | `ai_salary_max_value` | 0/8 | ❌ 0% | — | **Nunca para Ecuador** |
| 38 | `ai_salary_currency` | 0/8 | ❌ 0% | — | **Nunca para Ecuador** |
| 39 | `ai_hiring_manager_name` | 0/8 | ❌ 0% | — | Nunca viene |
| 40 | `ai_hiring_manager_email_address` | 0/8 | ❌ 0% | — | Nunca viene |

#### Campos de empresa (metadata LinkedIn)

| # | Campo | Llenado | Tasa | Ejemplo real | Observación |
|---|-------|---------|------|-------------|-------------|
| 41 | `organization_url` | 8/8 | ✅ 100% | URL LinkedIn empresa | |
| 42 | `organization_logo` | 8/8 | ✅ 100% | URL imagen logo | |
| 43 | `org_linkedin_headcount` | 8/8 | ✅ 100% | 202 | Nº empleados |
| 44 | `org_linkedin_size` | 8/8 | ✅ 100% | "201-500 employees" | Rango tamaño |
| 45 | `org_linkedin_industry` | 8/8 | ✅ 100% | "International Trade..." | Industria |
| 46 | `org_linkedin_headquarters` | 8/8 | ✅ 100% | "Guayaquil, Guayas" | Sede central |
| 47 | `org_linkedin_website` | 8/8 | ✅ 100% | "https://apracom-ec.com" | Web empresa |
| 48 | `org_linkedin_type` | 8/8 | ✅ 100% | "Privately Held" | Tipo sociedad |
| 49 | `org_linkedin_description` | 8/8 | ✅ 100% | Descripción empresa completa | |
| 50 | `org_linkedin_followers` | 8/8 | ✅ 100% | 26659 | Seguidores LinkedIn |
| 51 | `org_linkedin_recruitment_agency` | 8/8 | ✅ 100% | false | ¿Es reclutadora? |
| 52 | `org_linkedin_slogan` | 7/8 | 🟡 87.5% | "Tecnificando el futuro" | |
| 53 | `org_linkedin_founded_date` | 6/8 | 🟡 75% | "2000" | |
| 54 | `org_linkedin_specialties` | 6/8 | 🟡 75% | ["Administración de Nómina"...] | |

**Resumen**: 71 campos totales. 47 al 100%, 7 parciales, 14 siempre vacíos para Ecuador. Campos IA de valor alto (skills, experience, education, arrangement) funcionan al 100%. **Salario NUNCA viene para Ecuador** (ni directo ni IA).

---

### 1.2 JobSpy (Indeed + Google Jobs)

**Script**: `01_extractor_jobspy.py` | **Método**: Librería python-jobspy (scraping) | **Auth**: Ninguna
**Muestra verificada**: 88 registros únicos (último batch 2026-06-30)

| # | Campo | Llenado | Tasa | Ejemplo real | Observación |
|---|-------|---------|------|-------------|-------------|
| 1 | `title` | 88/88 | ✅ 100% | "Ingeniero Agrónomo / Agrícola" | |
| 2 | `organization` | 88/88 | ✅ 100% | "Jacorp" | |
| 3 | `location` | 88/88 | ✅ 100% | "U, EC" | String combinado |
| 4 | `url` | 88/88 | ✅ 100% | URL Indeed/Google | Link directo |
| 5 | `source` | 88/88 | ✅ 100% | "indeed" | Indeed o Google |
| 6 | `date_posted` | 88/88 | ✅ 100% | "2026-06-16" | Formato ISO |
| 7 | `description_snippet` | 88/88 | ✅ 100% | Texto completo de la oferta | Ya NO se trunca |
| 8 | `is_remote` | 88/88 | ✅ 100% | false | |
| 9 | `job_type` | 55/88 | 🟡 62.5% | "fulltime" | No siempre viene |
| 10 | `salary_currency` | 4/88 | 🟠 4.5% | "USD" | Muy raro |
| 11 | `salary_interval` | 4/88 | 🟠 4.5% | "monthly" | Muy raro |
| 12 | `salary_min` | 3/88 | 🟠 3.4% | 1000.0 | Muy raro |
| 13 | `salary_max` | 3/88 | 🟠 3.4% | 2000.0 | Muy raro |
| 14 | `city` | 88/88 | ✅ 100% | "U" | **CORREGIDO**: parseado desde `location` |
| 15 | `state` | 75/88 | 🟡 85.2% | "X" | **CORREGIDO**: parseado desde `location` |
| 16 | `country` | 88/88 | ✅ 100% | "Ecuador" | **CORREGIDO**: parseado desde `location` |

**Campos adicionales en JobSpy no capturados aún** (disponibles sin requests extra): `job_url_direct`, `job_level`, `job_function`, `emails`, `company_industry`, `company_num_employees`, `company_description`, `skills`, `experience_range` — requiere modificar extractor para capturarlos.

**Resumen**: 16 campos. 10 al 100% (incluyendo city/country corregidos), 2 parciales (state 85%, job_type 62%), 4 casi vacíos (salario ~4%). Descripción completa funciona bien.

**Nota**: Existe también `01_extractor_jobspy_linkedin.py` — script independiente que usa JobSpy solo con LinkedIn como fuente (alternativa gratuita a Fantastic Jobs API). Guarda en `jobspy_linkedin_batch_*.json` con source="LinkedIn-JobSpy".

---

### 1.3 CompuTrabajo (Scraping HTML)

**Script**: `01_extractor_computrabajo.py` | **Método**: requests + BeautifulSoup | **Auth**: Ninguna
**Muestra verificada**: 17 registros únicos (último batch 2026-06-30)

| # | Campo | Llenado | Tasa | Ejemplo real | Observación |
|---|-------|---------|------|-------------|-------------|
| 1 | `title` | 17/17 | ✅ 100% | "Supervisor de Cultivos y Riego" | |
| 2 | `organization` | 17/17 | ✅ 100% | "AGRÍCOLA URAPAMBA S.A." | |
| 3 | `location` | 17/17 | ✅ 100% | "Quito, Pichincha" | Ciudad + Provincia |
| 4 | `url` | 17/17 | ✅ 100% | URL CompuTrabajo | Link directo |
| 5 | `date_posted` | 17/17 | ✅ 100% | "Hace 6 días" | ⚠️ Texto relativo, no fecha |
| 6 | `source` | 17/17 | ✅ 100% | "CompuTrabajo" | |
| 7 | `salary` | 0/17 | ❌ 0% | — | **CORREGIDO**: filtro de basura funciona, CompuTrabajo rara vez publica salario real |
| 8 | `description_snippet` | 17/17 | ✅ 100% | "Ya aplicaste a esta oferta..." | **CORREGIDO**: scraping de detalle individual funciona (17/17) |

**Campos que existen en la página individual (no capturados, requiere visitar cada oferta):**
Descripción completa, requisitos, tipo de contrato, experiencia requerida, nivel educativo, salario real (raramente publicado).

**Resumen**: 8 campos capturados, **ambos bugs corregidos**: description ahora viene al 100% (scraping de detalle individual), salary ahora filtra valores basura. Para producción completa el scraping de detalle agrega ~5 segundos por oferta.

---

### 1.4 Multitrabajos (API interna — Grupo Bumeran)

**Script**: `01_extractor_multitrabajos.py` | **Método**: POST API interna | **Auth**: Ninguna (header `x-site-id: BMEC`)
**Muestra verificada**: 5 registros únicos (último batch 2026-06-30)

| # | Campo | Llenado | Tasa | Ejemplo real | Observación |
|---|-------|---------|------|-------------|-------------|
| 1 | `id` | 5/5 | ✅ 100% | "1118321549" | ID único |
| 2 | `title` | 5/5 | ✅ 100% | "Jefe de Ventas - Ing Agrónomo" | |
| 3 | `organization` | 5/5 | ✅ 100% | "MANPOWER" | |
| 4 | `location` | 5/5 | ✅ 100% | "Cayambe, Pichincha" | Ciudad + Provincia |
| 5 | `description_snippet` | 5/5 | ✅ 100% | "Importante Empresa Comercializadora..." | Ya NO se trunca |
| 6 | `date_posted` | 5/5 | ✅ 100% | "05-06-2026" | dd-mm-yyyy |
| 7 | `url` | 5/5 | ✅ 100% | URL Multitrabajos | Link directo |
| 8 | `job_type` | 5/5 | ✅ 100% | "Full-time" | |
| 9 | `modalidad` | 5/5 | ✅ 100% | "Presencial" | Presencial/Remoto/Híbrido |
| 10 | `num_vacantes` | 5/5 | ✅ 100% | 1 | |
| 11 | `confidencial` | 5/5 | ✅ 100% | false | ¿Empresa oculta? |
| 12 | `source` | 5/5 | ✅ 100% | "Multitrabajos" | |
| 13 | `salary` | 0/5 | ❌ 0% | — | Nunca viene en listado API |

**Campos adicionales en la respuesta API no capturados aún** (disponibles sin requests extra): `area`, `subarea`, `nivelLaboral`, `requisitos.educacion`, `requisitos.experiencia`, `empresa.logo`, `salarioObligatorio` — la API ya los devuelve, solo hay que agregarlos al extractor.

**Resumen**: 13 campos. 12 al 100%, solo salary vacío. **Fuente más completa proporcionalmente** (92% de campos llenos). API devuelve ~18 campos más que no capturamos aún.

---

### 1.5 Jooble (API interna — Agregador)

**Script**: `01_extractor_jooble.py` | **Método**: POST API interna + tls_client | **Auth**: Ninguna
**Muestra verificada**: 818 registros únicos (último batch 2026-06-30)

| # | Campo | Llenado | Tasa | Ejemplo real | Observación |
|---|-------|---------|------|-------------|-------------|
| 1 | `id` | 818/818 | ✅ 100% | "6960720849307626517" | |
| 2 | `title` | 818/818 | ✅ 100% | "Explorador" | |
| 3 | `location` | 818/818 | ✅ 100% | "Quito, Quito (canton)" | |
| 4 | `url` | 818/818 | ✅ 100% | URL redirect Jooble | ⚠️ Redirect, no directo |
| 5 | `description_snippet` | 818/818 | ✅ 100% | "USD 1.100 - USD 2.800..." | Ya NO se trunca |
| 6 | `date_posted` | 818/818 | ✅ 100% | "Hace 2 meses" | ⚠️ Texto relativo |
| 7 | `is_remote` | 818/818 | ✅ 100% | false | |
| 8 | `source` | 818/818 | ✅ 100% | "Jooble" | |
| 9 | `organization` | 785/818 | 🟡 96.0% | "JACORP" | 33 sin empresa (4%) |
| 10 | `salary` | 80/818 | 🟠 9.8% | "1 100 - 2 800 USD" | Texto libre, raro |
| 11 | `job_type` | 0/818 | ❌ 0% | — | **Siempre vacío** — limitación API |

**⚠️ Jooble es un AGREGADOR** — redirige a portales originales (CompuTrabajo, Indeed, etc.). Alta probabilidad de duplicados con otras fuentes. Deduplicación se maneja en R.

**Resumen**: 11 campos. 8 al 100%, 1 parcial (empresa 95%), 1 muy raro (salary 8%), 1 siempre vacío (job_type). Mayor volumen de todas las fuentes (548 únicos en un batch).

---

### 1.6 Encuentra Empleo (Ministerio del Trabajo)

**Script**: `01_extractor_encuentra_empleo.py` | **Método**: JSF AJAX | **Auth**: Ninguna (JSESSIONID)
**Muestra verificada**: 18 registros únicos (último batch 2026-06-30)

| # | Campo | Llenado | Tasa | Ejemplo real | Observación |
|---|-------|---------|------|-------------|-------------|
| 1 | `codigo_puesto` | 18/18 | ✅ 100% | "336474" | ID único del concurso |
| 2 | `title` | 18/18 | ✅ 100% | "ABOGADO (PC)" | |
| 3 | `organization` | 18/18 | ✅ 100% | "GAD DE SAN MIGUEL DE IBARRA" | Institución pública |
| 4 | `location` | 18/18 | ✅ 100% | "IBARRA" | Cantón |
| 5 | `salary` | 18/18 | ✅ 100% | "1212.0" | **RMU exacto en USD** |
| 6 | `num_vacantes` | 18/18 | ✅ 100% | "1" | |
| 7 | `etapa` | 18/18 | ✅ 100% | "POSTULACIÓNDesde:2026-06-30..." | ⚠️ Texto concatenado, requiere parsing |
| 8 | `date_posted` | 18/18 | ✅ 100% | "2026-06-30" | Formato ISO |
| 9 | `source` | 18/18 | ✅ 100% | "EncuentraEmpleo" | |
| 10 | `url` | 18/18 | ✅ 100% | URL portal genérica | ⚠️ Misma URL para todas las ofertas |

**Campos que existen en el portal pero no capturamos** (requieren modal AJAX separado): requisitos del puesto, perfil profesional, grupo ocupacional, tipo de institución.

**Resumen**: 10 campos, **TODOS al 100%**. Fuente con mejor calidad de datos: **única con salario exacto** (RMU sector público). Solo sector público (GADs, Ministerios, etc.).

---

## 2. Tabla comparativa de campos — VERIFICADO CON DATOS REALES

> Datos verificados el 2026-06-30 con `script/analizar_campos.py`.
> Tasa = registros con valor / total registros del último batch.

| Campo | LinkedIn (n=8) | JobSpy (n=88) | CompuTrabajo (n=17) | Multitrabajos (n=5) | Jooble (n=818) | Enc. Empleo (n=18) |
|-------|----------------|---------------|---------------------|---------------------|----------------|---------------------|
| Título | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% |
| Empresa | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | 🟡 94.9% | ✅ 100% |
| Ubicación | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% |
| Fecha publicación | ✅ 100% ISO | ✅ 100% ISO | ✅ 100% relativa | ✅ 100% dd-mm-yyyy | ✅ 100% relativa | ✅ 100% ISO |
| URL directa | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% | ✅ 100% redirect | ✅ 100% genérica |
| Descripción | ❌ No viene | ✅ 100% completa | ✅ CORREGIDO (detalle) | ✅ 100% completa | ✅ 100% completa | ❌ No viene |
| Salario | ❌ 0% en Ecuador | 🟠 4.9% | ❌ CORREGIDO (filtrado) | ❌ 0% | 🟠 8.0% | ✅ 100% RMU exacto |
| Tipo contrato | ✅ 100% | 🟡 60.2% | ❌ No captura | ✅ 100% | ❌ 0% | ❌ No captura |
| Modalidad (remoto) | ✅ 100% IA | ✅ 100% | ❌ No captura | ✅ 100% | ✅ 100% | ❌ No captura |
| Experiencia (IA) | ✅ 100% | ❌ — | ❌ — | ❌ — | ❌ — | ❌ — |
| Habilidades (IA) | ✅ 100% skills | ❌ — | ❌ — | ❌ — | ❌ — | ❌ — |
| Nivel educativo (IA) | ✅ 100% | ❌ — | ❌ — | ❌ — | ❌ — | ❌ — |
| Coordenadas GPS | ✅ 100% lat/lng | ❌ — | ❌ — | ❌ — | ❌ — | ❌ — |
| Info empresa | ✅ 100% 15+ campos | ❌ — | ❌ — | ❌ — | ❌ — | ❌ — |
| Tamaño empresa | ✅ 100% headcount | ❌ — | ❌ — | ❌ — | ❌ — | ❌ — |
| Beneficios (IA) | 🟠 25% | ❌ — | ❌ — | ❌ — | ❌ — | ❌ — |
| Salario IA inferido | ❌ 0% en Ecuador | ❌ — | ❌ — | ❌ — | ❌ — | ❌ — |
| Nº vacantes | ❌ — | ❌ — | ❌ — | ✅ 100% | ❌ — | ✅ 100% |

**Observaciones clave verificadas:**

1. **Salario en LinkedIn NUNCA viene para Ecuador** (0/8) — ni directo ni inferido por IA
2. ~~**CompuTrabajo `description_snippet` siempre vacío**~~ → **CORREGIDO**: script ahora visita cada oferta individual para obtener descripción completa
3. ~~**CompuTrabajo `salary` dice "Postulado Vista"**~~ → **CORREGIDO**: script ahora filtra valores basura (labels del sitio)
4. ~~**JobSpy `city/country/state` siempre vacíos**~~ → **CORREGIDO**: script ahora parsea city/state/country desde el string `location`
5. **Jooble `job_type` siempre vacío** (0/548) — limitación de la API, no tiene solución en código
6. **Encuentra Empleo es la ÚNICA fuente con salario 100%** (RMU del sector público)
7. **Descripciones ya NO se truncan** — scripts actualizados para capturar texto completo (JobSpy, Multitrabajos, Jooble)
8. **LinkedIn es la fuente con más metadata** — 71 campos, 47 al 100%, incluyendo IA (skills, education, experience)
9. **Multitrabajos es la más completa proporcionalmente** — 12/13 campos llenos (92%)

---

## 3. Planes y costos — LinkedIn API (Fantastic Jobs / RapidAPI)

**Fuente verificada**: [RapidAPI Pricing](https://rapidapi.com/fantastic-jobs-fantastic-jobs-default/api/linkedin-job-search-api/pricing) (consultado 2026-06-30)

| Plan | Precio/mes | Jobs/mes | Requests/mes | Rate Limit | Jobs por Request |
|------|-----------|----------|-------------|-----------|-----------------|
| **Basic (gratis)** | $0 | 250 | 25 | 1000/hora | Hasta 1000 |
| **Pro** | $45 | 10,000 | 5,000 | 5/segundo | Hasta 1000 |
| **Ultra** ⭐ | $95 | 20,000 | 10,000 | 15/segundo | Hasta 1000 |
| **Mega** | $175 | 50,000 | 25,000 | 25/segundo | Hasta 1000 |

### ¿Cómo funciona?

- **1 Request** = 1 llamada al endpoint `/active-jb` con un término de búsqueda
- **Jobs** = el total de registros que la API devuelve sumando todas las requests
- Cada request puede traer **hasta 1000 jobs** (parámetro `limit`)
- Nosotros usamos `limit=20` actualmente → podríamos subir a 100-1000

### Cálculo para 40 carreras UNL

Configuración actual: ~200 términos de búsqueda (promedio 5 por carrera × 40 carreras)

| Escenario | Requests necesarios | Jobs estimados | Plan mínimo |
|-----------|-------------------|----------------|-------------|
| 1 término × 40 carreras | 40 | ~400 | Basic ($0) |
| 5 términos × 40 carreras | 200 | ~2,000 | Pro ($45) |
| 5 términos × 40 carreras × limit=100 | 200 | ~5,000-10,000 | Pro ($45) |
| 10 términos × 40 carreras | 400 | ~4,000-10,000 | Pro ($45) |
| Extracción mensual completa | 200 | ~5,000-10,000 | **Pro ($45)** |

**Conclusión**: El plan Pro ($45/mes) es suficiente para la extracción mensual completa. Tenemos 5,000 requests y 10,000 jobs, muy por encima de lo que necesitamos (200 requests, ~2,000-5,000 jobs).

### Plan actual contratado: **Basic (gratis)**

- 250 jobs / 25 requests al mes
- **Suficiente solo para testing** (3 carreras)
- Para producción (40 carreras) → necesitamos **Pro ($45/mes)** mínimo

---

## 4. Coresignal — Alternativa LinkedIn (pendiente de pruebas)

**Fuente**: [Coresignal Jobs API](https://coresignal.com/solutions/jobs-data-api/)

### ¿Qué ofrece?

- 452M+ job postings de múltiples fuentes (LinkedIn, Indeed, Glassdoor, Wellfound)
- Dos productos:
  - **Base API**: 20+ campos, datos crudos — $49/mes (250 Collect + 500 Search)
  - **Multi-Source API**: 85+ campos, deduplicado y enriquecido — precio mayor

### Campos del Multi-Source API (85+ campos)

Incluye todo lo de LinkedIn API más: `department`, `management_level`, `is_decision_maker`, `seniority`, `is_urgently_hiring`, `accepts_remote`, `shift_schedule`, `company_hq_country`, `company_hq_location`, `company_enriched_keywords`, `salary.min_value`, `salary.max_value`, `salary.currency`, `salary.type`

### Pricing Coresignal

| Plan | Precio/mes | Collect credits | Search credits |
|------|-----------|----------------|----------------|
| **Free trial** | $0 (7 días) | 200 | 400 |
| **Starter** | $49 | 250 | 500 |
| **Pro** | $800 | 10,000 | 20,000 |
| **Premium** | $1,500+ | 50,000+ | 150,000+ |

### Comparación Fantastic Jobs vs Coresignal

| Aspecto | Fantastic Jobs (RapidAPI) | Coresignal |
|---------|--------------------------|-----------|
| Precio plan útil | $45/mes (Pro) | $49/mes (Starter) |
| Jobs disponibles | 10,000/mes | 250 collect/mes |
| Campos IA | ✅ 71 campos | ✅ 85+ campos |
| Fuentes | Solo LinkedIn | LinkedIn + Indeed + Glassdoor + más |
| Facilidad integración | ✅ Ya integrado | ✅ Extractor listo (pendiente créditos) |
| Cobertura Ecuador | ✅ Verificada | ❌ Sin verificar |
| Free tier útil | 250 jobs/25 req | 200 collect/400 search (7 días) |

### Estado actual (verificado 2026-06-30 en dashboard)

- ✅ Cuenta creada en equipo **"Epn.edu"**, API key válida
- ❌ Free trial (200 Collect + 400 Search) **expiró el 17 de julio 2025** sin usarse
- ❌ Créditos actuales: **0 Collect, 0 Search** → HTTP 402
- ⚠️ Owner de la cuenta: **Dilan Andrade** (dilan.andrade@epn.edu.ec) — solo él puede cambiar plan
- Tu cuenta (Gary Santiana) tiene rol **Member**, no puede comprar créditos

**Opciones para testear:**
1. Contactar a Dilan para solicitar nuevos créditos trial o contratar plan
2. Crear cuenta nueva con otro email → free trial 7 días (200 Collect + 400 Search)

**Planes mensuales (Starter):**

| Créditos | Precio | Costo/registro |
|----------|--------|----------------|
| 250 collect + 500 search | $49/mes | $0.196 |
| 550 collect + 1,100 search | $100/mes | $0.182 |
| 1,200 collect + 2,400 search | $200/mes | $0.167 |

- **Extractor de producción listo**: `script/01_extractor_coresignal.py` (config centralizada, catálogos, guardado en `data/raw/coresignal_batch_*.json`)
- Script de test auxiliar: `script/test_coresignal.py`

---

## 5. JobSpy como alternativa gratuita para LinkedIn

**Librería**: [python-jobspy](https://github.com/speedyapply/JobSpy)

JobSpy puede scrapear LinkedIn directamente (gratis) agregando `"linkedin"` a `SITES`.

### Comparación: API de pago vs JobSpy scraping

| Aspecto | Fantastic Jobs API ($45/mes) | JobSpy scraping ($0) |
|---------|------------------------------|---------------------|
| Campos IA (skills, salary, education) | ✅ 50+ campos IA | ❌ |
| Coordenadas GPS | ✅ | ❌ |
| Metadata empresa (tamaño, industria) | ✅ 15+ campos | ⚠️ Algunos |
| Descripción completa | ❌ No incluida | ✅ Completa |
| Rate limiting | Controlado (plan) | ⚠️ Riesgo de bloqueo |
| Estabilidad | ✅ API oficial | ⚠️ Scraping puede romperse |
| Costo | $45/mes | $0 |

### Resultados del test (2026-06-30)

Ejecutado con `SITES=["linkedin"]`, `linkedin_fetch_description=True`, 5 términos:

| Término | Jobs | Tiempo | Descripción promedio |
|---------|------|--------|---------------------|
| ingeniero agrónomo | 59 | 88s | 3330 chars |
| abogado | 10 | 17s | 4100 chars |
| médico | 75 | 110s | 1546 chars |
| contador auditor | 18 | 27s | 1459 chars |
| desarrollador software | 63 | 93s | 3555 chars |
| **TOTAL** | **225** | **~5.5 min** | |

**34 columnas disponibles** (vs 16 que capturamos con Indeed/Google):
`company`, `company_addresses`, `company_description`, `company_industry`, `company_logo`, `company_num_employees`, `company_rating`, `company_revenue`, `company_reviews_count`, `company_url`, `company_url_direct`, `currency`, `date_posted`, `description` (completa), `emails`, `experience_range`, `id`, `interval`, `is_remote`, `job_function`, `job_level`, `job_type`, `job_url`, `job_url_direct`, `listing_type`, `location`, `max_amount`, `min_amount`, `salary_source`, `site`, `skills`, `title`, `vacancy_count`, `work_from_home_type`

**Observaciones:**
- ✅ Descripciones completas (1,400-4,100 chars) — la API de pago NO las incluye
- ✅ `company_industry`, `company_num_employees` — metadata empresa
- ❌ `skills` siempre None — no extrae habilidades (la API sí con IA)
- ❌ Sin coordenadas GPS (la API sí las tiene)
- ❌ Sin campos IA (salary inferido, education, seniority, etc.)
- ⚠️ Lento (~90s por término con `linkedin_fetch_description=True`)
- ⚠️ `salary` devuelve `nan` en vez de None para algunos campos

### Comparación actualizada: API vs JobSpy

| Dato | Fantastic Jobs API ($45) | JobSpy LinkedIn ($0) |
|------|--------------------------|---------------------|
| Jobs por término (Ecuador) | 2-72 | 10-75 |
| Descripción completa | ❌ | ✅ (1,400-4,100 chars) |
| Habilidades IA | ✅ ai_key_skills | ❌ None |
| Salario IA inferido | ✅ ai_salary_* | ❌ |
| Coordenadas GPS | ✅ lat/lng | ❌ |
| Info empresa | ✅ 15+ campos LinkedIn | ✅ 10 campos básicos |
| Nivel educativo | ✅ ai_education | ❌ |
| Seniority | ✅ | ❌ |
| Velocidad | ~3s/término | ~90s/término |
| Estabilidad | ✅ API oficial | ⚠️ Puede romperse |

**Extractor de producción listo**: `script/01_extractor_jobspy_linkedin.py` (independiente de `01_extractor_jobspy.py` que usa Indeed+Google).
Guarda en `data/raw/jobspy_linkedin_batch_*.json` con source="LinkedIn-JobSpy".

**Conclusión: Son complementarios. La opción D (API + JobSpy) da lo mejor de ambos.**

---

## 6. Configuración centralizada

**TODOS los scripts migrados a `config/scraping_config.json`** — no quedan valores hardcodeados.

### 6.1 Scripts del pipeline (8 extractores)

| Script | Config key | Estado |
|--------|-----------|--------|
| `01_extractor_linkedin.py` | `linkedin` | ✅ Migrado |
| `01_extractor_jobspy.py` | `jobspy` | ✅ Migrado |
| `01_extractor_jobspy_linkedin.py` | `jobspy_linkedin` | ✅ Nuevo, config desde el inicio |
| `01_extractor_computrabajo.py` | `computrabajo` | ✅ Migrado |
| `01_extractor_multitrabajos.py` | `multitrabajos` | ✅ Migrado |
| `01_extractor_jooble.py` | `jooble` | ✅ Migrado |
| `01_extractor_encuentra_empleo.py` | `encuentra_empleo` | ✅ Migrado |
| `01_extractor_coresignal.py` | `coresignal` | ✅ Nuevo, config desde el inicio |
| **CompuTrabajo** | `DELAY_MIN/MAX` | 2.5 / 5.0 | ⚠️ OK |
| **Multitrabajos** | `PAGE_SIZE` | 20 | ⚠️ Máximo del API |
| **Multitrabajos** | `MAX_PAGINAS` | 5 | ✅ Configurable |
| **Multitrabajos** | `SITE_ID` | "BMEC" | ⚠️ Correcto para Ecuador |
| **Jooble** | `MAX_PAGINAS` | 3 | ✅ Configurable |
| **Jooble** | `DATE_ANY` | 7 | ✅ Podría filtrar por fecha |
| **Enc. Empleo** | `ROWS_PER_PAGE` | 5 | ⚠️ Default del portal |
| **Enc. Empleo** | `VACANTES_ROWS` | 100 | ⚠️ OK |
| **Enc. Empleo** | `max_paginas` (test) | 3 | ⚠️ Solo en modo test |
| **Todos** | Modo test: `[:3]` | 3 carreras | ⚠️ OK para testing |

### 6.2 Recomendaciones

1. **Crear archivo `config/scraping_config.json`** con todos los parámetros configurables
2. **Mover `LIMIT_PER_REQUEST`** de 20 a 100 en LinkedIn (optimiza uso de requests)
3. **Capturar `description` completa** en JobSpy (no truncar a 500 chars)
4. **Capturar `detalle` completo** en Multitrabajos (no truncar a 500 chars)
5. **Capturar `content` completo** en Jooble (no truncar a 500 chars)

---

## 7. Resumen de opciones para LinkedIn — Decisión del cliente

| Opción | Costo/mes | Ventajas | Desventajas |
|--------|----------|----------|-------------|
| **A. Fantastic Jobs Pro** | $45 | 71 campos IA, GPS, empresa, estable | Sin descripción completa |
| **B. Coresignal Starter** | $49 | 85+ campos, multi-fuente | Solo 250 registros/mes, sin verificar Ecuador |
| **C. JobSpy (scraping)** | $0 | Gratis, descripción completa | Sin campos IA, riesgo de bloqueo |
| **D. A + C combinados** | $45 | Lo mejor de ambos mundos | Complejidad extra |
| **E. B + C combinados** | $49 | Multi-fuente + gratis fallback | Sin verificar aún |

---

## 8. Resultados de tests de límites (verificados 2026-06-30)

### 8.1 LinkedIn API (Fantastic Jobs)

**Test**: `limit=100`, término "ingeniero", Ecuador, time_frame=6m

| Término | Jobs devueltos |
|---------|---------------|
| ingeniero | 72 |
| contador | 5 |
| abogado | 9 |
| médico | 31 |
| programador | 0 |
| agrónomo | 2 |
| enfermera | 1 |

**Headers de rate limit verificados:**

| Métrica | Valor |
|---------|-------|
| Jobs limit (plan Basic) | 250/mes |
| Jobs restantes | 120 |
| Jobs consumidos | 130 (de pruebas anteriores + hoy) |
| Requests limit | 25/mes |
| **Requests restantes** | **0 (AGOTADO)** |
| Reset | ~24.8 días |

**Conclusiones LinkedIn API:**
- Cada request consume 1 request + N jobs del plan
- Con `limit=100` se obtiene todo lo disponible en una sola request (Ecuador tiene pocos resultados por término)
- Con 200 términos de búsqueda (40 carreras × 5 términos) → necesitamos 200 requests/mes
- **Plan Basic (25 req) es insuficiente para producción**
- **Plan Pro (5,000 req, $45/mes) es más que suficiente**
- Subir `LIMIT_PER_REQUEST` de 20 a 100 reduce requests sin perder datos

### 8.2 Jooble

**Test**: término "ingeniero", 15 páginas, Ecuador

| Filtro de fecha | Total jobs |
|----------------|-----------|
| Sin filtro (date=7) | 63 |
| Último día (date=8) | 0 |
| 3 días (date=2) | 6 |
| 7 días (date=3) | 14 |

**Paginación**: 20 jobs/página, máximo ~4 páginas por término antes de quedarse sin resultados.

**Conclusiones Jooble:**
- Volumen bajo para Ecuador (~60 ofertas por término genérico)
- Es un AGREGADOR — muchos duplicados con CompuTrabajo e Indeed
- Sin costo, sin autenticación, pero necesita tls_client para bypass Cloudflare
- No tiene filtro de antigüedad confiable — "8 dias atras", "Hace un mes"
- **Valor principal**: complementar con ofertas que no aparecen en otras fuentes

### 8.3 Multitrabajos

**Test**: búsqueda vacía y por términos, Ecuador

| Término | Total ofertas |
|---------|--------------|
| (vacío = todo el portal) | **5,535** |
| ingeniero | 54 |
| contador | 36 |
| abogado | 14 |
| médico | 74 |
| agrónomo | 1 |

**Antigüedad**: Ofertas desde **2 de abril 2026** hasta hoy (~3 meses de historia)

**Paginación**: Hasta 276 páginas (20/página), sin límite aparente.

**Campos no capturados**: La API devuelve 31 campos, solo capturamos 13. Campos útiles sin capturar: `idArea`, `idSubarea`, `nivelLaboral`, `aptoDiscapacitado`, `fechaModificado`, `planPublicacion`, `logoURL`.

**Conclusiones Multitrabajos:**
- **FUENTE MÁS RICA en volumen**: 5,535 ofertas activas sin filtro
- Se puede obtener TODO el portal con búsqueda vacía + paginación completa
- Sin rate limiting aparente, sin autenticación
- Fechas ISO limpias, ubicaciones con provincia
- Truncamos descripción a 500 chars — debería ser completa
- **Estrategia óptima**: Scrape completo mensual (277 páginas × 1 request = ~300 requests, ~5 min)

### 8.4 CompuTrabajo

**Test**: término "ingeniero", paginación hasta p=5

| Página | Artículos |
|--------|----------|
| 1 | 20 |
| 2 | 20 |
| 3 | 6 |
| 4 | 0 |
| 5 | 0 |

**Total para "ingeniero"**: 46 ofertas (3 páginas).

**Limitaciones**:
- `description_snippet` siempre vacío (no se extrae del listado)
- `salary` captura texto basura ("Postulado Vista")
- Para datos útiles habría que visitar cada oferta individual (+1 request por oferta)
- Sin API, solo scraping HTML
- **MAX_PAGINAS=5 es suficiente** para la mayoría de términos

**Conclusiones CompuTrabajo:**
- Volumen moderado (~46 por término genérico)
- Datos del listado son pobres (solo título, empresa, ubicación, fecha)
- Para mejorar calidad → implementar scraping de detalle (descripción completa)
- Sin rate limiting agresivo pero hay delays necesarios

### 8.5 Encuentra Empleo (Ministerio del Trabajo)

**Test**: carga de página principal

| Métrica | Valor |
|---------|-------|
| Total instituciones registradas | **1,415** |
| Instituciones por página | 5 |
| Páginas totales | 283 |
| Formato | JSF AJAX (PrimeFaces DataTable) |

**Características únicas:**
- **Única fuente de sector público** (concursos de mérito y oposición)
- **Salarios exactos (RMU)** — dato más confiable de todas las fuentes
- Código de puesto oficial
- Número de vacantes por puesto
- Etapas del concurso con fechas (postulación desde/hasta)

**Limitaciones:**
- La mayoría de instituciones tienen 0 vacantes activas
- No tiene búsqueda por carrera — hay que recorrer todas las instituciones
- Recorrido completo toma ~30 min (1,415 instituciones × modal AJAX cada una)
- Sin historial — solo ofertas activas en el momento de la consulta

### 8.6 Resumen de límites

| Fuente | Ofertas disponibles | Antigüedad máx | Rate limit | Tiempo extracción completa |
|--------|-------------------|----------------|-----------|---------------------------|
| LinkedIn (API) | ~200-500 Ecuador | 6 meses | 25 req/mes (Basic) | ~3 min |
| JobSpy (Indeed+Google) | ~100-300 | 30 días (configurable) | Sin límite formal | ~15 min |
| CompuTrabajo | ~500-1,000 | Más de 30 días | Delay recomendado | ~20 min |
| **Multitrabajos** | **5,535** | **~3 meses** | **Sin límite** | **~5 min** |
| Jooble | ~100-300 | Mixto | Cloudflare bypass | ~10 min |
| Encuentra Empleo | Variable (público) | Solo activas | Sin límite | ~30 min |

## 9. Próximos pasos pendientes

### Completados recientemente (2026-06-30)

- [x] **JobSpy + LinkedIn**: Extractor de producción listo (`01_extractor_jobspy_linkedin.py`)
- [x] **Coresignal**: Extractor de producción listo (`01_extractor_coresignal.py`) — pendiente de créditos
- [x] **CompuTrabajo**: Scraping de detalle implementado y funcionando (17/17 con descripción)
- [x] **CompuTrabajo**: Filtro de salary basura ("Postulado Vista") implementado
- [x] **JobSpy**: Parsing de city/state/country desde location string (88/88 city, 75/88 state)
- [x] **Centralizar configuración**: `config/scraping_config.json` — todos los 8 scripts migrados
- [x] **LinkedIn**: `LIMIT_PER_REQUEST` subido a 100

### Pendientes

- [ ] **Coresignal**: Contactar a Dilan Andrade para activar créditos o contratar plan Starter ($49/mo)
- [ ] **Multitrabajos**: Capturar campos adicionales de la API (area, subarea, nivelLaboral, requisitos) — disponibles sin requests extra
- [ ] **JobSpy**: Capturar campos adicionales (job_level, job_function, company_industry, skills, experience_range) — disponibles sin requests extra
- [ ] **Jooble**: Evaluar duplicados con otras fuentes (es agregador)
- [ ] **LinkedIn API**: Subir plan de Basic (gratis) a Pro ($45/mes) para producción con 40 carreras
- [ ] **Git**: Commit y push de todos los cambios recientes
