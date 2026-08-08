import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext


def main():
    args = getResolvedOptions(
        sys.argv,
        ["JOB_NAME", "input_bucket", "input_key", "output_bucket", "output_prefix", "required_columns"],
    )

    required_columns = [column.strip() for column in args["required_columns"].split(",") if column.strip()]
    input_path = f"s3://{args['input_bucket']}/{args['input_key']}"
    output_base = f"s3://{args['output_bucket']}/{args['output_prefix'].rstrip('/')}"

    sc = SparkContext()
    glue_context = GlueContext(sc)
    spark = glue_context.spark_session
    job = Job(glue_context)
    job.init(args["JOB_NAME"], args)

    df = spark.read.option("header", "true").csv(input_path)
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns in Glue job input: {missing_columns}")

    selected_df = df.select(*required_columns)

    partition_output_path = f"{output_base}/partitioned"
    selected_df.write.mode("overwrite").partitionBy("city", "state", "country").option("header", "true").csv(partition_output_path)

    final_output_path = f"{output_base}/final-output"
    selected_df.coalesce(3).write.mode("overwrite").option("header", "true").csv(final_output_path)

    job.commit()


if __name__ == "__main__":
    main()
