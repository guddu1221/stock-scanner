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
    run_id = run_id or os.environ.get("GITHUB_RUN_ID") or now.strftime("%Y%m%dT%H%M%SZ")

    records = []
    for row in rows:
        records.append(
            {
                "run_id": str(run_id),
                "scan_name": str(row["scan_name"]),
                "ticker": str(row["ticker"]),
                "universe": str(row["universe"]),
                "market": market,
                "timeframe": timeframe,
                "scan_date": now.date().isoformat(),
                "scanned_at": now.isoformat(),
            }
        )

    if not records:
        return 0

    get_supabase().table("scan_results").upsert(
        records,
        on_conflict="run_id,ticker,scan_name,universe",
    ).execute()

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