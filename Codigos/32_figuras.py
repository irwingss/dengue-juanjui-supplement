# Figuras 3, 4 y S1 de difusión pública, generadas con datos agregados.
import argparse
from pathlib import Path
import pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
parser = argparse.ArgumentParser(description="Generate public Figures 3, 4 and S1.")
parser.add_argument("language", choices=("en", "es"))
parser.add_argument("--output", type=Path, default=Path("Reproduccion"))
args = parser.parse_args()
ES = args.language == "es"
tr = lambda en, es: es if ES else en

RAIZ = Path(__file__).resolve().parents[1]
FIG, TAB = args.output / args.language.upper(), RAIZ / "Tablas"
FIG.mkdir(parents=True, exist_ok=True)
BLUE, ORANGE, INK, MUTED = "#2a78d6", "#eb6834", "#0b0b0b", "#898781"
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.edgecolor": MUTED, "axes.grid": False,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False})

cuenta = pd.read_csv(RAIZ / "Datos/flujo.csv", index_col="motivo")["n"]
k = lambda m: int(cuenta.get(m, 0))
n_total = int(cuenta.sum())
n_analitica = k("0 Incluido")
n_insp = n_analitica + k("5 Intervencion fuera de 7 dias")
n_no_insp = n_total - n_insp
exposicion = pd.read_csv(RAIZ / "Datos/infestacion_resultado.csv", index_col="resultado")
assert (n_total, n_insp, n_analitica, exposicion.values.sum()) == (770, 254, 252, 252)


def guardar(fig, nombre):
    fig.savefig(FIG / (nombre + ".png"), bbox_inches="tight", dpi=300)
    fig.savefig(FIG / (nombre + ".pdf"), bbox_inches="tight")
    plt.close(fig)


def wilson(x, n, z=1.96):
    p = x / n; d = 1 + z ** 2 / n
    c = (p + z ** 2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / d
    return c - h, c + h


# ==================== FIGURA 3: flujograma ====================
fig, ax = plt.subplots(figsize=(8.0, 6.0), dpi=300)
ax.set_xlim(0, 128); ax.set_ylim(8, 100); ax.axis("off")


def caja(x, y, w, h, texto, relleno="white", borde=MUTED, tam=8):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.6,rounding_size=1.4",
                                facecolor=relleno, edgecolor=borde, linewidth=0.9))
    ax.text(x, y, texto, ha="center", va="center", fontsize=tam, color=INK, linespacing=1.45)


def flecha(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=11,
                                 color=MUTED, linewidth=0.9, shrinkA=0, shrinkB=0))


bf = lambda n: "$\\bf{n\\ =\\ %d}$" % n
caja(50, 92, 56, 8.5, tr("Patients notified with suspected dengue\nJanuary–June 2025, resident in Juanjuí\n",
                         "Pacientes notificados con sospecha de dengue\nenero–junio de 2025, residentes en Juanjuí\n") + bf(n_total))
caja(50, 70, 56, 8.5, tr("Household inspected\n(at least one container examined)\n",
                         "Vivienda inspeccionada\n(al menos un recipiente examinado)\n") + bf(n_insp))
caja(50, 50, 56, 8.5, tr("Inspection within 7 days of notification\n", "Inspección dentro de los 7 días\nde la notificación\n")
     + bf(n_analitica) + tr(" (analytical population)", " (población analítica)"))
excl1 = (tr("Household not inspected (n = %d)\n", "Vivienda no inspeccionada (n = %d)\n") % n_no_insp
         + tr("  not located  %d\n  closed  %d\n  refused  %d\n  visited, no containers  %d",
              "  no ubicada  %d\n  cerrada  %d\n  morador renuente  %d\n  visitada, sin recipientes  %d")
         % (k("1 Vivienda no ubicada"), k("2 Vivienda cerrada"), k("3 Morador renuente"), k("4 Visitada sin recipientes registrados")))
