# 02_procesamiento_inicial.R
# Script para unificar, limpiar y procesar vacantes de 6 fuentes distintas
# Genera el schema del cliente con 18+ columnas estandarizadas
#
# Fuentes soportadas:
#   1. LinkedIn (API Fantastic Jobs) - JSON con datos enriquecidos por IA
#   2. JobSpy (Indeed + Google Jobs) - JSON con campos de salary
#   3. CompuTrabajo - JSON básico (scraping)
#   4. Multitrabajos - JSON con modalidad y tipo de trabajo
#   5. Jooble - JSON con is_remote y job_type
#   6. Encuentra Empleo - JSON sector público (RMU, código puesto)
#
# Uso:
#   source("script/02_procesamiento_inicial.R")

library(tidyverse)
library(jsonlite)
library(lubridate)
library(here)
library(digest)  # Para generar id_unico con hash
library(sf)      # Para leer mapa de cantones (geometría)

# ── 1. Configuración ─────────────────────────────────────────────

raw_dir    <- here("data", "raw")
config_dir <- here("config")
out_dir    <- here("data", "processed")
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

# Cargar catálogos
catalogos <- fromJSON(file.path(config_dir, "catalogos.json"))

habilidades_hard  <- tolower(catalogos$habilidades_hard)
habilidades_soft  <- tolower(catalogos$habilidades_soft)
terminos_carrera  <- catalogos$terminos_por_carrera  # 40 carreras UNL con términos de búsqueda

# Diccionario oficial de cantones/provincias del Ecuador (221 cantones, 24 provincias)
# Fuente: mapa_cantones_ecuador.rds (shapefile con DPA_DESPRO, DPA_DESCAN)
cantones_sf <- readRDS(here("data", "mapa_cantones_ecuador.rds"))
cantones_df <- st_drop_geometry(cantones_sf) %>%
  mutate(
    canton_lower = tolower(DPA_DESCAN),
    provincia    = str_to_title(DPA_DESPRO),
    canton       = str_to_title(DPA_DESCAN)
  ) %>%
  select(canton_lower, canton, provincia, cod_provincia = DPA_PROVIN, cod_canton = DPA_CANTON)

# Crear lookup: clave → (canton, provincia)
# Incluye cantones + provincias como fallback
canton_lookup <- cantones_df %>%
  select(clave = canton_lower, canton, provincia) %>%
  bind_rows(
    # Agregar provincias como claves (para cuando la ubicación solo dice la provincia)
    cantones_df %>%
      group_by(provincia) %>%
      slice(1) %>%   # Capital de provincia = primer cantón (por código DPA)
      ungroup() %>%
      mutate(clave = tolower(provincia)) %>%
      select(clave, canton, provincia)
  ) %>%
  # Agregar alias comunes
  bind_rows(tribble(
    ~clave,           ~canton,                           ~provincia,
    "lago agrio",     "Lago Agrio",                      "Sucumbíos",
    "coca",           "Francisco de Orellana",            "Orellana",
    "sangolquí",      "Rumiñahui",                        "Pichincha",
    "sangolqui",      "Rumiñahui",                        "Pichincha",
    "santo domingo",  "Santo Domingo",                    "Santo Domingo de los Tsáchilas",
    "samborondón",    "Samborondón",                      "Guayas",
    "samborondon",    "Samborondón",                      "Guayas",
    "durán",          "Durán",                            "Guayas",
    "duran",          "Durán",                            "Guayas",
  )) %>%
  distinct(clave, .keep_all = TRUE)

message(sprintf("  Diccionario de ubicaciones: %d entradas (cantones + provincias + alias)",
                nrow(canton_lookup)))

# ── 2. Funciones auxiliares ──────────────────────────────────────

