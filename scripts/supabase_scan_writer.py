"""Shared Supabase writer for scanner workflows."""

import os
from datetime import datetime, timezone , timedelta
from typing import Iterable, Mapping

from supabase import create_client

def get_supabase():
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required")
    return create_client(url, key)


def upload_scan_records(
    rows: Iterable[Mapping],
    *,
    market: str,
    timeframe: str,
    run_id: str | None = None,
) -> int:
    """Insert/upsert scan hits and return the number of records submitted."""
    now = datetime.now(timezone.utc)
    active_run_id = str(run_id or os.environ.get("GITHUB_RUN_ID") or now.strftime("%Y%m%dT%H%M%SZ"))
    scan_date_iso = now.date().isoformat()
    scanned_at_iso = now.isoformat()

    records = [
        {
            "run_id": active_run_id,
            "scan_name": str(row["scan_name"]),
            "ticker": str(row["ticker"]),
            "universe": str(row["universe"]),
            "market": market,
            "timeframe": timeframe,
            "scan_date": scan_date_iso,
            "scanned_at": scanned_at_iso,
        }
        for row in rows
    ]

    if not records:
        print("ℹ️ No records to upload.")
        return 0

    print(f"Uploading {len(records)} records to Supabase...")

    try:
        get_supabase().table("scan_results").upsert(
            records,
            on_conflict="ticker,scan_date,universe,scan_name",
        ).execute()
        print(f"✅ Successfully uploaded/upserted {len(records)} records.")
    except Exception as e:
        print(f"❌ Failed to upload records to Supabase: {e}")
        raise

    return len(records)

def cleanup_scan_history(days_to_keep: int = 30) -> int:
    """Delete scan records older than `days_to_keep` directly via Supabase client."""
    supabase = get_supabase()
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_to_keep)).date().isoformat()

    response = supabase.table("scan_result") \
        .delete() \
        .lt("scan_date", cutoff_date) \
        .execute()

    deleted_count = len(response.data) if response.data else 0
    print(f"Deleted {deleted_count} scan records older than {days_to_keep} days.")
    return deleted_count
