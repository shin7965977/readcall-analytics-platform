"""Execute dlt ingestion for ReadCall GA4 Telemetry into Bronze layer."""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime, timedelta

import dlt
from dotenv import load_dotenv

from ingestion.sources.ga4_adapter import GA4TelemetryConfig, ReadCallGA4Adapter

load_dotenv()


def create_readcall_ga4_source(
    config: GA4TelemetryConfig | None = None,
    days: int = 90,
    raw_mode: bool = False,
    since_timestamp: datetime | None = None,
):
    """Declare dlt source and resources for the ReadCall GA4 data pipeline."""
    tel_config = config or GA4TelemetryConfig(
        property_id=os.getenv("GA4_PROPERTY_ID", "559361789"),
        days=days,
        raw_mode=raw_mode,
        since_timestamp=since_timestamp,
    )
    adapter = ReadCallGA4Adapter(config=tel_config)
    data = adapter.extract_telemetry(config=tel_config)

    @dlt.source(name="readcall_ga4")
    def readcall_source():
        @dlt.resource(
            name="raw_ga4_daily_traffic",
            write_disposition="merge",
            primary_key="traffic_record_id",
        )
        def daily_traffic():
            yield data["raw_ga4_daily_traffic"]

        @dlt.resource(
            name="raw_ga4_events",
            write_disposition="merge",
            primary_key="event_record_id",
        )
        def ga4_events():
            yield data["raw_ga4_events"]

        return daily_traffic, ga4_events

    return readcall_source()


def run_pipeline(
    destination: str = "bigquery",
    dataset_name: str = "readcall_bronze",
    days: int = 90,
    raw_mode: bool = False,
    incremental_days: int | None = None,
    pipeline_name: str = "readcall_ga4_pipeline",
    pipelines_dir: str | None = None,
    config: GA4TelemetryConfig | None = None,
):
    """Execute the dlt pipeline ingestion into target destination."""
    if config:
        days = config.days
        raw_mode = config.raw_mode
        since_timestamp = config.since_timestamp
    else:
        since_timestamp = None
        if incremental_days:
            since_timestamp = datetime.now(UTC) - timedelta(days=incremental_days)

    mode_label = "RAW GA4 UN-SCALED" if raw_mode else "90-DAY PRIVACY-CALIBRATED"
    if since_timestamp:
        print(
            f"[dlt] Incremental run ({mode_label}): extracting ReadCall GA4 since {since_timestamp.isoformat()}"
        )
    else:
        print(
            f"[dlt] Full run ({mode_label}): extracting {days} days of ReadCall GA4 telemetry"
        )

    source = create_readcall_ga4_source(
        days=days,
        raw_mode=raw_mode,
        since_timestamp=since_timestamp,
        config=config,
    )

    kwargs = {
        "pipeline_name": pipeline_name,
        "dataset_name": dataset_name,
    }
    if pipelines_dir:
        kwargs["pipelines_dir"] = pipelines_dir

    if destination == "duckdb":
        db_path = os.getenv("DUCKDB_DATABASE", "local_warehouse.duckdb")
        kwargs["destination"] = dlt.destinations.duckdb(credentials=db_path)
    else:
        kwargs["destination"] = destination

    pipeline = dlt.pipeline(**kwargs)
    load_info = pipeline.run(source)
    print(f"[dlt] Ingestion completed successfully: {load_info}")
    return load_info


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ReadCall GA4 Telemetry dlt Ingestion Runner"
    )
    parser.add_argument(
        "--destination",
        type=str,
        default=os.getenv("DLT_DESTINATION", "bigquery"),
        choices=["bigquery", "duckdb"],
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=os.getenv("DLT_DATASET_NAME", "readcall_bronze"),
    )
    parser.add_argument(
        "--days",
        type=int,
        default=int(os.getenv("SIMULATION_DAYS", "90")),
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Disable 90-day privacy scaling and output raw 14-day GA4 counts.",
    )
    parser.add_argument(
        "--incremental-days",
        type=int,
        default=None,
    )
    args = parser.parse_args()
    run_pipeline(
        destination=args.destination,
        dataset_name=args.dataset,
        days=args.days,
        raw_mode=args.raw,
        incremental_days=args.incremental_days,
    )