#' Normalizar ubicación usando el diccionario oficial de cantones del Ecuador
#' Busca match en canton_lookup (221 cantones + 24 provincias + alias)
#' @param ubicacion String con la ubicación cruda
#' @return tibble de 1 fila con ciudad y provincia
normalizar_ubicacion <- function(ubicacion) {
  if (is.na(ubicacion) || ubicacion == "") {
    return(tibble(ciudad = NA_character_, provincia = NA_character_))
  }

  loc <- tolower(trimws(ubicacion))
  # Limpiar sufijos comunes
  loc <- str_remove(loc, ",?\\s*(ecuador|ec|ecu)$")
  loc <- str_remove(loc, ",?\\s*(ec)$")
  loc <- trimws(loc)

  # Separar por coma: "Cayambe, Pichincha" → ["cayambe", "pichincha"]
  partes <- str_split(loc, ",")[[1]] %>% trimws()

  # Intentar cada parte contra el diccionario de cantones
  for (parte in partes) {
    match <- canton_lookup %>% filter(clave == parte)
    if (nrow(match) > 0) {
      return(tibble(
        ciudad    = match$canton[1],
        provincia = match$provincia[1]
      ))
    }
  }

  # Segundo intento: buscar si algún cantón está contenido en el texto
  for (i in seq_len(nrow(canton_lookup))) {
    if (str_detect(loc, fixed(canton_lookup$clave[i]))) {
      return(tibble(
        ciudad    = canton_lookup$canton[i],
        provincia = canton_lookup$provincia[i]
      ))
    }
  }

  # Sin match: devolver la primera parte como ciudad, sin provincia
  tibble(
    ciudad    = str_to_title(partes[1]),
    provincia = if (length(partes) > 1) str_to_title(partes[2]) else NA_character_
  )
}

#' Extraer habilidades hard/soft de texto usando catálogo
#' @param texto String con descripción de la vacante
#' @param catalogo Vector de habilidades a buscar
#' @return String con habilidades separadas por " | "
extraer_habilidades <- function(texto, catalogo) {
  if (is.na(texto) || texto == "") return(NA_character_)
  texto_lower <- tolower(texto)
  encontradas <- catalogo[sapply(catalogo, function(h) str_detect(texto_lower, fixed(h)))]
  if (length(encontradas) == 0) return(NA_character_)
  paste(encontradas, collapse = " | ")
}

#' Extraer años mínimos de experiencia del texto
#' @param texto Descripción en minúsculas
#' @return Numeric o NA
extraer_experiencia <- function(texto) {
  if (is.na(texto) || texto == "") return(NA_real_)
  texto_lower <- tolower(texto)
  # Patrones: "3 años de experiencia", "mínimo 2 años", "experiencia de 5 años"
  match <- str_extract(texto_lower, "(\\d+)\\s*(?:a[ñn]os?|years?)\\s*(?:de\\s*)?(?:experiencia)?")
  if (is.na(match)) {
    match <- str_extract(texto_lower, "(?:experiencia|m[ií]nimo)\\s*(?:de\\s*)?(\\d+)\\s*(?:a[ñn]os?|years?)")
  }
  num <- str_extract(match, "\\d+")
  if (is.na(num)) return(NA_real_)
  as.numeric(num)
}

#' Detectar si requiere maestría/PhD
#' @param texto Descripción
#' @return logical
detectar_maestria <- function(texto) {
  if (is.na(texto) || texto == "") return(FALSE)
  str_detect(
    tolower(texto),
    "maestr[ií]a|m[aá]ster|m\\.?b\\.?a\\.?|phd|ph\\.?\\s?d\\.?|doctorado|posgrado|postgrado|cuarto nivel"
  )
}

#' Normalizar fecha de publicación de diferentes formatos
#' @param fecha_raw String con la fecha
#' @return Date o NA
normalizar_fecha <- function(fecha_raw) {
  if (is.na(fecha_raw) || fecha_raw == "") return(as.Date(NA))

  # ISO datetime: "2026-06-05T00:00:00"
  d <- suppressWarnings(ymd_hms(fecha_raw, quiet = TRUE))
  if (!is.na(d)) return(as_date(d))

  # ISO date: "2026-06-05"
  d <- suppressWarnings(ymd(fecha_raw, quiet = TRUE))
  if (!is.na(d)) return(d)

  # Formato dd-mm-yyyy: "05-06-2026"
  d <- suppressWarnings(dmy(fecha_raw, quiet = TRUE))
  if (!is.na(d)) return(d)

  # Relativos: "Hace 12 horas", "Hace 2 días", "8 dias atras"
  if (str_detect(tolower(fecha_raw), "hace|atr[aá]s|horas?|d[ií]as?")) {
    nums <- as.numeric(str_extract(fecha_raw, "\\d+"))
    if (!is.na(nums)) {
      if (str_detect(tolower(fecha_raw), "hora")) {
        return(Sys.Date())  # Mismo día
      }
      if (str_detect(tolower(fecha_raw), "d[ií]a")) {
        return(Sys.Date() - nums)
      }
      if (str_detect(tolower(fecha_raw), "mes")) {
        return(Sys.Date() - (nums * 30))
      }
    }
  }

  # "Más de 30 días"
  if (str_detect(tolower(fecha_raw), "m[aá]s de 30")) {
    return(Sys.Date() - 30)
  }

  # "Hace un mes"
  if (str_detect(tolower(fecha_raw), "hace un mes")) {
    return(Sys.Date() - 30)
  }

  as.Date(NA)
}

