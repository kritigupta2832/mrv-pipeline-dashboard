import os
import pandas as pd
from flask import Flask, render_template

app = Flask(__name__)

# Same pattern as your biochar dashboard: if SHEET_CSV_URL is set (e.g. on
# Render, or once you publish your own sample-tracking Google Sheet), it
# reads live from there. Otherwise it falls back to the local demo file,
# so this works immediately without any extra setup.
SHEET_CSV_URL = os.environ.get(
    "SHEET_CSV_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vTzih6HRTfnfFjRmgs0LAcxuvffkBXGuVOTvcyKKGImE0B1dZfgUWC36CVy7ADeLa_zgKPHTjf4vI77/pub?gid=1037708497&single=true&output=csv"
)
LOCAL_FILE = "samples.csv"

# The order the pipeline is expected to move through
STAGE_ORDER = [
    "Registered",
    "Dispatched",
    "Received by Lab",
    "In Analysis",
    "Result Received",
    "QC Passed",
    "Closed",
]


def load_data():
    if SHEET_CSV_URL:
        df = pd.read_csv(SHEET_CSV_URL)
    else:
        df = pd.read_csv(LOCAL_FILE)
    df.columns = [c.strip() for c in df.columns]
    return df


def run_qc_checks(df):
    issues = []

    # 1. Duplicate sample IDs
    dup_ids = df[df.duplicated("Sample_ID", keep=False)]["Sample_ID"].unique()
    for sid in dup_ids:
        issues.append({"Sample_ID": sid, "Issue": "Duplicate Sample_ID"})

    # 2. Missing SOC result for samples that should have one
    missing_result = df[
        df["Status"].isin(["Result Received", "QC Passed", "Closed"])
        & df["SOC_Percent"].isna()
    ]
    for sid in missing_result["Sample_ID"]:
        issues.append({"Sample_ID": sid, "Issue": "Missing SOC result despite status"})

    # 3. Anomalous bulk density (soil is realistically ~1.0-1.8 g/cm3)
    bad_bd = df[(df["Bulk_Density"].notna()) & ((df["Bulk_Density"] < 0.9) | (df["Bulk_Density"] > 2.0))]
    for sid in bad_bd["Sample_ID"]:
        issues.append({"Sample_ID": sid, "Issue": "Bulk density out of plausible range"})

    # 4. Anomalous pH (field soils realistically fall between ~3.5 and 10)
    if "pH" in df.columns:
        ph = pd.to_numeric(df["pH"], errors="coerce")
        bad_ph = df[(ph.notna()) & ((ph < 3.5) | (ph > 10.0))]
        for sid in bad_ph["Sample_ID"]:
            issues.append({"Sample_ID": sid, "Issue": "pH out of plausible range"})

        # Non-numeric text accidentally entered in the pH column
        text_ph = df[(df["pH"].notna()) & (ph.isna())]
        for sid in text_ph["Sample_ID"]:
            issues.append({"Sample_ID": sid, "Issue": "pH value is not a number"})

    return issues


def compute_turnaround(df):
    d = df.dropna(subset=["Collection_Date", "Lab_Received_Date"]).copy()
    if d.empty:
        return None
    d["Collection_Date"] = pd.to_datetime(d["Collection_Date"])
    d["Lab_Received_Date"] = pd.to_datetime(d["Lab_Received_Date"])
    d["turnaround_days"] = (d["Lab_Received_Date"] - d["Collection_Date"]).dt.days
    return round(d["turnaround_days"].mean(), 1)


@app.route("/")
def pipeline():
    df = load_data()

    stage_counts = df["Status"].value_counts().reindex(STAGE_ORDER, fill_value=0)
    labels = stage_counts.index.tolist()
    values = stage_counts.values.tolist()

    qc_issues = run_qc_checks(df)
    avg_turnaround = compute_turnaround(df)

    batch_counts = df["Batch_ID"].nunique()

    return render_template(
        "pipeline.html",
        labels=labels,
        values=values,
        total_samples=len(df),
        batch_count=batch_counts,
        qc_issues=qc_issues,
        qc_count=len(qc_issues),
        avg_turnaround=avg_turnaround,
        table_rows=df.to_dict(orient="records"),
        columns=df.columns.tolist(),
    )


if __name__ == "__main__":
    app.run(debug=True)
