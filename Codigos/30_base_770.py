# Construcción de la base analítica individual de vigilancia de dengue en Juanjuí.
import argparse
import json
import sys
from pathlib import Path as FilePath
import numpy as np, pandas as pd
from matplotlib.path import Path
sys.stdout.reconfigure(encoding="utf-8")

parser = argparse.ArgumentParser(description="Prepare the individual analysis dataset from the authorized workbook.")
parser.add_argument("workbook", type=FilePath)
parser.add_argument("output", type=FilePath)
parser.add_argument("--boundaries", type=FilePath,
                    default=FilePath(__file__).resolve().parents[1] / "Datos" / "sectores_juanjui.geojson")
args = parser.parse_args()
XL, OUT = args.workbook, args.output
VENTANA = 7

d = pd.read_excel(XL, sheet_name="FORMATO 10 - INVESTIGACIÓN", header=None).iloc[5:].reset_index(drop=True)
d = d[d[1].notna()].reset_index(drop=True)

def coord(v, escala=1e6):
    x = pd.to_numeric(v, errors="coerce")
    return np.where(x.abs() > 1000, x / escala, x)

B = pd.DataFrame({
    "n":              d[1].astype(int),
    "edad":           pd.to_numeric(d[3], errors="coerce"),
    "sexo":           d[4].astype(str).str.strip().str.upper(),
    "ocupacion_raw":  d[5].astype(str).str.strip().str.upper(),
    "denguepositivo": d[6].astype(int),
    "vivienda":       d[7].astype(str).str.strip().str.upper(),
    "fecha_invest":   pd.to_datetime(d[8]),
    "fecha_interv":   pd.to_datetime(d[47], errors="coerce"),
    "mz":             pd.to_numeric(d[11], errors="coerce").fillna(0).astype(int),
    "lat":            coord(d[13]),
    "lon":            coord(d[14]),
    "recinsp":        pd.to_numeric(d[16], errors="coerce").fillna(0).astype(int),
    "recpos":         pd.to_numeric(d[17], errors="coerce").fillna(0).astype(int),
})
# mismas correcciones que la preparacion v4
B.loc[~B.sexo.isin(["M", "F"]), "sexo"] = np.nan
inv = B.fecha_interv < B.fecha_invest                      # 4 fechas invertidas (NOTA 2)
B.loc[inv, ["fecha_invest", "fecha_interv"]] = B.loc[inv, ["fecha_interv", "fecha_invest"]].values
_mapa = {"ESTUDIANTE": "Estudiante", "AMA DE CASA": "Ama de casa"}
B["ocupacion"] = B.ocupacion_raw.map(_mapa)
B.loc[B.ocupacion.isna() & ~B.ocupacion_raw.isin(["0", "NAN", ""]), "ocupacion"] = "Otra"

# tiempo calendario
B["mes"] = B.fecha_invest.dt.month
B["semana_epi"] = B.fecha_invest.apply(lambda f: int(f.strftime("%U")) + (0 if pd.Timestamp(f.year, 1, 1).weekday() == 6 else 1))
B["retraso"] = (B.fecha_interv - B.fecha_invest).dt.days

# ------------------------------------------------ sector por coordenadas (punto en poligono)
with args.boundaries.open(encoding="utf-8") as stream:
    features = json.load(stream)["features"]
pol = {
    feature["properties"]["sector"]: Path(feature["geometry"]["coordinates"][0])
    for feature in features
}
ok = np.isfinite(B.lat) & np.isfinite(B.lon) & B.lat.between(-7.3, -7.0) & B.lon.between(-76.9, -76.6)
B["sector_gps"] = None
for nm, p in pol.items():
    dentro = ok & p.contains_points(np.c_[B.lon, B.lat])
    B.loc[dentro & B.sector_gps.isna(), "sector_gps"] = nm

# sector oficial de la hoja LOGISTICO para quienes tienen manzana
L = pd.read_excel(XL, sheet_name="LOGISTICO")[["n", "sector"]]
B = B.merge(L, on="n", how="left").rename(columns={"sector": "sector_mz"})
B["sector_mz"] = B.sector_mz.str.upper().str.replace("Í", "I")
B["sector"] = B.sector_mz.fillna(B.sector_gps)
con = B.sector_mz.notna() & B.sector_gps.notna()
print("Concordancia sector por manzana vs por GPS: %d/%d (%.1f%%)"
      % ((B.sector_mz == B.sector_gps)[con].sum(), con.sum(), (B.sector_mz == B.sector_gps)[con].mean() * 100))

# ------------------------------------------------ elegibilidad y motivo de exclusion
B["inspeccionada"] = (B.recinsp > 0).astype(int)
B["aedes_vivienda"] = (B.recpos > 0).astype(int)
B["ir"] = np.where(B.recinsp > 0, B.recpos / B.recinsp.replace(0, np.nan), np.nan)
B["elegible_tiempo"] = B.retraso.between(0, VENTANA)

# La inspeccion se define por el dato (recipientes inspeccionados > 0), no por la etiqueta
# de estado: tres viviendas marcadas C o N tienen recipientes registrados.
def motivo(r):
    if r.inspeccionada == 1:
        return "0 Incluido" if r.elegible_tiempo else "5 Intervencion fuera de 7 dias"
    if r.vivienda == "N":   return "1 Vivienda no ubicada"
    if r.vivienda == "C":   return "2 Vivienda cerrada"
    if r.vivienda == "R":   return "3 Morador renuente"
    return "4 Visitada sin recipientes registrados"
B["motivo"] = B.apply(motivo, axis=1)
B["analitica"] = B.motivo.eq("0 Incluido")

print("\nFlujo de participantes (n = %d)" % len(B))
t = B.groupby("motivo").agg(n=("n", "size"), positivos=("denguepositivo", "sum"))
t["positividad_%"] = (t.positivos / t.n * 100).round(1)
print(t.to_string())
print("\nVivienda x manzana registrada:"); print(pd.crosstab(B.vivienda, B.mz > 0))
print("\nFecha de intervencion registrada aun sin inspeccion:", (B.fecha_interv.notna() & (B.inspeccionada == 0)).sum())
print("Sector asignado: por manzana %d, solo por GPS %d, sin sector %d"
      % (B.sector_mz.notna().sum(), (B.sector_mz.isna() & B.sector_gps.notna()).sum(), B.sector.isna().sum()))
A = B[B.analitica]
print("\nPoblacion analitica: %d (%d positivos, %d negativos); sin manzana: %d"
      % (len(A), A.denguepositivo.sum(), (A.denguepositivo == 0).sum(), (A.mz == 0).sum()))

OUT.parent.mkdir(parents=True, exist_ok=True)
B.to_csv(OUT, index=False, encoding="utf-8")
print("Exportado:", OUT)