#' Matching de vacante con carreras UNL usando terminos_por_carrera
#' Busca en título + descripción contra los términos de cada carrera
#' @param titulo Título del puesto
#' @param descripcion Descripción de la vacante
#' @param carrera_extraccion Carrera que originó la búsqueda (puede ser NA)
#' @return String con carreras afines separadas por " | "
matching_carreras <- function(titulo, descripcion, carrera_extraccion = NA_character_) {
  texto <- tolower(paste(
    coalesce(titulo, ""),
    coalesce(descripcion, ""),
    sep = " "
  ))

  if (texto == " " || texto == "") {
    # Sin texto para analizar: usar carrera_extraccion si existe
    if (!is.na(carrera_extraccion) && carrera_extraccion != "") {
      return(carrera_extraccion)
    }
    return(NA_character_)
  }

  # terminos_por_carrera viene del catálogo (variable global)
  carreras_match <- c()

  for (carrera in names(terminos_carrera)) {
    terminos <- terminos_carrera[[carrera]]
    # Contar cuántos términos matchean
    hits <- sum(sapply(terminos, function(t) str_detect(texto, fixed(tolower(t)))))
    if (hits > 0) {
      carreras_match <- c(carreras_match, carrera)
    }
  }

  # Siempre incluir la carrera de extracción si existe
  if (!is.na(carrera_extraccion) && carrera_extraccion != "") {
    carreras_match <- unique(c(carrera_extraccion, carreras_match))
  }

  if (length(carreras_match) == 0) return(NA_character_)
  paste(carreras_match, collapse = " | ")
}

#' Generar UUID determinístico a partir de título + empresa + fecha
generar_id_unico <- function(titulo, empresa, fecha) {
  clave <- paste(
    tolower(trimws(titulo %||% "")),
    tolower(trimws(empresa %||% "")),
    as.character(fecha %||% ""),
    sep = "|"
  )
  digest(clave, algo = "md5", serialize = FALSE)
}

# ── 3. Lectores por fuente ───────────────────────────────────────

#' Detectar fuente por nombre de archivo
detectar_fuente <- function(archivo) {
  nombre <- tolower(basename(archivo))
  case_when(
    str_detect(nombre, "^linkedin")         ~ "linkedin",
    str_detect(nombre, "^jobspy")           ~ "jobspy",
    str_detect(nombre, "^computrabajo")     ~ "computrabajo",
    str_detect(nombre, "^multitrabajos")    ~ "multitrabajos",
    str_detect(nombre, "^jooble")           ~ "jooble",
    str_detect(nombre, "^encuentra_empleo") ~ "encuentra_empleo",
    TRUE                                    ~ "desconocida"
  )
}

#' Leer y estandarizar un JSON según su fuente
#' Retorna un tibble con columnas unificadas
leer_y_estandarizar <- function(archivo) {
  fuente <- detectar_fuente(archivo)

  if (fuente == "desconocida") {
    message(sprintf("  SALTANDO archivo desconocido: %s", basename(archivo)))
    return(tibble())
  }

  datos <- tryCatch(
    fromJSON(archivo, flatten = TRUE),
    error = function(e) {
      message(sprintf("  ERROR leyendo %s: %s", basename(archivo), e$message))
      return(NULL)
    }
  )

  if (is.null(datos) || length(datos) == 0) return(tibble())

  df <- as_tibble(datos)
  n <- nrow(df)

  if (n == 0) return(tibble())

  message(sprintf("  [%s] %s: %d registros", fuente, basename(archivo), n))

  # Estandarizar según fuente
  resultado <- switch(fuente,
    "linkedin" = estandarizar_linkedin(df),
    "jobspy" = estandarizar_jobspy(df),
    "computrabajo" = estandarizar_computrabajo(df),
    "multitrabajos" = estandarizar_multitrabajos(df),
    "jooble" = estandarizar_jooble(df),
    "encuentra_empleo" = estandarizar_encuentra_empleo(df),
    tibble()
  )

  resultado$archivo_origen <- basename(archivo)
  resultado
}

