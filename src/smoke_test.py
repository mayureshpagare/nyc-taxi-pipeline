"""Smoke Test: Prove Spark + Delta Lake can write and read a table locally"""

import argparse
from pathlib import Path

import yaml
from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "pipeline.yaml"

def load_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_spark(app_name:str) -> SparkSession:
    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog","org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description = "Delta Lake Smoke Test")
    parser.add_argument(
        "--mode",
        choices=["append","overwrite"],
        default="overwrite",
        help="Save Mode for test Write"
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    config = load_config(CONFIG_PATH)
    paths = config["paths"]
    output_path = PROJECT_ROOT / paths["lake_root"] / paths["smoke_test"]

    spark = build_spark("delta-smoke-test")
    try:
        df = spark.createDataFrame(
            [(1, "Manhattan"), (2, "Brooklyn"), (3, "Queens")],
            ["id", "borough"]
        )

        df.write.format("delta").mode(args.mode).save(str(output_path))

        result = spark.read.format("delta").load(str(output_path))
        print("Spark Version:", spark.version)
        print(f"Wrote to {output_path} in {args.mode} mode")
        print(f"Row Count : {result.count()}")
        result.show()
    finally:
        spark.stop()

if __name__ == "__main__":
    main()