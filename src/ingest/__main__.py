"""Entry point: python -m src.ingest --year 2024 --month 1 [--force]"""  # NEW

import argparse
import logging
import sys
from datetime import date

import requests

from src.common import layer_path, load_config
from src.ingest.download import build_url, download_file, landing_file_path

log = logging.getLogger("ingest")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download one month of TLC trip data")
    parser.add_argument("--year",type=int, required=True)
    parser.add_argument("--month",type=int, required=True,choices=range(1,13))
    parser.add_argument("--force",action="store_true",help="Re-download even if the file exists")
    return parser.parse_args()

def validate_period(year:int, month:int, first_year:int)-> None:
    if year < first_year:
        raise ValueError(f"No data before {first_year}; got {year}")
    if date(year, month, 1)>date.today():
        raise ValueError(f"{year}-{month:02d} is in the future")

def main() -> int:
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = parse_args()
    config = load_config()
    source = config["source"]

    try:
        validate_period(args.year, args.month, source["first_year"])
    except ValueError as err:
        log.error("%s",err)
        return 2

    url = build_url(source["url_template"], args.year, args.month)
    target = landing_file_path(layer_path(config,"landing"),source["dataset"],args.year, args.month,url)

    if target.exists() and not args.force:
        log.info("Already downloaded, skipping : %s (use --force to re-download)",target)
        return 0

    log.info("Downloading %s",url)
    try:
        size = download_file(url, target, timeout=source["timeout_seconds"])
    except requests.HTTPError as err:
        status = err.response.status_code
        log.error("HTTP %s for %s - the month may not be published yet (TLC lags ~2 months)", status, url)
        return 1
    except (requests.ConnectionError, requests.Timeout) as err:
        log.error("Network Problem: %s",err)
        return 1

    log.info("Saved %s (%.1f MB)",target, size/1_000_000)
    return 0

if __name__ == "__main__":
    sys.exit(main())