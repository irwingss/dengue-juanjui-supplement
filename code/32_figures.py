"""Generate public Figures 3, 4 and S1 from aggregate data."""
import argparse
from pathlib import Path
import pandas as pd, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
parser = argparse.ArgumentParser(description="Generate public Figures 3, 4 and S1.")
parser.add_argument("--output", type=Path, default=Path("build/figures"))
args = parser.parse_args()

ROOT = Path(__file__).resolve().parents[1]
FIG, TAB = args.output, ROOT / "tables" / "analysis_outputs"
FIG.mkdir(parents=True, exist_ok=True)
BLUE, ORANGE, INK, MUTED = "#2a78d6", "#eb6834", "#0b0b0b", "#898781"
plt.rcParams.update({"font.family": "Arial", "font.size": 9, "axes.edgecolor": MUTED, "axes.grid": False,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False})

counts = pd.read_csv(ROOT / "data/participant_flow.csv", index_col="eligibility_reason")["n"]
k = lambda m: int(counts.get(m, 0))
n_total = int(counts.sum())
n_included = k("0 Included")
n_inspected = n_included + k("5 Inspection outside the 7-day window")
n_not_inspected = n_total - n_inspected
exposure = pd.read_csv(ROOT / "data/infestation_by_test_result.csv", index_col="test_result")
assert (n_total, n_inspected, n_included, exposure.values.sum()) == (770, 254, 252, 252)


def save_figure(fig, name):
    fig.savefig(FIG / (name + ".png"), bbox_inches="tight", dpi=300)
    fig.savefig(FIG / (name + ".pdf"), bbox_inches="tight")
    plt.close(fig)


def wilson(x, n, z=1.96):
    p = x / n; d = 1 + z ** 2 / n
    c = (p + z ** 2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / d
    return c - h, c + h


# Figure 3: participant flow
fig, ax = plt.subplots(figsize=(8.0, 6.0), dpi=300)
ax.set_xlim(0, 128); ax.set_ylim(8, 100); ax.axis("off")


def box(x, y, w, h, text, fill="white", border=MUTED, size=8):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.6,rounding_size=1.4",
                                facecolor=fill, edgecolor=border, linewidth=0.9))
    ax.text(x, y, text, ha="center", va="center", fontsize=size, color=INK, linespacing=1.45)


def arrow(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=11,
                                 color=MUTED, linewidth=0.9, shrinkA=0, shrinkB=0))


bf = lambda n: "$\\bf{n\\ =\\ %d}$" % n
box(50, 92, 56, 8.5, 'Patients notified with suspected dengue\nJanuary–June 2025, resident in Juanjuí\n' + bf(n_total))
box(50, 70, 56, 8.5, 'Household inspected\n(at least one container examined)\n' + bf(n_inspected))
box(50, 50, 56, 8.5, 'Inspection within 7 days of notification\n'
     + bf(n_included) + ' (analytical population)')
not_inspected = ('Household not inspected (n = %d)\n' % n_not_inspected
         + '  not located  %d\n  closed  %d\n  refused  %d\n  visited, no containers  %d'
         % (k("1 Household not located"), k("2 Household closed"), k("3 Resident declined"), k("4 Visited, no containers recorded")))
box(103, 81, 44, 16.5, not_inspected, fill="#fdf3ec", border=ORANGE)
box(103, 60, 44, 6.0, 'Inspected > 7 days after\nnotification (n = %d)'
     % k("5 Inspection outside the 7-day window"), fill="#fdf3ec", border=ORANGE)
for test_result, x, et in (
    ("Positive", 27, 'Laboratory-positive'),
    ("Negative", 73, 'Laboratory-negative'),
):
    g = exposure.loc[test_result]
    n = g.sum()
    aedes = g["with_aedes"]
    box(x, 26, 32, 9.0, et + "\n" + bf(n) + "\n%d (%.1f%%) " % (aedes, 100 * aedes / n)
         + 'with' + " $\\it{Ae.\\ aegypti}$", fill="#f3f7fd", border=BLUE)
arrow(50, 87.5, 50, 74.5); arrow(50, 65.5, 50, 54.5)
arrow(50, 81, 80.5, 81); arrow(50, 60, 80.5, 60)
arrow(50, 45.5, 27, 31); arrow(50, 45.5, 73, 31)
save_figure(fig, "figure_3_participant_flow")

# Figure 4: household infestation and test result
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.6), dpi=300, gridspec_kw={"wspace": 1.15, "width_ratios": [0.75, 1.3]})
tab = pd.DataFrame({"sum": exposure.loc["Positive"], "count": exposure.sum()})
prop = tab["sum"] / tab["count"]
err = np.array([[p - wilson(x, n)[0], wilson(x, n)[1] - p] for p, x, n in zip(prop, tab["sum"], tab["count"])]).T
a1.bar([0, 1], prop, width=0.55, color=[ORANGE, BLUE], edgecolor="white", linewidth=0.5)
a1.errorbar([0, 1], prop, yerr=err, fmt="none", ecolor=INK, elinewidth=1, capsize=4)
for i, (p, x, n) in enumerate(zip(prop, tab["sum"], tab["count"])):
    a1.text(i, 0.04, "%d/%d" % (x, n), ha="center", fontsize=8, color="white", weight="bold")
    a1.text(i, wilson(x, n)[1] + 0.035, "%.0f%%" % (p * 100), ha="center", fontsize=8.5, color=INK)
