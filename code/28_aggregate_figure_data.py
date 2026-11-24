"""Prepare the public aggregate inputs from an authorized analysis dataset."""

import argparse
from pathlib import Path

import pandas as pd


def export_aggregates(source, output):
    data = pd.read_csv(source)
    analytical = data.loc[data["included"]]
    inspected = data.loc[data["inspected"] == 1]
    output.mkdir(parents=True, exist_ok=True)

    counts = data.groupby("eligibility_reason").size().rename("n")
    counts.to_csv(output / "participant_flow.csv")

    exposure = pd.crosstab(analytical["dengue_positive"], analytical["household_aedes"])
    exposure = exposure.rename(
        index={0: "Negative", 1: "Positive"},
        columns={0: "without_aedes", 1: "with_aedes"},
    )
    exposure.index.name = "test_result"
    exposure.to_csv(output / "infestation_by_test_result.csv")

    groups = [
        ("0", inspected["delay_days"].eq(0)),
        ("1", inspected["delay_days"].eq(1)),
        ("2", inspected["delay_days"].eq(2)),
        ("3", inspected["delay_days"].eq(3)),
        ("4", inspected["delay_days"].eq(4)),
        ("5–7", inspected["delay_days"].between(5, 7)),
        (">7", inspected["delay_days"].gt(7)),
    ]
    rows = []
    for label, mask in groups:
        results = inspected.loc[mask, "dengue_positive"]
        positive = int(results.sum())
        negative = len(results) - positive
        disclose = min(positive, negative) >= 5
        rows.append((label, positive if disclose else None, negative if disclose else None, len(results)))
    delays = pd.DataFrame(rows, columns=["days", "positive", "negative", "total"])
    assert delays["total"].sum() == len(inspected), "Delay groups must cover every inspected household."
    delays = delays.astype({"positive": "Int64", "negative": "Int64"})
    delays.to_csv(output / "inspection_delay.csv", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Authorized individual analysis CSV")
    parser.add_argument("output", type=Path, help="Directory for aggregate CSV output")
    args = parser.parse_args()
    export_aggregates(args.input, args.output)
