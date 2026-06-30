"""
analizar_campos.py
Analiza la tasa de llenado real de cada campo en los datos extraídos.
Lee TODOS los batches de data/raw/ y genera un reporte por fuente.

Para cada campo reporta:
  - Registros con valor (no vacío/null)
  - Tasa de llenado (%)
  - Ejemplo de valor real

Genera: documents/reporte_campos_reales.md

Uso:
    python script/analizar_campos.py
"""

import os
import sys
import json
import glob
from collections import defaultdict
from datetime import datetime


def es_valor_presente(valor):
    """Determina si un valor contiene datos reales (no vacío/null)."""
    if valor is None:
        return False
    if isinstance(valor, bool):
        return True  # True/False son valores válidos
    if isinstance(valor, float):
        import math
        return not math.isnan(valor)
    if isinstance(valor, int):
        return True
    if isinstance(valor, str):
        return valor.strip() != "" and valor.strip().lower() not in ("nan", "none", "null", "")
    if isinstance(valor, list):
        # Lista con al menos un elemento no vacío
        return len(valor) > 0 and any(v is not None and str(v).strip() not in ("", "nan") for v in valor)
    if isinstance(valor, dict):
        return len(valor) > 0
    return bool(valor)


def ejemplo_valor(valor, max_chars=80):
    """Genera un ejemplo legible del valor, truncado."""
    if valor is None:
        return "—"
    if isinstance(valor, list):
        if len(valor) == 0:
            return "[]"
        muestra = str(valor[0])
        if len(muestra) > max_chars:
            muestra = muestra[:max_chars] + "..."
        extras = f" (+{len(valor)-1} más)" if len(valor) > 1 else ""
        return f'["{muestra}"{extras}]'
    if isinstance(valor, dict):
        keys = list(valor.keys())[:3]
        return "{" + ", ".join(keys) + "...}"
    s = str(valor)
    if len(s) > max_chars:
        s = s[:max_chars] + "..."
    return s


def analizar_fuente(registros, nombre_fuente):
    """Analiza todos los campos de una lista de registros."""
    if not registros:
        return {}

    # Recopilar todos los campos posibles
    todos_campos = set()
    for reg in registros:
        todos_campos.update(reg.keys())

    total = len(registros)
    resultado = {}

    for campo in sorted(todos_campos):
        valores_presentes = 0
        ejemplo = None

        for reg in registros:
            val = reg.get(campo)
            if es_valor_presente(val):
                valores_presentes += 1
                if ejemplo is None:
                    ejemplo = val

        resultado[campo] = {
            "presentes": valores_presentes,
            "total": total,
            "tasa": round(valores_presentes / total * 100, 1),
            "ejemplo": ejemplo_valor(ejemplo),
        }

    return resultado


def cargar_batches(data_dir, prefijo, solo_ultimo=True):
    """Carga batches de una fuente. Si solo_ultimo=True, solo el más reciente."""
    patron = os.path.join(data_dir, f"{prefijo}_batch_*.json")
    archivos = sorted(glob.glob(patron))

    if not archivos:
        return [], []

    if solo_ultimo:
        archivos = [archivos[-1]]  # Solo el más reciente (sorted por timestamp)

    todos = []
    for archivo in archivos:
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    todos.extend(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"  ⚠ Error leyendo {archivo}: {e}")

    return todos, archivos


