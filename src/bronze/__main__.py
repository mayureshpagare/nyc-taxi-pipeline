"""Entry point: python -m src.bronze --year 2024 --month 1"""

import argparse
import logging
import sys

from src.bronze.transform import PARTITION_COLUMNS, add_ingestion_metadata, month_predicate
from src.common import layer_path, load_config
from src.ingest.download import build_url, landing_file_path
from src.spark_session import get_spark

log= logging.getLogger("bronze")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load one month from landing into the Bronze Delta Table")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True, choices=range(1,13))
    return parser.parse_args()

def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    args = parse_args()
    config = load_config()
    source = config["source"]

    url = build_url(source["url_template"],args.year, args.month)
    landing_file = landing_file_path(layer_path(config, "landing"), source["dataset"], args.year, args.month, url)
    if not landing_file.exists():
        log.error("Landing file not found: %s - run: python -m src.ingest --year %s --month %s", landing_file, args.year, args.month)
        return 2

    bronze_table = layer_path(config, "bronze") / config["tables"]["bronze"]
    predicate = month_predicate(args.year, args.month)

    spark = get_spark("bronze")
    try:
        raw = spark.read.parquet(str(landing_file))
        source_rows = raw.count()

        bronze = add_ingestion_metadata(raw, landing_file.name, args.year, args.month)

        (
            bronze.write.format("delta")
            .mode("overwrite")
            .option("replaceWhere",predicate)
            .partitionBy(*PARTITION_COLUMNS)
            .save(str(bronze_table))
        )

        bronze_rows = spark.read.format("delta").load(str(bronze_table)).where(predicate).count()
        if bronze_rows != source_rows:
            log.error("Row Count mismatch for %s: landing=%s bronze=%s",predicate, source_rows, bronze_rows)
            return 1

        log.info("Bronze %s-%02d OK: %s rows -> %s", args.year, args.month, bronze_rows, bronze_table)
        return 0
    finally:
        spark.stop()



if __name__ == "__main__":
    sys.exit(main())