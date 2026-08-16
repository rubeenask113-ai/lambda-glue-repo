import boto3
import csv
import urllib.parse
import os

s3 = boto3.client("s3")
glue = boto3.client("glue")

REQUIRED_COLUMNS = ["city", "state", "country"]

# Get Glue job name from Lambda environment variable
GLUE_JOB_NAME = os.environ.get("GLUE_JOB_NAME")

# Output folder in the same S3 bucket
OUTPUT_PREFIX = "glue-output"


def lambda_handler(event, context):
    print("Event:", event)

    # 1. Get file details from S3 event
    record = event["Records"][0]

    bucket = record["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

    print(f"Processing file: s3://{bucket}/{key}")

    # 2. Read the CSV file from S3
    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )

    content = response["Body"].read().decode("utf-8").splitlines()

    reader = csv.reader(content)
    headers = [header.strip() for header in next(reader)]

    print("Headers:", headers)

    # 3. Validate required columns
    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in headers
    ]

    if missing_columns:
        raise Exception(
            f"Missing required columns: {missing_columns}"
        )

    print("Columns are valid")

    # 4. Check that Glue job name exists
    if not GLUE_JOB_NAME:
        raise Exception(
            "GLUE_JOB_NAME environment variable is not configured"
        )

    print(f"Starting Glue job: {GLUE_JOB_NAME}")

    # 5. Trigger Glue job with ALL required arguments
    glue_response = glue.start_job_run(
        JobName=GLUE_JOB_NAME,
        Arguments={
            "--input_bucket": bucket,
            "--input_key": key,
            "--output_bucket": bucket,
            "--output_prefix": OUTPUT_PREFIX,
            "--required_columns": ",".join(REQUIRED_COLUMNS)
        }
    )

    job_run_id = glue_response["JobRunId"]

    print(
        f"Glue job triggered successfully. "
        f"JobRunId: {job_run_id}"
    )

    return {
        "statusCode": 200,
        "body": {
            "message": "Glue job triggered successfully",
            "job_name": GLUE_JOB_NAME,
            "job_run_id": job_run_id,
            "input": f"s3://{bucket}/{key}",
            "output": f"s3://{bucket}/{OUTPUT_PREFIX}/"
        }
    }
