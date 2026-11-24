"""Draw the test-negative study design using four patients per pictogram."""
import argparse
import math
from pathlib import Path
import pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, FancyArrow, Rectangle
parser = argparse.ArgumentParser(description="Generate the test-negative study design figure.")
parser.add_argument("--output", type=Path, default=Path("build/figures"))
args = parser.parse_args()

BASE = Path(__file__).resolve().parents[1]
FIG = args.output
FIG.mkdir(parents=True, exist_ok=True)
# Blue marks infestation, orange marks no infestation, and gray marks excluded patients.
INFESTED, UNINFESTED, EXCLUDED = "#2a78d6", "#eb6834", "#b4b2a9"
GRAY, ARROW_COLOR = "#898781", "#e1e0d9"
plt.rcParams.update({"font.family": "Arial", "font.size": 8.5, "mathtext.fontset": "custom",
                     "mathtext.rm": "Arial", "mathtext.it": "Arial:italic", "mathtext.bf": "Arial:bold"})
AE = r"$\it{Ae.}$ $\it{aegypti}$"

n_tot = pd.read_csv(BASE / "data/participant_flow.csv")["n"].sum()
tab = pd.read_csv(BASE / "data/infestation_by_test_result.csv", index_col="test_result")
n_pos, n_neg = int(tab.loc["Positive"].sum()), int(tab.loc["Negative"].sum())
a_pos, a_neg = int(tab.loc["Positive", "with_aedes"]), int(tab.loc["Negative", "with_aedes"])
assert (n_tot, n_pos, n_neg, a_pos, a_neg) == (770, 124, 128, 53, 24), tab
K = 4
fig_ = lambda n: math.floor(n / K + 0.5)
f_pos, f_neg, f_a_pos, f_a_neg = fig_(n_pos), fig_(n_neg), fig_(a_pos), fig_(a_neg)
f_sel = f_pos + f_neg
f_excluded = fig_(n_tot) - f_sel
assert (f_pos, f_neg, f_a_pos, f_a_neg, f_excluded) == (31, 32, 13, 6, 130), (f_pos, f_neg, f_a_pos, f_a_neg, f_excluded)
selection = [INFESTED] * (f_a_pos + f_a_neg) + [UNINFESTED] * (f_sel - f_a_pos - f_a_neg)

W, H = 2.0, 2.65                                  # Pictogram cell size.
ROWS = 13
C_LEFT, C_SEL, C_RIGHT, C_PN = 5, 5, 5, 3           # Column counts for each group.
assert C_SEL * ROWS >= f_sel and (C_LEFT + C_RIGHT) * ROWS == f_excluded and C_PN * ROWS >= f_neg
Y0 = 50.0                                         # First row of pictograms.
Y_BOTTOM = Y0 - (ROWS - 1) * H - 0.95               # Lower edge of the first two groups.
Y_MIDDLE = Y0 - (ROWS - 1) * H / 2                  # Height of horizontal arrows.


def person(ax, x, y, color):
    ax.add_patch(Circle((x, y + 0.72), 0.42, fc=color, ec="none"))
    ax.add_patch(FancyBboxPatch((x - 0.55, y - 0.95), 1.1, 1.25, boxstyle="round,pad=0,rounding_size=0.4",
                                fc=color, ec="none"))


