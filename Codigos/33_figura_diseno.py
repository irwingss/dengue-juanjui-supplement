# Figura 2. Diseño test-negativo, con datos agregados y cuatro pacientes por pictograma.
import argparse
import math
from pathlib import Path
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrow, Rectangle
parser = argparse.ArgumentParser(description="Generate the test-negative study design figure.")
parser.add_argument("language", choices=("en", "es"))
parser.add_argument("--output", type=Path, default=Path("Reproduccion"))
args = parser.parse_args()
ES = args.language == "es"
tr = lambda en, es: es if ES else en

BASE = Path(__file__).resolve().parents[1]
FIG = args.output / args.language.upper()
FIG.mkdir(parents=True, exist_ok=True)
# mismo codigo de color que el panel B de la figura de riesgo individual: azul = con Aedes, naranja = sin Aedes;
# gris = no incluido (vivienda sin inspeccionar: su condicion no se conoce); franja y flechas en gris claro
CON, SIN, FUERA = "#2a78d6", "#eb6834", "#b4b2a9"
GRIS, FLECHA = "#898781", "#e1e0d9"
plt.rcParams.update({"font.family": "Arial", "font.size": 8.5, "mathtext.fontset": "custom",
                     "mathtext.rm": "Arial", "mathtext.it": "Arial:italic", "mathtext.bf": "Arial:bold"})
AE = r"$\it{Ae.}$ $\it{aegypti}$"

n_tot = pd.read_csv(BASE / "Datos/flujo.csv")["n"].sum()
tab = pd.read_csv(BASE / "Datos/infestacion_resultado.csv", index_col="resultado")
n_pos, n_neg = int(tab.loc["Positivo"].sum()), int(tab.loc["Negativo"].sum())
a_pos, a_neg = int(tab.loc["Positivo", "con_aedes"]), int(tab.loc["Negativo", "con_aedes"])
assert (n_tot, n_pos, n_neg, a_pos, a_neg) == (770, 124, 128, 53, 24), tab
K = 4
fig_ = lambda n: math.floor(n / K + 0.5)
f_pos, f_neg, f_a_pos, f_a_neg = fig_(n_pos), fig_(n_neg), fig_(a_pos), fig_(a_neg)
f_sel = f_pos + f_neg
f_fuera = fig_(n_tot) - f_sel
assert (f_pos, f_neg, f_a_pos, f_a_neg, f_fuera) == (31, 32, 13, 6, 130), (f_pos, f_neg, f_a_pos, f_a_neg, f_fuera)
seleccion = [CON] * (f_a_pos + f_a_neg) + [SIN] * (f_sel - f_a_pos - f_a_neg)

W, H = 2.0, 2.65                                  # celda de cada figura humana
FILAS = 13
C_IZQ, C_SEL, C_DER, C_PN = 5, 5, 5, 3           # columnas: grises a cada lado de la franja, franja, positivos/negativos
assert C_SEL * FILAS >= f_sel and (C_IZQ + C_DER) * FILAS == f_fuera and C_PN * FILAS >= f_neg
Y0 = 50.0                                         # primera fila de figuras
Y_INF = Y0 - (FILAS - 1) * H - 0.95               # borde inferior de los bloques 1 y 2
Y_MED = Y0 - (FILAS - 1) * H / 2                  # altura de las flechas horizontales


def persona(ax, x, y, color):
    ax.add_patch(Circle((x, y + 0.72), 0.42, fc=color, ec="none"))
    ax.add_patch(FancyBboxPatch((x - 0.55, y - 0.95), 1.1, 1.25, boxstyle="round,pad=0,rounding_size=0.4",
                                fc=color, ec="none"))