def generar_tabla_md(analisis, nombre):
    """Genera tabla markdown para una fuente."""
    lineas = []
    lineas.append(f"### {nombre}")
    lineas.append("")

    total_reg = 0
    if analisis:
        total_reg = list(analisis.values())[0]["total"]

    lineas.append(f"**Total registros analizados: {total_reg}**")
    lineas.append("")
    lineas.append("| Campo | Llenado | Tasa | Ejemplo |")
    lineas.append("|-------|---------|------|---------|")

    # Ordenar: primero los que tienen datos, luego los vacíos
    items = sorted(analisis.items(), key=lambda x: (-x[1]["tasa"], x[0]))

    for campo, info in items:
        tasa_str = f'{info["tasa"]}%'
        llenado = f'{info["presentes"]}/{info["total"]}'

        # Emoji de estado
        if info["tasa"] == 100:
            estado = "✅"
        elif info["tasa"] >= 50:
            estado = "🟡"
        elif info["tasa"] > 0:
            estado = "🟠"
        else:
            estado = "❌"

        # Escapar pipes en el ejemplo
        ej = info["ejemplo"].replace("|", "\\|")

        lineas.append(f"| {estado} `{campo}` | {llenado} | {tasa_str} | {ej} |")

    lineas.append("")
    return "\n".join(lineas)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(project_dir, "data", "raw")
    doc_dir = os.path.join(project_dir, "documents")

    fuentes = {
        "linkedin": "LinkedIn (API Fantastic Jobs)",
        "jobspy": "JobSpy (Indeed + Google Jobs)",
        "jobspy_linkedin": "JobSpy LinkedIn (scraping gratuito)",
        "computrabajo": "CompuTrabajo",
        "multitrabajos": "Multitrabajos",
        "jooble": "Jooble",
        "coresignal": "Coresignal (API alternativa LinkedIn)",
        "encuentra_empleo": "Encuentra Empleo",
    }

    solo_ultimo = "--all" not in sys.argv

    print("=" * 70)
    print("ANÁLISIS DE TASA DE LLENADO DE CAMPOS")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Modo: {'Solo último batch por fuente' if solo_ultimo else 'Todos los batches'}")
    print("  (usa --all para analizar todos los batches)")
    print("=" * 70)

    reporte = []
    reporte.append("# Reporte de Campos Reales por Fuente")
    reporte.append("")
    reporte.append(f"> Generado automáticamente: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    reporte.append("> Datos de: `data/raw/`")
    reporte.append("> ✅ = 100% | 🟡 = 50-99% | 🟠 = 1-49% | ❌ = 0%")
    reporte.append("")
    reporte.append("---")
    reporte.append("")

    # Resumen
    resumen_lineas = []
    resumen_lineas.append("## Resumen")
    resumen_lineas.append("")
    resumen_lineas.append("| Fuente | Registros | Campos totales | Campos con datos (>0%) | Campos 100% |")
    resumen_lineas.append("|--------|-----------|----------------|------------------------|-------------|")

    detalles = []

    for prefijo, nombre in fuentes.items():
        print(f"\n--- {nombre} ---")
        registros, archivos = cargar_batches(data_dir, prefijo, solo_ultimo=solo_ultimo)

        if not registros:
            print(f"  Sin datos")
            resumen_lineas.append(f"| {nombre} | 0 | — | — | — |")
            continue

        print(f"  {len(registros)} registros de {len(archivos)} batch(es)")

        # Deduplicar — lógica por fuente
        if prefijo == "encuentra_empleo":
            # EE usa URL única de portal JSF, dedup por codigo_puesto
            dedupe_key = "codigo_puesto"
        elif registros[0].get("id") and prefijo != "jooble":
            dedupe_key = "id"
        elif registros[0].get("url"):
            dedupe_key = "url"
        else:
            dedupe_key = None

        if dedupe_key:
            seen = set()
            unicos = []
            for r in registros:
                k = str(r.get(dedupe_key, ""))
                if k and k not in seen:
                    seen.add(k)
                    unicos.append(r)
            print(f"  {len(unicos)} únicos (dedup por '{dedupe_key}')")
            registros = unicos

        analisis = analizar_fuente(registros, nombre)

        total_campos = len(analisis)
        campos_con_datos = sum(1 for v in analisis.values() if v["tasa"] > 0)
        campos_100 = sum(1 for v in analisis.values() if v["tasa"] == 100)

        resumen_lineas.append(
            f"| {nombre} | {len(registros)} | {total_campos} | {campos_con_datos} | {campos_100} |"
        )

        # Imprimir en consola
        for campo, info in sorted(analisis.items(), key=lambda x: (-x[1]["tasa"], x[0])):
            estado = "✅" if info["tasa"] == 100 else "🟡" if info["tasa"] >= 50 else "🟠" if info["tasa"] > 0 else "❌"
            print(f"  {estado} {campo}: {info['presentes']}/{info['total']} ({info['tasa']}%) — {info['ejemplo'][:50]}")

        detalles.append(generar_tabla_md(analisis, nombre))

    # Construir reporte final
    reporte.extend(resumen_lineas)
    reporte.append("")
    reporte.append("---")
    reporte.append("")
    reporte.append("## Detalle por fuente")
    reporte.append("")

    for detalle in detalles:
        reporte.append(detalle)
        reporte.append("---")
        reporte.append("")

    # Guardar
    output_path = os.path.join(doc_dir, "reporte_campos_reales.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(reporte))

    print(f"\n{'='*70}")
    print(f"Reporte guardado: {output_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