# ── Estandarizadores por fuente ──

estandarizar_linkedin <- function(df) {
  # LinkedIn tiene datos IA enriquecidos
  tibble(
    titulo_puesto     = df$title,
    empresa           = df$organization,
    ubicacion_raw     = if ("locations_derived" %in% names(df)) {
      sapply(df$locations_derived, function(x) if (is.null(x) || length(x) == 0) NA_character_ else x[1])
    } else NA_character_,
    fecha_publicacion_raw = df$date_posted,
    fuente            = "LinkedIn",
    url_oferta        = df$url,
    descripcion_raw   = paste0(
      if ("ai_core_responsibilities" %in% names(df)) coalesce(df$ai_core_responsibilities, "") else "",
      " ",
      if ("ai_requirements_summary" %in% names(df)) coalesce(df$ai_requirements_summary, "") else ""
    ),
    salario_min       = if ("ai_salary_min_value" %in% names(df)) as.numeric(df$ai_salary_min_value) else NA_real_,
    salario_max       = if ("ai_salary_max_value" %in% names(df)) as.numeric(df$ai_salary_max_value) else NA_real_,
    modalidad_raw     = if ("ai_work_arrangement" %in% names(df)) df$ai_work_arrangement else NA_character_,
    experiencia_raw   = if ("ai_experience_level" %in% names(df)) df$ai_experience_level else NA_character_,
    habilidades_ia    = if ("ai_key_skills" %in% names(df)) {
      sapply(df$ai_key_skills, function(x) if (is.null(x) || length(x) == 0) NA_character_ else paste(x, collapse = " | "))
    } else NA_character_,
    tipo_empleo       = if ("employment_type" %in% names(df)) {
      sapply(df$employment_type, function(x) if (is.null(x) || length(x) == 0) NA_character_ else paste(x, collapse = ", "))
    } else NA_character_,
    lat               = if ("lats_derived" %in% names(df)) {
      sapply(df$lats_derived, function(x) if (is.null(x) || length(x) == 0) NA_real_ else as.numeric(x[1]))
    } else NA_real_,
    lng               = if ("lngs_derived" %in% names(df)) {
      sapply(df$lngs_derived, function(x) if (is.null(x) || length(x) == 0) NA_real_ else as.numeric(x[1]))
    } else NA_real_,
    carrera_origen    = if ("carrera_origen" %in% names(df)) df$carrera_origen else NA_character_,
    termino_busqueda  = if ("termino_busqueda" %in% names(df)) df$termino_busqueda else NA_character_,
    id_fuente         = as.character(df$id)
  )
}

estandarizar_jobspy <- function(df) {
  tibble(
    titulo_puesto     = df$title,
    empresa           = df$organization,
    ubicacion_raw     = df$location,
    fecha_publicacion_raw = df$date_posted,
    fuente            = paste0("JobSpy (", coalesce(df$source, "indeed"), ")"),
    url_oferta        = df$url,
    descripcion_raw   = df$description_snippet,
    salario_min       = if ("salary_min" %in% names(df)) as.numeric(df$salary_min) else NA_real_,
    salario_max       = if ("salary_max" %in% names(df)) as.numeric(df$salary_max) else NA_real_,
    modalidad_raw     = case_when(
      df$is_remote == TRUE ~ "Remoto",
      TRUE                 ~ NA_character_
    ),
    experiencia_raw   = NA_character_,
    habilidades_ia    = NA_character_,
    tipo_empleo       = if ("job_type" %in% names(df)) df$job_type else NA_character_,
    lat               = NA_real_,
    lng               = NA_real_,
    carrera_origen    = df$carrera_origen,
    termino_busqueda  = df$termino_busqueda,
    id_fuente         = NA_character_
  )
}

