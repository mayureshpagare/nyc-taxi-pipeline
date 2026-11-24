"""Silver transformations: standardise, flag invalid rows, dedupe, derive columns.

Every function takes and returns DataFrames (no reads or writes), so the same
logic runs locally, on Databricks and in the cloud.
"""

from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

COLUMN_RENAMES = {
    "VendorID": "vendor_id",
    "tpep_pickup_datetime": "pickup_at",
    "tpep_dropoff_datetime": "dropoff_at",
    "passenger_count": "passenger_count",
    "trip_distance": "trip_distance",
    "RatecodeID": "ratecode_id",
    "store_and_fwd_flag": "store_and_fwd_flag",
    "PULocationID": "pu_location_id",
    "DOLocationID": "do_location_id",
    "payment_type": "payment_type",
    "fare_amount": "fare_amount",
    "extra": "extra",
    "mta_tax": "mta_tax",
    "tip_amount": "tip_amount",
    "tolls_amount": "tolls_amount",
    "improvement_surcharge": "improvement_surcharge",
    "total_amount": "total_amount",
    "congestion_surcharge": "congestion_surcharge",
    "Airport_fee": "airport_fee",
}
INT_COLUMNS = ["vendor_id", "passenger_count", "ratecode_id", "pu_location_id", "do_location_id", "payment_type"]
METADATA_COLUMNS = ["_ingested_at", "_source_file", "_source_year", "_source_month"]

TRIP_COLUMNS = list(COLUMN_RENAMES.values())

DROP_REASON = "_drop_reason"
DUPLICATE_RULE = "duplicate"

RULE_ORDER = [
    "null_timestamp",
    "pickup_outside_file_month",
    "dropoff_before_pickup",
    "zero_or_negative_distance",
    "zero_or_negative_fare",
    DUPLICATE_RULE
]

def rules() -> list[tuple[str,Column]]:
    """Filter rules, in order. Each condition is True for a row that must be DROPPED.

    A function, not a module-level list: Spark Columns can only be built once a
    SparkSession exists, and this module is imported before that.
    A row breaking several rules is counted under the FIRST one (attribution, not result).
    Nulls are handled explicitly: in Spark, (null <= 0) is null, not True.
    """
    return [
        ("null_timestamp",F.col("pickup_at").isNull() | F.col("dropoff_at").isNull() ),
        (
            "pickup_outside_file_month", ((F.year("pickup_at") != F.col("_source_year")) | (F.month("pickup_at") != F.col("_source_month"))),
        ),
        ("dropoff_before_pickup", F.col("dropoff_at") < F.col("pickup_at")),
        ("zero_or_negative_distance", F.col("trip_distance").isNull() | (F.col("trip_distance") <= 0)),
        ("zero_or_negative_fare", F.col("fare_amount").isNull() | (F.col("fare_amount") <= 0)),
    ]

def standardise(bronze: DataFrame) -> DataFrame:
    """Rename to snake_case and cast code columns to int. Keep Metadata Columns"""
    renamed = [F.col(src).alias(dst) for src, dst in COLUMN_RENAMES.items()]
    df = bronze.select(*renamed, *METADATA_COLUMNS)
    for name in INT_COLUMNS:
        df = df.withColumn(name, F.col(name).cast("int"))
    return df

def flag_invalid_rows(df: DataFrame) -> DataFrame:
    first_match = F.coalesce(*[F.when(condition, F.lit(name)) for name,condition in rules()])
    return df.withColumn(DROP_REASON,first_match)

def remove_duplicates(df: DataFrame) -> DataFrame:
    return df.dropDuplicates(TRIP_COLUMNS)

def add_trip_durations(df: DataFrame) -> DataFrame:
    seconds = F.timestamp_diff("SECOND",F.col("pickup_at"), F.col("dropoff_at"))
    return df.withColumn("trip_duration_min",F.round(seconds / 60.0, 2))