caja(103, 81, 44, 16.5, excl1, relleno="#fdf3ec", borde=ORANGE)
caja(103, 60, 44, 6.0, tr("Inspected > 7 days after\nnotification (n = %d)", "Inspeccionada > 7 días después\nde la notificación (n = %d)")
     % k("5 Intervencion fuera de 7 dias"), relleno="#fdf3ec", borde=ORANGE)
for resultado, x, et in (
    ("Positivo", 27, tr("Laboratory-positive", "Positivos por laboratorio")),
    ("Negativo", 73, tr("Laboratory-negative", "Negativos por laboratorio")),
):
    g = exposicion.loc[resultado]
    n = g.sum()
    aedes = g["con_aedes"]
    caja(x, 26, 32, 9.0, et + "\n" + bf(n) + "\n%d (%.1f%%) " % (aedes, 100 * aedes / n)
         + tr("with", "con") + " $\\it{Ae.\\ aegypti}$", relleno="#f3f7fd", borde=BLUE)
flecha(50, 87.5, 50, 74.5); flecha(50, 65.5, 50, 54.5)
flecha(50, 81, 80.5, 81); flecha(50, 60, 80.5, 60)
flecha(50, 45.5, 27, 31); flecha(50, 45.5, 73, 31)
guardar(fig, "Figura_3_flujograma")

# ==================== FIGURA 4: asociacion ====================
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.6), dpi=300, gridspec_kw={"wspace": 1.15, "width_ratios": [0.75, 1.3]})
tab = pd.DataFrame({"sum": exposicion.loc["Positivo"], "count": exposicion.sum()})
prop = tab["sum"] / tab["count"]
err = np.array([[p - wilson(x, n)[0], wilson(x, n)[1] - p] for p, x, n in zip(prop, tab["sum"], tab["count"])]).T
a1.bar([0, 1], prop, width=0.55, color=[ORANGE, BLUE], edgecolor="white", linewidth=0.5)
a1.errorbar([0, 1], prop, yerr=err, fmt="none", ecolor=INK, elinewidth=1, capsize=4)
for i, (p, x, n) in enumerate(zip(prop, tab["sum"], tab["count"])):
    a1.text(i, 0.04, "%d/%d" % (x, n), ha="center", fontsize=8, color="white", weight="bold")
    a1.text(i, wilson(x, n)[1] + 0.035, "%.0f%%" % (p * 100), ha="center", fontsize=8.5, color=INK)
a1.set_xticks([0, 1])
a1.set_xticklabels(tr(["No $\\it{Aedes}$\nin the household", "$\\it{Aedes}$ present\nin the household"],
                      ["Sin $\\it{Aedes}$\nen la vivienda", "Con $\\it{Aedes}$\nen la vivienda"]))
a1.set_ylim(0, 1); a1.set_ylabel(tr("Laboratory-positive (proportion)", "Resultado positivo (proporción)"))
a1.set_title(tr("A. Positive result by\nhousehold infestation", "A. Resultado positivo según\nla infestación de la vivienda"),
             loc="left", fontsize=9.5, color=INK)

S = pd.read_csv(TAB / "T_modelos_ajuste_secuencial.csv")
S = S[S.exposicion == "Vivienda positiva"]
Z = pd.read_csv(TAB / "T_sensibilidad.csv")
ETQ = {"Crudo": tr("Crude", "Crudo"), "Edad + sexo": tr("Age + sex", "Edad + sexo"),
       "Edad + sexo + mes": tr("+ month", "+ mes"), "Edad + sexo + semana epi (spline)": tr("+ epi week (spline)", "+ semana epidemiológica (spline)"),
       "Edad + sexo + mes + sector (fijo)": tr("+ month + sector (main model)", "+ mes + sector (modelo principal)"),
       "Edad + sexo + mes + sector + ocupacion": tr("+ month + sector + occupation", "+ mes + sector + ocupación")}
filas = [(ETQ[r.modelo], r.OR, r.inf, r.sup, int(r.n), "Edad + sexo + mes + sector (fijo)" == r.modelo) for r in S.itertuples()]
ZE = {"Principal EE robustos manzana": tr("Main, block-clustered SE", "Principal, EE robustos por manzana"),
      "IPW inclusion": tr("Inverse probability of inclusion", "Ponderación por probabilidad de inclusión")}
