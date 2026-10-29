import os
from pathlib import Path

import duckdb
import yaml

from pipeline_runner import run_pipeline_orchestrator


def test_semantic_layer_yaml_structure_and_metrics():
    """Verify semantic_models.yml defines entities, measures, ratio metrics, and thresholds."""
    sem_path = Path("transform_dbt/models/semantic_models.yml")
    assert sem_path.exists(), "semantic_models.yml must exist"

    doc = yaml.safe_load(sem_path.read_text(encoding="utf-8"))
    assert doc["version"] == 2

    model_names = {m["name"] for m in doc.get("semantic_models", [])}
    assert {
        "daily_growth_telemetry",
        "byok_conversion_funnel",
        "feature_catalog_adoption",
    }.issubset(model_names)

    metrics = {m["name"]: m for m in doc.get("metrics", [])}
    for required_metric in (
        "aha_activation_rate",
        "ai_morphological_depth",
        "byok_conversion_rate",
        "byok_modal_completion_rate",
        "byok_verify_failure_rate",
        "viral_k_factor",
    ):
        assert required_metric in metrics
        meta = metrics[required_metric].get("meta", {})
        assert "healthy_threshold" in meta
        assert "source_components" in meta


def test_end_to_end_duckdb_dbt_medallion_and_tests(tmp_path: Path):
    """Run dlt ingestion + dbt run + dbt test in DuckDB and verify Silver & Gold tables."""
    db_file = tmp_path / "test_medallion.duckdb"
    old_duck = os.environ.get("DUCKDB_DATABASE")
    old_dbt_duck = os.environ.get("DBT_DUCKDB_PATH")
    old_target = os.environ.get("DBT_TARGET")

    os.environ["DUCKDB_DATABASE"] = str(db_file)
    os.environ["DBT_DUCKDB_PATH"] = str(db_file)
    os.environ["DBT_TARGET"] = "duckdb"

    try:
        ret = run_pipeline_orchestrator(
            target="all",
            destination="duckdb",
            dataset="readcall_bronze",
            days=10,
            raw_mode=False,
            skip_cloud_publish=True,
        )
        assert ret == 0

        conn = duckdb.connect(str(db_file), read_only=True)
        for table_name in (
            "dim_channels",
            "dim_devices_geo",
            "dim_feature_catalog",
            "fct_daily_traffic",
            "fct_feature_events",
            "gold_daily_growth_kpi",
            "gold_feature_adoption",
            "gold_byok_funnel",
            "gold_referral_loop",
        ):
            cnt = conn.execute(f"SELECT COUNT(*) FROM main.{table_name}").fetchone()[0]
            assert cnt > 0, f"Table {table_name} should be populated"

        # Check dim_feature_catalog has 32 events and source_component mapping
        cat_cnt = conn.execute(
            "SELECT COUNT(*) FROM main.dim_feature_catalog WHERE source_component IS NOT NULL"
        ).fetchone()[0]
        assert cat_cnt == 32

        # Check DACH region flag works in dim_devices_geo
        dach_cnt = conn.execute(
            "SELECT COUNT(*) FROM main.dim_devices_geo WHERE is_dach_region = TRUE"
        ).fetchone()[0]
        assert dach_cnt > 0

        conn.close()
    finally:
        if old_duck is not None:
            os.environ["DUCKDB_DATABASE"] = old_duck
        else:
            os.environ.pop("DUCKDB_DATABASE", None)
        if old_dbt_duck is not None:
            os.environ["DBT_DUCKDB_PATH"] = old_dbt_duck
        else:
            os.environ.pop("DBT_DUCKDB_PATH", None)
        if old_target is not None:
            os.environ["DBT_TARGET"] = old_target
        else:
            os.environ.pop("DBT_TARGET", None)