estandarizar_computrabajo <- function(df) {
  tibble(
    titulo_puesto     = df$title,
    empresa           = df$organization,
    ubicacion_raw     = df$location,
    fecha_publicacion_raw = df$date_posted,
    fuente            = "CompuTrabajo",
    url_oferta        = df$url,
    descripcion_raw   = df$description_snippet,
    salario_min       = NA_real_,
    salario_max       = NA_real_,
    modalidad_raw     = NA_character_,
    experiencia_raw   = NA_character_,
    habilidades_ia    = NA_character_,
    tipo_empleo       = NA_character_,
    lat               = NA_real_,
    lng               = NA_real_,
    carrera_origen    = df$carrera_origen,
    termino_busqueda  = df$termino_busqueda,
    id_fuente         = NA_character_
  )
}

estandarizar_multitrabajos <- function(df) {
  tibble(
    titulo_puesto     = df$title,
    empresa           = df$organization,
    ubicacion_raw     = df$location,
    fecha_publicacion_raw = df$date_posted,
    fuente            = "Multitrabajos",
    url_oferta        = df$url,
    descripcion_raw   = df$description_snippet,
    salario_min       = NA_real_,
    salario_max       = NA_real_,
    modalidad_raw     = if ("modalidad" %in% names(df)) df$modalidad else NA_character_,
    experiencia_raw   = NA_character_,
    habilidades_ia    = NA_character_,
    tipo_empleo       = if ("job_type" %in% names(df)) df$job_type else NA_character_,
    lat               = NA_real_,
    lng               = NA_real_,
    carrera_origen    = df$carrera_origen,
    termino_busqueda  = df$termino_busqueda,
    id_fuente         = as.character(df$id)
  )
}

estandarizar_jooble <- function(df) {
  tibble(
    titulo_puesto     = df$title,
    empresa           = df$organization,
    ubicacion_raw     = df$location,
    fecha_publicacion_raw = df$date_posted,
    fuente            = "Jooble",
    url_oferta        = df$url,
    descripcion_raw   = df$description_snippet,
    salario_min       = NA_real_,
    salario_max       = NA_real_,
    modalidad_raw     = case_when(
      df$is_remote == TRUE ~ "Remoto",
      TRUE                 ~ NA_character_
    ),
    experiencia_raw   = NA_character_,
    habilidades_ia    = NA_character_,
    tipo_empleo       = if ("job_type" %in% names(df)) df$job_type else NA_character_,
    lat               = NA_real_,
    lng               = NA_real_,
    carrera_origen    = df$carrera_origen,
    termino_busqueda  = df$termino_busqueda,
    id_fuente         = as.character(df$id)
  )
}

estandarizar_encuentra_empleo <- function(df) {
  # Sector público: tiene salario (RMU) y código de puesto
  # No tiene carrera_origen (no busca por términos)
  rmu <- suppressWarnings(as.numeric(df$salary))

  tibble(
    titulo_puesto     = df$title,
    empresa           = df$organization,
    ubicacion_raw     = df$location,
    fecha_publicacion_raw = df$date_posted,
    fuente            = "EncuentraEmpleo",
    url_oferta        = df$url,
    descripcion_raw   = NA_character_,  # No disponible en este portal
    salario_min       = rmu,
    salario_max       = rmu,  # RMU es salario fijo
    modalidad_raw     = "Presencial",  # Sector público = presencial por defecto
    experiencia_raw   = NA_character_,
    habilidades_ia    = NA_character_,
    tipo_empleo       = "Contrato público",
    lat               = NA_real_,
    lng               = NA_real_,
    carrera_origen    = if ("carrera_origen" %in% names(df)) df$carrera_origen else NA_character_,
    termino_busqueda  = if ("termino_busqueda" %in% names(df)) df$termino_busqueda else NA_character_,
    id_fuente         = as.character(df$codigo_puesto)
  )
}

# ── 4. Leer todos los archivos y unificar ────────────────────────

message("\n========================================")
message("  PROCESAMIENTO MULTI-FUENTE v2.0")
message("========================================\n")

archivos_json <- list.files(raw_dir, pattern = "\\.json$", full.names = TRUE)
message(sprintf("Encontrados %d archivos JSON en data/raw/\n", length(archivos_json)))

if (length(archivos_json) == 0) {
  stop("No se encontraron archivos JSON en data/raw/")
}

# Solo usar el batch más reciente de cada fuente
# (para evitar duplicados entre ejecuciones de test)
archivos_por_fuente <- tibble(
  archivo = archivos_json,
  fuente  = sapply(archivos_json, detectar_fuente),
  mtime   = file.mtime(archivos_json)
) %>%
  filter(fuente != "desconocida") %>%
  group_by(fuente) %>%
  slice_max(mtime, n = 1) %>%  # Solo el más reciente por fuente
  ungroup()

