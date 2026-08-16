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
            "required_columns",
        ],
    )

    required_columns = [
        column.strip()
        for column in args["required_columns"].split(",")
        if column.strip()
    ]

    input_path = f"s3://{args['input_bucket']}/{args['input_key']}"

    output_base = (
        f"s3://{args['output_bucket']}/"
        f"{args['output_prefix'].rstrip('/')}"
    )

    # ------------------------------------------------------------
    # START GLUE
    # ------------------------------------------------------------

    sc = SparkContext()

    glue_context = GlueContext(sc)

    spark = glue_context.spark_session

    job = Job(glue_context)

    job.init(args["JOB_NAME"], args)


    # ------------------------------------------------------------
    # READ INPUT CSV
    # ------------------------------------------------------------

    print(f"Reading input from: {input_path}")

    df = (
        spark.read
        .option("header", "true")
        .option("inferSchema", "true")
        .csv(input_path)
    )

    print("Input columns:", df.columns)


    # ------------------------------------------------------------
    # VALIDATE REQUIRED COLUMNS
    # ------------------------------------------------------------

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    print("Required columns are present.")


    # ------------------------------------------------------------
    # CITY OUTPUT
    # ------------------------------------------------------------

    city_output = f"{output_base}/city"

    (
        df.select("city")
        .dropDuplicates()
        .write
        .mode("overwrite")
        .option("header", "true")
        .csv(city_output)
    )

    print(f"City output written to: {city_output}")


    # ------------------------------------------------------------
    # STATE OUTPUT
    # ------------------------------------------------------------

    state_output = f"{output_base}/state"

    (
        df.select("state")
        .dropDuplicates()
        .write
        .mode("overwrite")
        .option("header", "true")
        .csv(state_output)
    )

    print(f"State output written to: {state_output}")


    # ------------------------------------------------------------
    # COUNTRY OUTPUT
    # ------------------------------------------------------------

    country_output = f"{output_base}/country"

    (
        df.select("country")
        .dropDuplicates()
        .write
        .mode("overwrite")
        .option("header", "true")
        .csv(country_output)
    )

    print(f"Country output written to: {country_output}")


    # ------------------------------------------------------------
    # COMPLETE JOB
    # ------------------------------------------------------------

    job.commit()

    print("Glue job completed successfully.")


if __name__ == "__main__":
    main()
