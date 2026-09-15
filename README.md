# Soil Sample MRV Pipeline Dashboard

This dashboard tracks soil samples through the full pipeline:
Registered -> Dispatched -> Received by Lab -> In Analysis ->
Result Received -> QC Passed -> Closed.

It ships with a realistic demo dataset (`samples.csv`) that
intentionally includes a few planted QC issues, so the dashboard has
something real to catch and demonstrate:
- A duplicated Sample_ID (S007 appears twice)
- A missing SOC result on a sample marked "Result Received"
- An impossible bulk density value (45.00 g/cm3) that should be flagged

## Run it locally (same steps as the biochar dashboard)
```
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000

## Switching to live Google Sheet data (optional, later)
Exactly the same pattern as your biochar dashboard:
1. Put your real sample tracker in a Google Sheet with columns:
   Sample_ID, Plot_ID, Batch_ID, Collection_Date, Dispatch_Date,
   Lab_Received_Date, Status, SOC_Percent, Bulk_Density
2. File -> Share -> Publish to web -> CSV -> copy the link.
3. Set an environment variable named SHEET_CSV_URL to that link
   (or paste it directly into app.py the same way as before).
   When this variable is empty, the app automatically falls back
   to the local samples.csv file, so nothing breaks either way.

## Deploying on Render
Same steps as the biochar dashboard:
1. Push these files to a GitHub repo (keep dashboard.html inside
   a folder literally named `templates`).
2. Render -> New -> Web Service -> connect the repo.
3. Build command: pip install -r requirements.txt
4. Start command: gunicorn app:app
5. (Optional) Add SHEET_CSV_URL as an environment variable if you
   want it reading live Google Sheets data instead of the demo file.