message(sprintf("Usando %d archivos (más reciente por fuente):", nrow(archivos_por_fuente)))
walk(archivos_por_fuente$archivo, ~message(sprintf("  • %s", basename(.x))))
message("")

df_unificado <- map_dfr(archivos_por_fuente$archivo, leer_y_estandarizar)

message(sprintf("\nTotal unificado: %d registros de %d fuentes\n",
                nrow(df_unificado), n_distinct(df_unificado$fuente)))

# ── 5. Enriquecimiento ──────────────────────────────────────────

message("Enriqueciendo datos...")

df_procesado <- df_unificado %>%
  # 5a. Normalizar ubicación → ciudad + provincia
  mutate(
    ubicacion_parsed = map(ubicacion_raw, normalizar_ubicacion)
  ) %>%
  unnest(ubicacion_parsed) %>%
  rename(
    ubicacion_ciudad = ciudad,
    # provincia ya se llama provincia
  ) %>%

  # 5b. Normalizar fecha
  mutate(
    fecha_publicacion = map_dbl(fecha_publicacion_raw, ~as.numeric(normalizar_fecha(.x))) %>%
      as.Date(origin = "1970-01-01"),
    fecha_extraccion  = Sys.Date()
  ) %>%

  # 5c. Normalizar modalidad
  mutate(
    modalidad = case_when(
      str_detect(tolower(coalesce(modalidad_raw, "")), "remoto|remote|teletrabajo") ~ "Remoto",
      str_detect(tolower(coalesce(modalidad_raw, "")), "h[ií]brido|hybrid")          ~ "Híbrido",
      str_detect(tolower(coalesce(modalidad_raw, "")), "presencial|on.?site|oficina") ~ "Presencial",
      TRUE ~ NA_character_
    )
  ) %>%

  # 5d. Extraer habilidades de la descripción (para fuentes sin IA)
  mutate(
    habilidades_hard = case_when(
      # LinkedIn ya tiene habilidades IA — usarlas como base
      !is.na(habilidades_ia) ~ habilidades_ia,
      # Para las demás fuentes, extraer del texto
      TRUE ~ map_chr(descripcion_raw, ~extraer_habilidades(.x, habilidades_hard))
    ),
    habilidades_soft = map_chr(descripcion_raw, ~extraer_habilidades(.x, habilidades_soft))
  ) %>%

  # 5e. Extraer experiencia mínima
  mutate(
    experiencia_min = case_when(
      # LinkedIn: experiencia_raw viene como "5-10" o "2-5" — extraer mínimo
      !is.na(experiencia_raw) & str_detect(experiencia_raw, "\\d") ~
        as.numeric(str_extract(experiencia_raw, "^\\d+")),
      # Para las demás: extraer del texto
      TRUE ~ map_dbl(descripcion_raw, extraer_experiencia)
    )
  ) %>%

  # 5f. Detectar si requiere maestría
  mutate(
    requiere_maestria = map_lgl(descripcion_raw, detectar_maestria)
  ) %>%

  # 5g. Generar id_unico (hash de título + empresa + fecha)
  mutate(
    id_unico = pmap_chr(
      list(titulo_puesto, empresa, fecha_publicacion),
      generar_id_unico
    )
  ) %>%

  # 5h. Moneda siempre USD para Ecuador
  mutate(moneda = "USD") %>%

  # 5i. Matching carreras UNL ↔ vacantes
  # Busca en título + descripción contra los 40 catálogos de términos
  # Genera carreras_afines (puede tener múltiples) y complementa carrera_origen
  mutate(
    carreras_afines = pmap_chr(
      list(titulo_puesto, descripcion_raw, carrera_origen),
      matching_carreras
    )
  )

message("  ✓ Ubicación, fecha, modalidad, habilidades, experiencia, maestría, carreras")

# ── 6. Seleccionar y ordenar columnas (schema del cliente) ──────

