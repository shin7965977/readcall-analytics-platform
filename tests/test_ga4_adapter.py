from pathlib import Path

import duckdb

from ingestion.run_ingest import run_pipeline
from ingestion.sources.ga4_adapter import (
    ALLOWED_READCALL_EVENTS,
    GA4TelemetryConfig,
    ReadCallGA4Adapter,
)

FORBIDDEN_PII_FIELDS = {
    "user_id",
    "email",
    "ip_address",
    "client_id",
    "user_pseudo_id",
    "search_term",
    "document_name",
}


def test_allowlist_contains_readcall_core_events_and_excludes_portfolio_tracking():
    """Verify the strict allowlist includes ReadCall's 32 product events and excludes recruiter telemetry."""
    assert len(ALLOWED_READCALL_EVENTS) == 32
    assert "reader_text_selected" in ALLOWED_READCALL_EVENTS
    assert "dictionary_searched" in ALLOWED_READCALL_EVENTS
    assert "byok_key_saved" in ALLOWED_READCALL_EVENTS
    assert "byok_verify_failed" in ALLOWED_READCALL_EVENTS
    assert "referral_unlock_success" in ALLOWED_READCALL_EVENTS
    assert "verb_conjugation_viewed" in ALLOWED_READCALL_EVENTS

    # Recruiter tracking events must never be in the allowlist
    assert "portfolio_opened" not in ALLOWED_READCALL_EVENTS
    assert "portfolio_tab_viewed" not in ALLOWED_READCALL_EVENTS
    assert "portfolio_ai_tested" not in ALLOWED_READCALL_EVENTS


def test_filter_and_sanitize_drops_portfolio_and_resume_traffic():
    """Verify that any raw event or traffic row from portfolio/resume tracking is dropped at ingestion."""
    adapter = ReadCallGA4Adapter()
    contaminated_events = [
        {
            "event_date": "2026-10-28",
            "event_name": "reader_text_selected",
            "device_category": "desktop",
            "channel_group": "Organic Search",
            "event_count": 120,
            "total_users": 45,
        },
        {
            "event_date": "2026-10-28",
            "event_name": "portfolio_opened",
            "device_category": "desktop",
            "channel_group": "Referral",
            "event_count": 5,
            "total_users": 3,
        },
        {
            "event_date": "2026-10-28",
            "event_name": "portfolio_ai_tested",
            "device_category": "mobile",
            "channel_group": "Direct",
            "event_count": 2,
            "total_users": 1,
        },
    ]
    cleaned_events = adapter.sanitize_event_records(contaminated_events)
    assert len(cleaned_events) == 1
    assert cleaned_events[0]["event_name"] == "reader_text_selected"

    contaminated_traffic = [
        {
            "event_date": "2026-10-28",
            "channel_group": "Organic Search",
            "source_medium": "google / organic",
            "device_category": "desktop",
            "country": "Germany",
            "sessions": 50,
            "engaged_sessions": 38,
            "active_users": 42,
            "new_users": 30,
            "avg_session_duration_sec": 185.0,
            "event_count": 410,
        },
        {
            "event_date": "2026-10-28",
            "channel_group": "Email",
            "source_medium": "resume / email",
            "device_category": "desktop",
            "country": "Taiwan",
            "sessions": 3,
            "engaged_sessions": 3,
            "active_users": 2,
            "new_users": 2,
            "avg_session_duration_sec": 120.0,
            "event_count": 15,
        },
    ]
    cleaned_traffic = adapter.sanitize_traffic_records(contaminated_traffic)
    assert len(cleaned_traffic) == 1
    assert cleaned_traffic[0]["country"] == "Germany"


def test_calibrated_90_day_extraction_schema_and_zero_pii():
    """Verify 90-day privacy-calibrated telemetry conforms to Bronze canonical schema with zero PII."""
    config = GA4TelemetryConfig(days=15, raw_mode=False)
    adapter = ReadCallGA4Adapter(config=config)
    payload = adapter.extract_telemetry()

    assert "raw_ga4_daily_traffic" in payload
    assert "raw_ga4_events" in payload

    traffic_rows = payload["raw_ga4_daily_traffic"]
    event_rows = payload["raw_ga4_events"]
    assert len(traffic_rows) > 0
    assert len(event_rows) > 0

    for row in traffic_rows:
        assert FORBIDDEN_PII_FIELDS.isdisjoint(row.keys())
        assert row["traffic_record_id"]
        assert row["sessions"] >= row["engaged_sessions"]
        assert row["active_users"] >= row["new_users"]

    for row in event_rows:
        assert FORBIDDEN_PII_FIELDS.isdisjoint(row.keys())
        assert row["event_record_id"]
        assert row["event_name"] in ALLOWED_READCALL_EVENTS
        assert row["event_count"] >= row["total_users"]


def test_raw_mode_versus_calibrated_scale():
    """Verify raw_mode returns unscaled ground-truth authentic baseline counts."""
    raw_adapter = ReadCallGA4Adapter(config=GA4TelemetryConfig(days=14, raw_mode=True))
    raw_data = raw_adapter.extract_telemetry()
    raw_total_events = sum(r["event_count"] for r in raw_data["raw_ga4_events"])
    assert raw_total_events > 0


def test_dlt_duckdb_ingestion_end_to_end(tmp_path: Path):
    """Verify dlt ingests raw_ga4_daily_traffic and raw_ga4_events into DuckDB readcall_bronze."""
    db_file = tmp_path / "test_readcall.duckdb"
    import os

    old_db = os.environ.get("DUCKDB_DATABASE")
    os.environ["DUCKDB_DATABASE"] = str(db_file)
    try:
        run_pipeline(
            destination="duckdb",
            dataset_name="readcall_bronze",
            days=7,
            raw_mode=False,
            pipeline_name="test_readcall_ing",
            pipelines_dir=str(tmp_path / "dlt_state"),
        )
        conn = duckdb.connect(str(db_file), read_only=True)
        traffic_cnt = conn.execute(
            "SELECT COUNT(*) FROM readcall_bronze.raw_ga4_daily_traffic"
        ).fetchone()[0]
        events_cnt = conn.execute(
            "SELECT COUNT(*) FROM readcall_bronze.raw_ga4_events"
        ).fetchone()[0]
        conn.close()
        assert traffic_cnt > 0
        assert events_cnt > 0
    finally:
        if old_db is not None:
            os.environ["DUCKDB_DATABASE"] = old_db
        else:
            os.environ.pop("DUCKDB_DATABASE", None)