def grid(ax, x0, cols, colors):
    """Place colors in row order and return the center and lower edge."""
    for i, c in enumerate(colors):
        person(ax, x0 + (i % cols) * W, Y0 - (i // cols) * H, c)
    return x0 + (cols - 1) * W / 2, Y0 - ((len(colors) - 1) // cols) * H - 0.95


def title(x, text):
    ax.text(x, Y0 + 7.2, text, ha="center", va="top", fontsize=9, linespacing=1.2)


def arrow(x_start, x_end):
    ax.add_patch(FancyArrow(x_start + 1.8, Y_MIDDLE, x_end - x_start - 3.6, 0, width=4.2, head_width=8.0, head_length=3.2,
                            length_includes_head=True, fc=ARROW_COLOR, ec=GRAY, lw=0.8))


fig, ax = plt.subplots(figsize=(7.6, 5.0), dpi=300)
ax.set_xlim(-1.5, 96); ax.set_aspect("equal"); ax.axis("off")

# All notified patients, with the included population highlighted.
X_TOT = 0.0
x_band = X_TOT + C_LEFT * W
ax.add_patch(Rectangle((x_band - 1.25, Y_BOTTOM - 0.6), C_SEL * W + 0.5, Y0 + 1.15 - Y_BOTTOM + 1.2, fc=ARROW_COLOR, ec=GRAY,
                       lw=0.8, zorder=0))
grid(ax, X_TOT, C_LEFT, [EXCLUDED] * (C_LEFT * ROWS))
grid(ax, x_band, C_SEL, selection)
grid(ax, x_band + C_SEL * W, C_RIGHT, [EXCLUDED] * (C_RIGHT * ROWS))
cols_tot = C_LEFT + C_SEL + C_RIGHT
title(X_TOT + (cols_tot - 1) * W / 2, 'Notified febrile\npatients')
total_right = X_TOT + (cols_tot - 1) * W + 0.55

# Included patients in the same order as the highlighted group.
X_SEL = total_right + 11.0
xc_sel, _ = grid(ax, X_SEL, C_SEL, selection)
arrow(total_right, X_SEL - 0.55)
title(xc_sel, 'Patients with\ninspected household')
# Place the study protocol beneath the included group.
ax.text(X_SEL - 0.55, Y_BOTTOM - 2.0, 'Patient data: age,\nsex, month, sector\n\nHousehold inspection:\nsame protocol in\nboth groups',
        ha="left", va="top", fontsize=8.5, linespacing=1.3)

# Split patients by ELISA result.
selected_right = X_SEL + (C_SEL - 1) * W + 0.55
X_POS = selected_right + 18.0
X_NEG = X_POS + (C_PN - 1) * W + 9.0
y_pn = Y0
for x0, tit, n, a in ((X_POS, 'Test-positive\n(cases)', f_pos, f_a_pos),
                      (X_NEG, 'Test-negative\n(controls)', f_neg, f_a_neg)):
    xc, y_b = grid(ax, x0, C_PN, [INFESTED] * a + [UNINFESTED] * (n - a))
    title(xc, tit)
    y_pn = min(y_pn, y_b)
arrow(selected_right, X_POS - 0.55)
ax.text((selected_right + X_POS - 0.55) / 2, Y_MIDDLE - 4.8, 'ELISA\ntest', ha="center", va="top",
        fontsize=8.5, linespacing=1.2)

# Define the odds ratio.
xd = (X_POS + X_NEG + (C_PN - 1) * W) / 2                              # Center beneath the two groups.
ax.add_patch(FancyArrow(xd, y_pn - 1.0, 0, -4.4, width=6.0, head_width=11.0, head_length=2.6,
                        length_includes_head=True, fc=ARROW_COLOR, ec=GRAY, lw=0.8))
ax.text(xd, y_pn - 6.4, 'OR = odds$_{\\mathrm{positive}}$ ÷ odds$_{\\mathrm{negative}}$',
        ha="center", va="top", fontsize=10.5)
ax.text(xd, y_pn - 11.2, 'odds = patients with / without\n' + AE
        + ' in the household', ha="center", va="top", fontsize=8.5, linespacing=1.3)

# Boxed legend below the notified population.
legend_rows = ((INFESTED, 'Household with immature\nstages of ' + AE),
             (UNINFESTED, 'Household without ' + AE),
             (EXCLUDED, 'Not included: household not\ninspected within 7 days'))
legend_top = y = Y_BOTTOM - 2.0                                                # Top edge of the legend box.
for color, label in legend_rows:
    h = 5.2 if "\n" in label else 3.4
    person(ax, X_TOT + 0.6, y - 0.8 - h / 2, color)
    ax.text(X_TOT + 2.3, y - 0.8 - h / 2, label, ha="left", va="center", fontsize=8.5, linespacing=1.3)
    y -= h
y -= 1.0
ax.add_patch(Rectangle((X_TOT - 1.2, y - 0.6), total_right + 5.0 - X_TOT, legend_top - y + 0.6, fc="none", ec="black", lw=0.6))
ax.set_ylim(y - 1.5, Y0 + 7.8)

name = FIG / "figure_2_test_negative_design"
fig.savefig(name.with_suffix(".png"), bbox_inches="tight")
fig.savefig(name.with_suffix(".pdf"), bbox_inches="tight")
