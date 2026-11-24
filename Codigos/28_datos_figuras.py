"""Prepare the public aggregate inputs from an authorized analysis dataset."""

import argparse
from pathlib import Path

import pandas as pd


def export_aggregates(source, output):
    data = pd.read_csv(source)
    analytical = data.loc[data["analitica"]]
    inspected = data.loc[data["inspeccionada"] == 1]
    output.mkdir(parents=True, exist_ok=True)

    counts = data.groupby("motivo").size().rename("n")
    counts.to_csv(output / "flujo.csv")

    exposure = pd.crosstab(analytical["denguepositivo"], analytical["aedes_vivienda"])
    exposure = exposure.rename(
        index={0: "Negativo", 1: "Positivo"},
        columns={0: "sin_aedes", 1: "con_aedes"},
    )
    exposure.index.name = "resultado"
    exposure.to_csv(output / "infestacion_resultado.csv")

    groups = [
        ("0", inspected["retraso"].eq(0)),
        ("1", inspected["retraso"].eq(1)),
        ("2", inspected["retraso"].eq(2)),
        ("3", inspected["retraso"].eq(3)),
        ("4", inspected["retraso"].eq(4)),
        ("5–7", inspected["retraso"].between(5, 7)),
        (">7", inspected["retraso"].gt(7)),
    ]
    rows = []
    for label, mask in groups:
        results = inspected.loc[mask, "denguepositivo"]
        positive = int(results.sum())
        negative = len(results) - positive
        disclose = min(positive, negative) >= 5
        rows.append((label, positive if disclose else None, negative if disclose else None, len(results)))
    delays = pd.DataFrame(rows, columns=["dias", "positivos", "negativos", "total"])
    assert delays["total"].sum() == len(inspected), "Delay groups must cover every inspected household."
    delays = delays.astype({"positivos": "Int64", "negativos": "Int64"})
    delays.to_csv(output / "intervalo_inspeccion.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Authorized individual analysis CSV")
    parser.add_argument("output", type=Path, help="Directory for aggregate CSV output")
    args = parser.parse_args()
    export_aggregates(args.input, args.output)
