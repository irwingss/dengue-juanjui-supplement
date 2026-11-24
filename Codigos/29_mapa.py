"""Draw the public version of Figure 1 from the study sector polygons."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator


SECTORS = {
    "LA MERCED": ("La Merced", "#e6bf59"),
    "JUANJUI CENTRO": ("Juanjuí Centro", "#d66e93"),
    "SANTA ROSA": ("Santa Rosa", "#8fb27d"),
    "SAN JUAN": ("San Juan", "#74b4c6"),
    "JUANJUICILLO": ("Juanjuicillo", "#df8e70"),
}


def draw_map(source, output):
    features = json.loads(source.read_text(encoding="utf-8"))["features"]
    fig, ax = plt.subplots(figsize=(7.5, 7), layout="constrained")
    ax.set_axisbelow(True)
    ax.grid(color="#dadfe1", linewidth=0.55)

    legend = []
    for feature in features:
        name, color = SECTORS[feature["properties"]["sector"]]
        lon, lat = zip(*feature["geometry"]["coordinates"][0])
        ax.fill(lon, lat, color=color, edgecolor="#34424a", linewidth=0.8, alpha=0.85)
        legend.append(Patch(facecolor=color, edgecolor="#34424a", label=name))

    ax.set_aspect(1.008)
    ax.set_xlabel("Longitude / Longitud (°)")
    ax.set_ylabel("Latitude / Latitud (°)")
    ax.ticklabel_format(useOffset=False)
    ax.xaxis.set_major_locator(MaxNLocator(5))
    ax.set_title("Urban sectors of Juanjuí / Sectores urbanos de Juanjuí", loc="left")
    ax.annotate("", xy=(0.08, 0.91), xytext=(0.08, 0.83), xycoords="axes fraction",
                arrowprops={"arrowstyle": "-|>", "color": "#34424a"})
    ax.text(0.08, 0.92, "N", transform=ax.transAxes, ha="center", color="#34424a")
    ax.legend(handles=legend, loc="lower right", framealpha=0.95)
    output.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(output / f"Figura_1_mapa_sectorial.{ext}", dpi=300)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("Reproduccion"))
    options = parser.parse_args()
    boundaries = Path(__file__).resolve().parents[1] / "Datos" / "sectores_juanjui.geojson"
    draw_map(boundaries, options.output)
