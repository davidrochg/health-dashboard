#!/usr/bin/env python3
"""
Lee la columna "Eat" del Excel de peso y genera data/dieta.json.

Métrica: días que cumplo el plan de alimentación en la semana natural en curso.
- En la hoja de peso, col A = día del mes, col C = "Eat": "X" = cumplí, "-" = no.
- OJO (a diferencia de peso/deporte): la dieta solo se sabe al FINAL del día, así
  que el denominador son los días YA CERRADOS de la semana (lunes → ayer). "Hoy"
  no cuenta hasta que termina.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import openpyxl

EXCEL_PATH = (
    "/Users/davidrochgarcia/Library/CloudStorage/"
    "GoogleDrive-davidrochgarcia@gmail.com/My Drive/1. dOS/Salud/Peso.xlsx"
)
OUTPUT_PATH = "data/dieta.json"

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}


def cumple(v):
    return v is not None and str(v).strip().upper() == "X"


def leer_eat(ws):
    """Mapa {día_del_mes: valor Eat} y número de mes de la hoja."""
    titulo = str(ws.cell(1, 1).value or "").strip().lower()
    mes_num = MESES.get(titulo.split()[0]) if titulo else None
    data = {}
    for r in range(3, 40):
        d = ws.cell(r, 1).value
        e = ws.cell(r, 3).value
        if isinstance(d, (int, float)):
            data[int(d)] = e
    return data, mes_num


def main():
    excel = sys.argv[1] if len(sys.argv) > 1 else EXCEL_PATH
    out = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_PATH
    hoy = datetime.now()

    wb = openpyxl.load_workbook(excel, data_only=True)
    ws = wb.worksheets[0]
    data, mes_num = leer_eat(ws)
    anio = hoy.year

    lunes = hoy - timedelta(days=hoy.weekday())
    cerrados = hoy.weekday()  # nº de días ya terminados esta semana (lun..ayer); 0 el lunes

    def eat_de(dia_dt):
        # solo si el día pertenece al mes/año de la hoja (evita colisión al cruzar mes)
        if mes_num and (dia_dt.month != mes_num or dia_dt.year != anio):
            return None
        return data.get(dia_dt.day)

    pattern = []
    cumplidos = 0
    for i in range(7):
        dia_dt = (lunes + timedelta(days=i))
        if i < cerrados:          # día cerrado (antes de hoy)
            if cumple(eat_de(dia_dt)):
                pattern.append("ok")
                cumplidos += 1
            else:
                pattern.append("fail")
        elif i == cerrados:       # hoy (en curso)
            pattern.append("today")
        else:                     # futuro
            pattern.append("future")

    # Semana pasada completa (lun-dom), como referencia (útil los lunes).
    last_start = lunes - timedelta(days=7)
    last_cumplidos = 0
    for i in range(7):
        dia_dt = last_start + timedelta(days=i)
        if cumple(eat_de(dia_dt)):
            last_cumplidos += 1

    res = {
        "generated_at": hoy.isoformat(timespec="seconds"),
        "week_start": lunes.date().isoformat(),
        "dias_cumplidos": cumplidos,
        "dias_cerrados": cerrados,        # denominador (hasta ayer)
        "total_semana": 7,
        "pattern": pattern,               # 7 estados: ok | fail | today | future
        "last_week": {"cumplidos": last_cumplidos, "total": 7},
    }

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    print(f"Semana del {lunes.date()} · días cerrados: {cerrados}")
    print(f"Dieta: {cumplidos} de {cerrados}  (semana pasada: {last_cumplidos}/7)")
    print(f"Patrón: {pattern}")
    print(f"Escrito: {out}")


if __name__ == "__main__":
    main()
