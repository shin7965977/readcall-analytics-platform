"""ReadCall GA4 Product Analytics Pipeline Orchestrator (dlt + dbt + Observability)."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

from ingestion.run_ingest import run_pipeline
from ingestion.sources.ga4_adapter import GA4TelemetryConfig


def parse_args():
    parser = argparse.ArgumentParser(
        description="ReadCall GA4 Product Analytics Pipeline Orchestrator"
    )
    parser.add_argument(
        "--target",
        choices=["all", "ingest", "transform", "test"],
        default=os.getenv("PIPELINE_TARGET", "all"),
        help="Pipeline phase to execute (all, ingest, transform, test)",
    )
    parser.add_argument(
        "--destination",
        default=os.getenv("DLT_DESTINATION", "bigquery"),
        help="Storage destination (bigquery or duckdb)",
    )
    parser.add_argument(
        "--dataset",
        default=os.getenv("DLT_DATASET_NAME", "readcall_bronze"),
        help="Bronze target dataset",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=int(os.getenv("SIMULATION_DAYS", "90")),
        help="Number of historical days to extract/calibrate",
    )
    parser.add_argument(
        "--incremental-days",
        type=int,
        default=int(os.getenv("INCREMENTAL_DAYS", "0")) or None,
        help="Lookback days for incremental run",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        default=os.getenv("READCALL_RAW_MODE", "false").lower() == "true",
        help="Extract raw unscaled 14-day GA4 counts instead of 90-day privacy-calibrated mode",
    )
    parser.add_argument(
        "--report-bucket",
        default=os.getenv("ELEMENTARY_REPORT_BUCKET"),
        help="Optional GCS bucket to publish Elementary Observability HTML report",
    )
    return parser.parse_args()


def run_ingestion_step(
    destination: str = "bigquery",
    dataset: str = "readcall_bronze",
    config: GA4TelemetryConfig | None = None,
    days: int = 90,
    incremental_days: int | None = None,
    raw_mode: bool = False,
):
    print("=" * 60)
    print("STEP 1: INGESTION (dlt GA4 Adapter -> readcall_bronze)")
    print("=" * 60)
    tel_config = config or GA4TelemetryConfig(
        days=days,
        raw_mode=raw_mode,
    )
    load_info = run_pipeline(
        destination=destination,
        dataset_name=dataset,
        incremental_days=incremental_days,
        config=tel_config,
    )
    return load_info


def run_transformation_step(
    dbt_target: str | None = None,
    project_dir: str = "transform_dbt",
    profiles_dir: str = "transform_dbt",
) -> int:
    print("=" * 60)
    print("STEP 2: TRANSFORMATION (dbt run -> readcall_silver & readcall_gold)")
    print("=" * 60)
    target = dbt_target or os.getenv("DBT_TARGET", "bigquery")
    env = {**dict(os.environ), "DBT_TARGET": target}

    cmd_run = [
        sys.executable,
        "-m",
        "dbt.cli.main",
        "run",
        "--project-dir",
        project_dir,
        "--profiles-dir",
        profiles_dir,
        "--select",
        "readcall_transform",
    ]
    print(f"[dbt] Running ReadCall models against target: {target}...")
    res_run = subprocess.run(cmd_run, env=env, check=False)  # noqa: S603
    if res_run.returncode != 0:
        print("[dbt] dbt run failed! Exiting pipeline.")
        return res_run.returncode

    print("[dbt] Transformations completed successfully!")
    return 0


def upload_file_to_gcs(
    local_file: str, bucket_name: str, target_name: str | None = None
) -> str | None:
    """Upload a local HTML file to GCS under the isolated readcall/ prefix."""
    if not (bucket_name and os.path.exists(local_file)):
        return None
    try:
        from google.cloud import storage

        if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ and os.path.exists(
            "gcp-key.json"
        ):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(
                "gcp-key.json"
            )

        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blob_name = target_name or f"readcall/{os.path.basename(local_file)}"
        blob = bucket.blob(blob_name)
        blob.cache_control = "no-cache, max-age=0"
        blob.upload_from_filename(local_file, content_type="text/html")
        return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
    except Exception as e:  # noqa: BLE001
        print(f"[Storage] Warning: Failed to upload {local_file} to GCS: {e}")
        return None


def generate_and_publish_dbt_docs(
    project_dir: str = "transform_dbt",
    profiles_dir: str = "transform_dbt",
    report_file: str = "dbt_docs.html",
    gcs_bucket: str | None = None,
) -> str | None:
    """Generate dbt docs, bundle into a standalone single-file HTML, and upload to GCS."""
    print("-" * 60)
    print("[dbt Docs] Generating ReadCall Data Catalog & Lineage documentation...")
    cmd_docs = [
        sys.executable,
        "-m",
        "dbt.cli.main",
        "docs",
        "generate",
        "--project-dir",
        project_dir,
        "--profiles-dir",
        profiles_dir,
    ]
    try:
        res = subprocess.run(cmd_docs, check=False)  # noqa: S603
        if res.returncode != 0:
            return None

        target_dir = os.path.join(project_dir, "target")
        index_path = os.path.join(target_dir, "index.html")
        manifest_path = os.path.join(target_dir, "manifest.json")
        catalog_path = os.path.join(target_dir, "catalog.json")

        if (
            os.path.exists(index_path)
            and os.path.exists(manifest_path)
            and os.path.exists(catalog_path)
        ):
            with open(index_path, encoding="utf-8") as f:
                html = f.read()
            with open(manifest_path, encoding="utf-8") as f:
                manifest = f.read()
            with open(catalog_path, encoding="utf-8") as f:
                catalog = f.read()

            html = html.replace('"MANIFEST.JSON INLINE DATA"', manifest, 1)
            html = html.replace('"CATALOG.JSON INLINE DATA"', catalog, 1)

            with open(report_file, "w", encoding="utf-8") as f:
                f.write(html)

            if gcs_bucket:
                return upload_file_to_gcs(
                    report_file, gcs_bucket, "readcall/dbt_docs.html"
                )
    except Exception as e:  # noqa: BLE001
        print(f"[dbt Docs] Warning: Failed to bundle dbt docs: {e}")
        return None
    return report_file


def run_testing_step(
    dbt_target: str | None = None,
    project_dir: str = "transform_dbt",
    profiles_dir: str = "transform_dbt",
    gcs_bucket: str | None = None,
    skip_cloud_publish: bool = False,
) -> int:
    print("=" * 60)
    print("STEP 3: TESTING & SEMANTIC LAYER VERIFICATION")
    print("=" * 60)
    target = dbt_target or os.getenv("DBT_TARGET", "bigquery")
    env = {**dict(os.environ), "DBT_TARGET": target}

    cmd_test = [
        sys.executable,
        "-m",
        "dbt.cli.main",
        "test",
        "--project-dir",
        project_dir,
        "--profiles-dir",
        profiles_dir,
        "--select",
        "readcall_transform",
    ]
    print(f"[dbt] Running quality tests against target: {target}...")
    res_test = subprocess.run(cmd_test, env=env, check=False)  # noqa: S603

    if not skip_cloud_publish and target == "bigquery":
        shutil.which("edr")
        generate_and_publish_dbt_docs(
            project_dir=project_dir,
            profiles_dir=profiles_dir,
            gcs_bucket=gcs_bucket,
        )

    if res_test.returncode != 0:
        print("[dbt] dbt test failed! Exiting pipeline.")
        return res_test.returncode

    print("[dbt] All ReadCall tests completed successfully!")
    return 0


def run_pipeline_orchestrator(
    target: str = "all",
    destination: str = "bigquery",
    dataset: str = "readcall_bronze",
    days: int = 90,
    incremental_days: int | None = None,
    raw_mode: bool = False,
    report_bucket: str | None = None,
    skip_cloud_publish: bool = False,
) -> int:
    print(f"Starting ReadCall Analytics Pipeline Orchestrator with target: {target}")

    if target in ("all", "ingest"):
        run_ingestion_step(
            destination=destination,
            dataset=dataset,
            days=days,
            incremental_days=incremental_days,
            raw_mode=raw_mode,
        )

    dbt_target = "duckdb" if destination == "duckdb" else "bigquery"

    if target in ("all", "transform"):
        ret = run_transformation_step(dbt_target=dbt_target)
        if ret != 0:
            return ret

    if target in ("all", "test"):
        ret = run_testing_step(
            dbt_target=dbt_target,
            gcs_bucket=report_bucket,
            skip_cloud_publish=skip_cloud_publish,
        )
        if ret != 0:
            return ret

    print("ReadCall Pipeline finished successfully.")
    return 0


def main():
    args = parse_args()
    code = run_pipeline_orchestrator(
        target=args.target,
        destination=args.destination,
        dataset=args.dataset,
        days=args.days,
        incremental_days=args.incremental_days,
        raw_mode=args.raw,
        report_bucket=args.report_bucket,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