for r in Z.itertuples():
    et = ZE.get(r.analisis, tr("Main model without sex (n = 249)", "Modelo principal sin sexo (n = 249)"))
    filas.append((et, r.OR, r.inf, r.sup, None, False))
y = np.arange(len(filas))[::-1].astype(float)
y[len(S):] -= 0.6                                          # separa los analisis de sensibilidad
for yi, (et, o, lo, hi, n, princ) in zip(y, filas):
    c = BLUE if princ else INK
    a2.plot([lo, hi], [yi, yi], color=c, lw=1.3 if princ else 1)
    a2.plot(o, yi, "s" if princ else "o", color=c, ms=6 if princ else 4.5)
    a2.text(13.5, yi, "%.2f (%.2f–%.2f)" % (o, lo, hi), va="center", fontsize=7.2, color=INK)
a2.axvline(1, color=MUTED, lw=0.8, ls="--")
a2.set_xscale("log"); a2.set_xlim(0.8, 12); a2.set_xticks([1, 2, 4, 8]); a2.set_xticklabels(["1", "2", "4", "8"])
a2.set_yticks(y); a2.set_yticklabels([f[0] for f in filas], fontsize=7.5)
a2.tick_params(axis="y", length=0)
a2.text(13.5, y[0] + 1.0, tr("OR (95% CI)", "OR (IC 95%)"), fontsize=7.5, weight="bold", va="center")
a2.text(0.8, (y[len(S) - 1] + y[len(S)]) / 2, tr("Sensitivity analyses", "Análisis de sensibilidad"), fontsize=7.2,
        color=MUTED, va="center", ha="right", transform=a2.get_yaxis_transform(), style="italic")
a2.set_xlabel(tr("OR for a household with $\\it{Ae.\\ aegypti}$ (log scale)", "OR de vivienda con $\\it{Ae.\\ aegypti}$ (escala log)"))
a2.set_title(tr("B. Association by model\nspecification", "B. Asociación según la\nespecificación del modelo"), loc="left",
             fontsize=9.5, color=INK, x=-0.62)
a2.spines["left"].set_visible(False)
guardar(fig, "Figura_4_asociacion")

# Figura S1 pública: agrupación de intervalos sin fechas ni su cruce con resultados individuales.
intervalos = pd.read_csv(RAIZ / "Datos/intervalo_inspeccion.csv")
por_resultado = intervalos.dropna(subset=["positivos", "negativos"])
fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=300)
ax.bar(por_resultado.index, por_resultado["positivos"], color=BLUE, label=tr("Positive", "Positivo"))
ax.bar(por_resultado.index, por_resultado["negativos"], bottom=por_resultado["positivos"],
       color=ORANGE, label=tr("Negative", "Negativo"))
sin_desglose = intervalos.loc[intervalos["positivos"].isna()]
ax.bar(sin_desglose.index, sin_desglose["total"], color=MUTED,
       label=tr("Not broken down by result", "Sin desglose por resultado"))
ax.set_xticks(intervalos.index, intervalos["dias"])
ax.set_xlabel(tr("Time from investigation to inspection (days)", "Intervalo entre investigación e inspección (días)"))
ax.set_ylabel(tr("Inspected households", "Viviendas inspeccionadas"))
ax.set_title(tr("Figure S1. Investigation-to-inspection interval", "Figura S1. Intervalo entre investigación e inspección"), loc="left")
dentro = intervalos.loc[intervalos["dias"] != ">7", "total"].sum()
n = intervalos["total"].sum()
ax.text(0.98, 0.97, tr("n = %d | %.1f%% within 7 days", "n = %d | %.1f%% dentro de 7 días") % (n, 100 * dentro / n),
        transform=ax.transAxes, ha="right", va="top", fontsize=8)
ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(1, 0.87))
ax.set_ylim(0, intervalos["total"].max() * 1.17)
guardar(fig, "Figura_S1_intervalo_agregado")