df_final <- df_procesado %>%
  select(
    id_unico,
    fecha_extraccion,
    fecha_publicacion,
    fuente,
    titulo_puesto,
    empresa,
    ubicacion_ciudad,
    provincia,
    modalidad,
    habilidades_hard,
    habilidades_soft,
    salario_min,
    salario_max,
    moneda,
    experiencia_min,
    requiere_maestria,
    descripcion_raw,
    url_oferta,
    carrera_origen,
    carreras_afines,
    termino_busqueda,
    # Extras útiles para análisis
    lat,
    lng,
    tipo_empleo,
    id_fuente,
    archivo_origen
  )

# ── 7. Deduplicación ────────────────────────────────────────────

message("\n--- Deduplicación ---")
n_inicial <- nrow(df_final)

# Nivel 1: ID de fuente exacto (misma fuente, mismo ID)
df_final <- df_final %>%
  distinct(id_unico, .keep_all = TRUE)
n_dedup1 <- nrow(df_final)

# Nivel 2: Título + Empresa normalizado (cross-source)
df_final <- df_final %>%
  mutate(
    clave_dedup = paste(
      str_to_lower(str_replace_all(coalesce(titulo_puesto, ""), "[^a-záéíóúñ0-9\\s]", "")),
      str_to_lower(str_replace_all(coalesce(empresa, ""), "[^a-záéíóúñ0-9\\s]", ""))
    ) %>% str_squish()
  ) %>%
  # Priorizar: LinkedIn > Multitrabajos > JobSpy > Jooble > CompuTrabajo > EncuentraEmpleo
  arrange(factor(fuente, levels = c(
    "LinkedIn", "Multitrabajos", "Jooble",
    "CompuTrabajo", "EncuentraEmpleo",
    "JobSpy (indeed)", "JobSpy (google)"
  ))) %>%
  distinct(clave_dedup, .keep_all = TRUE) %>%
  select(-clave_dedup)

n_final <- nrow(df_final)

message(sprintf("  Registros iniciales:        %d", n_inicial))
message(sprintf("  Nivel 1 (hash exacto):      -%d → %d", n_inicial - n_dedup1, n_dedup1))
message(sprintf("  Nivel 2 (título+empresa):   -%d → %d", n_dedup1 - n_final, n_final))
message(sprintf("  Registros únicos finales:   %d", n_final))

# ── 8. Resumen por fuente ────────────────────────────────────────

message("\n--- Resumen por fuente ---")
resumen <- df_final %>%
  group_by(fuente) %>%
  summarise(
    n             = n(),
    con_salario   = sum(!is.na(salario_min) & salario_min > 0, na.rm = TRUE),
    con_habilidad = sum(!is.na(habilidades_hard), na.rm = TRUE),
    con_ciudad    = sum(!is.na(ubicacion_ciudad), na.rm = TRUE),
    con_modalidad = sum(!is.na(modalidad), na.rm = TRUE),
    .groups       = "drop"
  )

print(resumen)

# ── 9. Guardar resultados ────────────────────────────────────────

saveRDS(df_final, file.path(out_dir, "df_vacantes_limpio.rds"))
write_csv(df_final, file.path(out_dir, "df_vacantes_limpio.csv"))

message(sprintf("\n✓ Guardado en data/processed/"))
message(sprintf("  • df_vacantes_limpio.rds (%d filas × %d columnas)", nrow(df_final), ncol(df_final)))
message(sprintf("  • df_vacantes_limpio.csv"))

# Resumen de carreras afines (matching NLP)
message("\n--- Top 15 carreras UNL con más vacantes afines ---")
# Explotar carreras_afines (separadas por " | ") para contar individualmente
df_final %>%
  filter(!is.na(carreras_afines)) %>%
  separate_rows(carreras_afines, sep = "\\s*\\|\\s*") %>%
  count(carreras_afines, sort = TRUE) %>%
  head(15) %>%
  print()

# Cobertura del matching
n_con_carrera <- sum(!is.na(df_final$carreras_afines))
message(sprintf("\nCobertura de matching: %d/%d vacantes (%.0f%%)",
                n_con_carrera, nrow(df_final), 100 * n_con_carrera / nrow(df_final)))

# Vacantes con múltiples carreras afines
n_multi <- sum(str_detect(coalesce(df_final$carreras_afines, ""), "\\|"), na.rm = TRUE)
message(sprintf("Vacantes multi-carrera: %d (%.0f%%)", n_multi, 100 * n_multi / nrow(df_final)))

message("\n=== ESTRUCTURA DEL DATAFRAME FINAL ===")
glimpse(df_final)
