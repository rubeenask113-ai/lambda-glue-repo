import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext


def main():

    args = getResolvedOptions(
        sys.argv,
        [
            "JOB_NAME",
            "input_bucket",
            "input_key",
            "output_bucket",
            "output_prefix",
            "required_columns"
        ]
    )

    required_columns = [
        column.strip()
        for column in args["required_columns"].split(",")
        if column.strip()
    ]

    input_path = (
        f"s3://{args['input_bucket']}/{args['input_key']}"
    )

    output_base = (
        f"s3://{args['output_bucket']}/"
        f"{args['output_prefix'].rstrip('/')}"
    )

    # Start Spark / Glue
    sc = SparkContext()
    glue_context = GlueContext(sc)
    spark = glue_context.spark_session

    job = Job(glue_context)

    job.init(args["JOB_NAME"], args)

    # Read CSV
    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(input_path)
    )

    print("Input columns:", df.columns)

    # Validate columns
    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Keep only required columns
    selected_df = df.select(*required_columns)

    # --------------------------------------------------
    # 1. PARTITIONED OUTPUT
    # --------------------------------------------------

    partition_output_path = (
        f"{output_base}/partitioned"
    )

    (
        selected_df
        .write
        .mode("overwrite")
        .partitionBy("city", "state", "country")
        .option("header", "true")
        .csv(partition_output_path)
    )

    print(
        f"Partitioned output written to: "
        f"{partition_output_path}"
    )

    # --------------------------------------------------
    # 2. THREE SEPARATE OUTPUT FILES
    # --------------------------------------------------

    # CITY
    city_df = selected_df.select("city").distinct()

    city_df.coalesce(1).write \
        .mode("overwrite") \
        .option("header", "true") \
        .csv(f"{output_base}/city")

    # STATE
    state_df = selected_df.select("state").distinct()

    state_df.coalesce(1).write \
        .mode("overwrite") \
        .option("header", "true") \
        .csv(f"{output_base}/state")

    # COUNTRY
    country_df = selected_df.select("country").distinct()

    country_df.coalesce(1).write \
        .mode("overwrite") \
        .option("header", "true") \
        .csv(f"{output_base}/country")

    print(
        f"Three outputs written under: {output_base}"
    )

    job.commit()


if __name__ == "__main__":
    main()