a1.set_xticks([0, 1])
a1.set_xticklabels(["No $\\it{Aedes}$\nin the household", "$\\it{Aedes}$ present\nin the household"])
a1.set_ylim(0, 1); a1.set_ylabel('Laboratory-positive (proportion)')
a1.set_title('A. Positive result by\nhousehold infestation',
             loc="left", fontsize=9.5, color=INK)

S = pd.read_csv(TAB / "sequential_adjustment_models.csv")
S = S[S.exposure == "Positive household"]
Z = pd.read_csv(TAB / "sensitivity_analyses.csv")
MODEL_LABELS = {"Crude": 'Crude', "Age + sex": 'Age + sex',
       "Age + sex + month": '+ month', "Age + sex + epidemiological week (spline)": '+ epi week (spline)',
       "Age + sex + month + sector (fixed effects)": '+ month + sector (main model)',
       "Age + sex + month + sector + occupation": '+ month + sector + occupation'}
rows = [(MODEL_LABELS[r.model], r.OR, r.ci_lower, r.ci_upper, int(r.n), "Age + sex + month + sector (fixed effects)" == r.model) for r in S.itertuples()]
SENSITIVITY_LABELS = {"Main model with block-clustered standard errors": 'Main, block-clustered SE',
      "Inverse probability of inclusion weighting": 'Inverse probability of inclusion'}
for r in Z.itertuples():
    et = SENSITIVITY_LABELS.get(r.analysis, 'Main model without sex (n = 249)')
    rows.append((et, r.OR, r.ci_lower, r.ci_upper, None, False))
y = np.arange(len(rows))[::-1].astype(float)
y[len(S):] -= 0.6                                          # Separate the sensitivity analyses from the main models.
for yi, (et, o, lo, hi, n, main) in zip(y, rows):
    c = BLUE if main else INK
    a2.plot([lo, hi], [yi, yi], color=c, lw=1.3 if main else 1)
    a2.plot(o, yi, "s" if main else "o", color=c, ms=6 if main else 4.5)
    a2.text(13.5, yi, "%.2f (%.2f–%.2f)" % (o, lo, hi), va="center", fontsize=7.2, color=INK)
a2.axvline(1, color=MUTED, lw=0.8, ls="--")
a2.set_xscale("log"); a2.set_xlim(0.8, 12); a2.set_xticks([1, 2, 4, 8]); a2.set_xticklabels(["1", "2", "4", "8"])
a2.set_yticks(y); a2.set_yticklabels([f[0] for f in rows], fontsize=7.5)
a2.tick_params(axis="y", length=0)
a2.text(13.5, y[0] + 1.0, 'OR (95% CI)', fontsize=7.5, weight="bold", va="center")
a2.text(0.8, (y[len(S) - 1] + y[len(S)]) / 2, 'Sensitivity analyses', fontsize=7.2,
        color=MUTED, va="center", ha="right", transform=a2.get_yaxis_transform(), style="italic")
a2.set_xlabel('OR for a household with $\\it{Ae.\\ aegypti}$ (log scale)')
a2.set_title('B. Association by model\nspecification', loc="left",
             fontsize=9.5, color=INK, x=-0.62)
a2.spines["left"].set_visible(False)
save_figure(fig, "figure_4_household_infestation")

# Figure S1: grouped delays without individual visit dates.
delays = pd.read_csv(ROOT / "data/inspection_delay.csv")
by_result = delays.dropna(subset=["positive", "negative"])
fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=300)
ax.bar(by_result.index, by_result["positive"], color=BLUE, label='Positive')
ax.bar(by_result.index, by_result["negative"], bottom=by_result["positive"],
       color=ORANGE, label='Negative')
pooled = delays.loc[delays["positive"].isna()]
ax.bar(pooled.index, pooled["total"], color=MUTED,
       label='Not broken down by result')
ax.set_xticks(delays.index, delays["days"])
ax.set_xlabel('Time from investigation to inspection (days)')
ax.set_ylabel('Inspected households')
ax.set_title('Figure S1. Investigation-to-inspection interval', loc="left")
within_window = delays.loc[delays["days"] != ">7", "total"].sum()
n = delays["total"].sum()
ax.text(0.98, 0.97, 'n = %d | %.1f%% within 7 days' % (n, 100 * within_window / n),
        transform=ax.transAxes, ha="right", va="top", fontsize=8)
ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(1, 0.87))
ax.set_ylim(0, delays["total"].max() * 1.17)
save_figure(fig, "figure_s1_inspection_delay")
