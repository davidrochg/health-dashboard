#!/usr/bin/env python3
"""
Lee el Excel de peso y genera data/peso.json para el dashboard de salud.

Estructura de la hoja (una sola hoja, meses en BLOQUES de 3 columnas a la derecha):
- Fila 1: nombre del mes en la primera columna del bloque (celda combinada),
  p. ej. A1="Agosto" (bloque A-C), D1="Septiembre" (bloque D-F), etc.
- Fila 2: cabeceras del bloque (Día, Peso, Eat).
- Fila 3 en adelante: datos. Día = 1..31, Peso puede estar vacío (hueco).
- La fila de la media del mes (número suelto sin día) se ignora (no tiene día).

El lector une TODOS los bloques en una única serie temporal continua, de modo que
"ayer", "hace 7 días" y la media semanal funcionan aunque la semana cruce el cambio
de mes. Las stats y la gráfica ("series") muestran el MES EN CURSO (el del último
registro). El JSON de salida no cambia de forma.
"""

import json
import sys
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path

import openpyxl

EXCEL_PATH = (
    "/Users/davidrochgarcia/Library/CloudStorage/"
    "GoogleDrive-davidrochgarcia@gmail.com/My Drive/1. dOS/Salud/Peso.xlsx"
)
OUTPUT_PATH = "data/peso.json"

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


def _sin_acentos(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in t if not unicodedata.combining(c)).strip().lower()


def escanear_bloques(ws):
    """Detecta los bloques de mes por su cabecera en la fila 1.
    Devuelve [{mes_num, mes_txt, col_dia, col_peso, col_eat}] en orden de columna."""
    bloques = []
    for c in range(1, ws.max_column + 1):
        v = ws.cell(row=1, column=c).value
        if not v:
            continue
        mn = MESES.get(_sin_acentos(str(v)).split()[0]) if str(v).strip() else None
        if mn:
            bloques.append({
                "mes_num": mn, "mes_txt": str(v).strip(),
                "col_dia": c, "col_peso": c + 1, "col_eat": c + 2,
            })
    return bloques


def leer_peso(excel_path: str) -> dict:
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb.worksheets[0]
    anio = datetime.now().year

    bloques = escanear_bloques(ws)
    # Compatibilidad: si no se detecta ningún bloque, asumimos el clásico A/B con mes en A1.
    if not bloques:
        titulo = ws.cell(row=1, column=1).value
        mn = MESES.get(_sin_acentos(str(titulo)).split()[0]) if titulo else None
        bloques = [{"mes_num": mn, "mes_txt": str(titulo).strip() if titulo else "",
                    "col_dia": 1, "col_peso": 2, "col_eat": 3}]

    registros = []
    meses = {}
    for b in bloques:
        if b["mes_num"]:
            meses[b["mes_num"]] = b["mes_txt"]
        for r in range(3, ws.max_row + 1):
            dia = ws.cell(row=r, column=b["col_dia"]).value
            peso = ws.cell(row=r, column=b["col_peso"]).value
            if not isinstance(dia, (int, float)):
                continue
            dia = int(dia)
            if dia < 1 or dia > 31:
                continue
            if not isinstance(peso, (int, float)):
                continue
            fecha = f"{anio:04d}-{b['mes_num']:02d}-{dia:02d}" if b["mes_num"] else None
            registros.append({"date": fecha, "day": dia, "weight": round(float(peso), 1)})

    # Orden cronológico real (por fecha) para tratar los meses como una línea continua.
    registros.sort(key=lambda r: (r["date"] or ""))
    return {"registros": registros, "meses": meses, "anio": anio}


def dias_entre(fecha_a: str, fecha_b: str) -> int:
    a = datetime.strptime(fecha_a, "%Y-%m-%d")
    b = datetime.strptime(fecha_b, "%Y-%m-%d")
    return abs((a - b).days)