def rejilla(ax, x0, cols, colores):
    """colores en filas de `cols`, en el orden dado (azules primero). Devuelve (centro x, y inferior)."""
    for i, c in enumerate(colores):
        persona(ax, x0 + (i % cols) * W, Y0 - (i // cols) * H, c)
    return x0 + (cols - 1) * W / 2, Y0 - ((len(colores) - 1) // cols) * H - 0.95


def titulo(x, texto):
    ax.text(x, Y0 + 7.2, texto, ha="center", va="top", fontsize=9, linespacing=1.2)


def flecha(x_ini, x_fin):
    ax.add_patch(FancyArrow(x_ini + 1.8, Y_MED, x_fin - x_ini - 3.6, 0, width=4.2, head_width=8.0, head_length=3.2,
                            length_includes_head=True, fc=FLECHA, ec=GRIS, lw=0.8))


fig, ax = plt.subplots(figsize=(7.6, 5.0), dpi=300)
ax.set_xlim(-1.5, 96); ax.set_aspect("equal"); ax.axis("off")

# ---- bloque 1: todos los notificados; la franja resaltada son los de vivienda inspeccionada
X_TOT = 0.0
x_band = X_TOT + C_IZQ * W
ax.add_patch(Rectangle((x_band - 1.25, Y_INF - 0.6), C_SEL * W + 0.5, Y0 + 1.15 - Y_INF + 1.2, fc=FLECHA, ec=GRIS,
                       lw=0.8, zorder=0))
rejilla(ax, X_TOT, C_IZQ, [FUERA] * (C_IZQ * FILAS))
rejilla(ax, x_band, C_SEL, seleccion)
rejilla(ax, x_band + C_SEL * W, C_DER, [FUERA] * (C_DER * FILAS))
cols_tot = C_IZQ + C_SEL + C_DER
titulo(X_TOT + (cols_tot - 1) * W / 2, tr("Notified febrile\npatients", "Pacientes febriles\nnotificados"))
tot_der = X_TOT + (cols_tot - 1) * W + 0.55

# ---- bloque 2: los de vivienda inspeccionada (la franja del bloque 1, en el mismo orden)
X_SEL = tot_der + 11.0
xc_sel, _ = rejilla(ax, X_SEL, C_SEL, seleccion)
flecha(tot_der, X_SEL - 0.55)
titulo(xc_sel, tr("Patients with\ninspected household", "Pacientes con\nvivienda inspeccionada"))
# notas, cortadas al ancho del bloque como en el Box 1
ax.text(X_SEL - 0.55, Y_INF - 2.0, tr("Patient data: age,\nsex, month, sector\n\nHousehold inspection:\nsame protocol in\n"
                                      "both groups",
                                      "Datos del paciente:\nedad, sexo, mes, sector\n\nInspección de vivienda:\n"
                                      "mismo protocolo en\nambos grupos"),
        ha="left", va="top", fontsize=8.5, linespacing=1.3)

# ---- bloques 3 y 4: positivos y negativos, tras una flecha horizontal igual a la primera (prueba ELISA)
sel_der = X_SEL + (C_SEL - 1) * W + 0.55
X_POS = sel_der + 18.0
X_NEG = X_POS + (C_PN - 1) * W + 9.0
y_pn = Y0
for x0, tit, n, a in ((X_POS, tr("Test-positive\n(cases)", "Positivos\n(casos)"), f_pos, f_a_pos),
                      (X_NEG, tr("Test-negative\n(controls)", "Negativos\n(controles)"), f_neg, f_a_neg)):
    xc, y_b = rejilla(ax, x0, C_PN, [CON] * a + [SIN] * (n - a))
    titulo(xc, tit)
    y_pn = min(y_pn, y_b)
flecha(sel_der, X_POS - 0.55)
ax.text((sel_der + X_POS - 0.55) / 2, Y_MED - 4.8, tr("ELISA\ntest", "Prueba\nELISA"), ha="center", va="top",
        fontsize=8.5, linespacing=1.2)                                 # bajo la flecha: arriba choca con las figuras

# ---- que se compara: concepto del OR, sin estimaciones
xd = (X_POS + X_NEG + (C_PN - 1) * W) / 2                              # centro bajo los dos grupos
ax.add_patch(FancyArrow(xd, y_pn - 1.0, 0, -4.4, width=6.0, head_width=11.0, head_length=2.6,
                        length_includes_head=True, fc=FLECHA, ec=GRIS, lw=0.8))
ax.text(xd, y_pn - 6.4, tr(r"OR = odds$_{\mathrm{positive}}$ ÷ odds$_{\mathrm{negative}}$",
                           r"OR = odds$_{\mathrm{positivos}}$ ÷ odds$_{\mathrm{negativos}}$"),
        ha="center", va="top", fontsize=10.5)
ax.text(xd, y_pn - 11.2, tr("odds = patients with / without\n", "odds = pacientes con / sin\n") + AE
        + tr(" in the household", " en la vivienda"), ha="center", va="top", fontsize=8.5, linespacing=1.3)

# ---- leyenda en recuadro, bajo el bloque 1
filas_ley = ((CON, tr("Household with immature\nstages of ", "Vivienda con estadios\ninmaduros de ") + AE),
             (SIN, tr("Household without ", "Vivienda sin ") + AE),
             (FUERA, tr("Not included: household not\ninspected within 7 days",
                        "No incluido: vivienda no\ninspeccionada en 7 días")))
y_ley = y = Y_INF - 2.0                                                # borde superior del recuadro
for color, etiqueta in filas_ley:
    h = 5.2 if "\n" in etiqueta else 3.4
    persona(ax, X_TOT + 0.6, y - 0.8 - h / 2, color)
    ax.text(X_TOT + 2.3, y - 0.8 - h / 2, etiqueta, ha="left", va="center", fontsize=8.5, linespacing=1.3)
    y -= h
y -= 1.0
ax.add_patch(Rectangle((X_TOT - 1.2, y - 0.6), tot_der + 5.0 - X_TOT, y_ley - y + 0.6, fc="none", ec="black", lw=0.6))
ax.set_ylim(y - 1.5, Y0 + 7.8)

nombre = FIG / "Figura_2_diseno_test_negativo"
fig.savefig(nombre.with_suffix(".png"), bbox_inches="tight")
fig.savefig(nombre.with_suffix(".pdf"), bbox_inches="tight")
