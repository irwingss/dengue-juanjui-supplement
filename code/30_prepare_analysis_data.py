"""Prepare the individual-level data from the authorized surveillance workbook."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.path import Path as Polygon


def coordinates(values):
    numeric = pd.to_numeric(values, errors="coerce")
    return np.where(numeric.abs() > 1000, numeric / 1e6, numeric)


def eligibility_reason(row):
    # A household counts as inspected if at least one container was recorded.
    if row.inspected:
        return "0 Included" if row.within_window else "5 Inspection outside the 7-day window"
    visit_reasons = {
        "N": "1 Household not located",
        "C": "2 Household closed",
        "R": "3 Resident declined",
    }
    return visit_reasons.get(row.visit_status, "4 Visited, no containers recorded")


def prepare_data(workbook, boundaries):
    # The sheet names and source category values are fixed by the surveillance workbook.
    records = pd.read_excel(workbook, sheet_name="FORMATO 10 - INVESTIGACIÓN", header=None).iloc[5:]
    records = records.loc[records[1].notna()].reset_index(drop=True)
    data = pd.DataFrame({
        "record_id": records[1].astype(int),
        "age": pd.to_numeric(records[3], errors="coerce"),
        "sex": records[4].astype(str).str.strip().str.upper(),
        "raw_occupation": records[5].astype(str).str.strip().str.upper(),
        "dengue_positive": records[6].astype(int),
        "visit_status": records[7].astype(str).str.strip().str.upper(),
        "investigation_date": pd.to_datetime(records[8]),
        "visit_date": pd.to_datetime(records[47], errors="coerce"),
        "block": pd.to_numeric(records[11], errors="coerce").fillna(0).astype(int),
        "latitude": coordinates(records[13]),
        "longitude": coordinates(records[14]),
        "containers_inspected": pd.to_numeric(records[16], errors="coerce").fillna(0).astype(int),
        "positive_containers": pd.to_numeric(records[17], errors="coerce").fillna(0).astype(int),
    })
    data.loc[~data.sex.isin(["M", "F"]), "sex"] = np.nan
    date_reversed = data.visit_date < data.investigation_date
    data.loc[date_reversed, ["investigation_date", "visit_date"]] = data.loc[
        date_reversed, ["visit_date", "investigation_date"]
    ].values
    source_occupations = {"ESTUDIANTE": "Student", "AMA DE CASA": "Homemaker"}
    data["occupation"] = data.raw_occupation.map(source_occupations)
    has_other_occupation = data.occupation.isna() & ~data.raw_occupation.isin(["0", "NAN", ""])
    data.loc[has_other_occupation, "occupation"] = "Other"

    data["month"] = data.investigation_date.dt.month
    data["epi_week"] = data.investigation_date.apply(
        lambda date: int(date.strftime("%U")) + (pd.Timestamp(date.year, 1, 1).weekday() != 6)
    )
    data["delay_days"] = (data.visit_date - data.investigation_date).dt.days

    features = json.loads(boundaries.read_text(encoding="utf-8"))["features"]
    plausible = data.latitude.between(-7.3, -7.0) & data.longitude.between(-76.9, -76.6)
    points = np.c_[data.longitude, data.latitude]
    data["gps_sector"] = None
    for feature in features:
        area = Polygon(feature["geometry"]["coordinates"][0])
        within = plausible & area.contains_points(points)
        data.loc[within & data.gps_sector.isna(), "gps_sector"] = feature["properties"]["sector"]

    sectors = pd.read_excel(workbook, sheet_name="LOGISTICO")[["n", "sector"]]
    sectors = sectors.rename(columns={"n": "record_id", "sector": "block_sector"})
    data = data.merge(sectors, on="record_id", how="left")
    data["block_sector"] = data.block_sector.str.upper().str.replace("Í", "I")
    data["sector"] = data.block_sector.fillna(data.gps_sector)

    data["inspected"] = (data.containers_inspected > 0).astype(int)
    data["household_aedes"] = (data.positive_containers > 0).astype(int)
    data["container_index"] = data.positive_containers / data.containers_inspected.replace(0, np.nan)
    data["within_window"] = data.delay_days.between(0, 7)
    data["eligibility_reason"] = data.apply(eligibility_reason, axis=1)
    data["included"] = data.eligibility_reason.eq("0 Included")
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("output", type=Path, help="Local path for the restricted analysis CSV")
    parser.add_argument("--boundaries", type=Path,
                        default=Path(__file__).resolve().parents[1] / "data" / "juanjui_sectors.geojson")
    args = parser.parse_args()
    data = prepare_data(args.workbook, args.boundaries)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(args.output, index=False, encoding="utf-8")
    print(f"Prepared {len(data)} records, with {data.included.sum()} included in the analysis.")