def construir_json(datos: dict) -> dict:
    regs = datos["registros"]          # serie CONTINUA (todos los meses), ordenada por fecha
    if not regs:
        ultimo_mes = max(datos["meses"]) if datos["meses"] else None
        etiqueta = f'{datos["meses"].get(ultimo_mes, "")} {datos["anio"]}'.strip()
        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "unit": "kg",
            "month": etiqueta,
            "current": None,
            "series": [],
            "note": "Sin registros de peso.",
        }

    current = regs[-1]
    previous = regs[-2] if len(regs) >= 2 else None
    delta_prev = round(current["weight"] - previous["weight"], 1) if previous else None

    # Variación vs exactamente 7 días antes (serie continua, cruza meses).
    delta_week = None
    ref_week = None
    if current["date"]:
        for r in regs[:-1]:
            if r["date"] and dias_entre(current["date"], r["date"]) == 7:
                ref_week = r
                delta_week = round(current["weight"] - r["weight"], 1)
                break

    # Medias por semana natural (lunes-domingo) sobre la serie continua.
    def media_rango(desde, hasta):
        vals = []
        for r in regs:
            if not r["date"]:
                continue
            dt = datetime.strptime(r["date"], "%Y-%m-%d")
            if desde <= dt <= hasta:
                vals.append(r["weight"])
        if not vals:
            return {"avg": None, "count": 0, "_sum": 0.0}
        return {"avg": round(sum(vals) / len(vals), 2), "count": len(vals), "_sum": sum(vals)}

    week = None
    if current["date"]:
        cur_dt = datetime.strptime(current["date"], "%Y-%m-%d")
        this_start = cur_dt - timedelta(days=cur_dt.weekday())
        last_start = this_start - timedelta(days=7)
        last_end = this_start - timedelta(days=1)
        this_w = media_rango(this_start, cur_dt)
        last_w = media_rango(last_start, last_end)
        delta_w = None
        if this_w["avg"] is not None and last_w["avg"] is not None:
            delta_w = round(this_w["_sum"] / this_w["count"] - last_w["_sum"] / last_w["count"], 2)
        for w in (this_w, last_w):
            w.pop("_sum", None)
        week = {
            "this": this_w, "last": last_w, "delta": delta_w,
            "this_start": this_start.strftime("%Y-%m-%d"),
            "last_start": last_start.strftime("%Y-%m-%d"),
            "last_end": last_end.strftime("%Y-%m-%d"),
        }

    # Stats y gráfica = MES EN CURSO (el del último registro).
    cur_dt = datetime.strptime(current["date"], "%Y-%m-%d") if current["date"] else None
    if cur_dt:
        mes_regs = [r for r in regs if r["date"]
                    and datetime.strptime(r["date"], "%Y-%m-%d").month == cur_dt.month
                    and datetime.strptime(r["date"], "%Y-%m-%d").year == cur_dt.year]
        mes_txt = datos["meses"].get(cur_dt.month, "")
        month_label = f"{mes_txt} {cur_dt.year}".strip()
    else:
        mes_regs = regs
        month_label = f'{datos["anio"]}'.strip()

    pesos = [r["weight"] for r in mes_regs]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "unit": "kg",
        "month": month_label,
        "current": current,
        "previous": previous,
        "delta_vs_previous": delta_prev,
        "delta_vs_week": delta_week,
        "reference_week": ref_week,
        "week": week,
        "stats": {
            "count": len(mes_regs),
            "min": min(pesos), "max": max(pesos),
            "avg": round(sum(pesos) / len(pesos), 1),
        },
        "series": mes_regs,
    }


def main():
    excel_path = sys.argv[1] if len(sys.argv) > 1 else EXCEL_PATH
    out_path = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_PATH

    datos = leer_peso(excel_path)
    resultado = construir_json(datos)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    c = resultado.get("current")
    if c:
        print(f"Mes: {resultado['month']}")
        print(f"Registros del mes: {resultado['stats']['count']}")
        print(f"Peso actual: {c['weight']} kg (día {c['day']}, {c['date']})")
        print(f"Variación vs día anterior: {resultado['delta_vs_previous']} "
              f"(anterior: {resultado['previous']['date'] if resultado['previous'] else None})")
        print(f"Variación vs ~semana: {resultado['delta_vs_week']}")
        if resultado.get("week"):
            print(f"Media semanal: esta {resultado['week']['this']['avg']} · "
                  f"pasada {resultado['week']['last']['avg']} · delta {resultado['week']['delta']}")
        print(f"Media/min/max mes: {resultado['stats']['avg']} / "
              f"{resultado['stats']['min']} / {resultado['stats']['max']}")
    else:
        print("Sin registros.")
    print(f"Escrito: {out_path}")


if __name__ == "__main__":
    main()
