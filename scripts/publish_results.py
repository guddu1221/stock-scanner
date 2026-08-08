#!/usr/bin/env python
import json, os, sys
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import requests

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"public/data"; DATA.mkdir(parents=True, exist_ok=True)

def latest_file(name):
    p=ROOT/name
    if p.exists(): return p
    # Search recursively for the scanner's known CSV output.
    hits=list(ROOT.rglob(name))
    return hits[0] if hits else None

def df_records(path):
    if not path: return []
    df=pd.read_csv(path)
    df=df.where(pd.notnull(df), None)
    return df.to_dict(orient="records")

def publish(scanner, filename, outjson):
    path=latest_file(filename)
    records=df_records(path)
    payload={
        "scanner":scanner,
        "updated_at":datetime.now(timezone.utc).isoformat(),
        "count":len(records),
        "rows":records,
    }
    (DATA/outjson).write_text(json.dumps(payload, default=str, indent=2))

    url=os.getenv("SUPABASE_URL")
    key=os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print(f"[publish] Supabase not configured; wrote {outjson}")
        return

    headers={"apikey":key,"Authorization":f"Bearer {key}",
             "Content-Type":"application/json","Prefer":"return=minimal"}
    # One scan_run record, followed by result rows. The JSON payload keeps
    # scanner-specific columns without requiring a new DB column every time.
    run={"scanner":scanner,"market":"mixed","status":"success",
         "finished_at":payload["updated_at"],"rows_written":len(records)}
    r=requests.post(url.rstrip("/")+"/rest/v1/scan_runs",headers=headers,json=run,timeout=30)
    r.raise_for_status()
    run_id=None
    # Prefer representation if the server returns it; otherwise results can
    # still be inserted without scan_run_id.
    for rec in records:
        ticker=rec.get("Ticker") or rec.get("ticker")
        if not ticker: continue
        row={
            "scanner":scanner,
            "market":rec.get("Universe") or rec.get("market"),
            "scan_name":rec.get("Scan") or rec.get("scan"),
            "ticker":ticker,
            "company":rec.get("Company") or rec.get("company"),
            "price":rec.get("Price") or rec.get("price") or rec.get("Close"),
            "change_pct":rec.get("Change %") or rec.get("change_pct"),
            "volume":rec.get("Volume") or rec.get("volume"),
            "payload":rec
        }
        rr=requests.post(url.rstrip("/")+"/rest/v1/scan_results",
                          headers=headers,json=row,timeout=30)
        rr.raise_for_status()
    print(f"[publish] Supabase: {scanner}: {len(records)} rows")

if __name__=="__main__":
    publish(sys.argv[1], sys.argv[2], sys.argv[3])
