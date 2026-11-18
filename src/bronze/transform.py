from pyspark.sql import DataFrame
from pyspark.sql import functions as F

PARTITION_COLUMNS = ["_source_year","_source_month"]

def add_ingestion_metadata(df: DataFrame, source_file: str, year: int, month: int) -> DataFrame:
    return (
        df.withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file",F.lit(source_file))
        .withColumn("_source_year",F.lit(year))
        .withColumn("_source_month", F.lit(month))
    )

def month_predicate(year: int, month: int) -> str:
    return f"_source_year = {year} AND _source_month = {month}"