import boto3
import csv
import os
import urllib.parse

s3 = boto3.client("s3")
glue = boto3.client("glue")

REQUIRED_COLUMNS = [
    column.strip()
    for column in os.environ.get(
        "REQUIRED_COLUMNS",
        "city,state,country"
    ).split(",")
    if column.strip()
]

GLUE_JOB_NAME = os.environ["GLUE_JOB_NAME"]


def lambda_handler(event, context):

    print("Event:", event)

    # 1. Get file details from S3 event
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(
        event["Records"][0]["s3"]["object"]["key"]
    )

    print(f"Processing file: s3://{bucket}/{key}")

    # 2. Read file from S3
    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )

    content = response["Body"].read().decode("utf-8").splitlines()

    reader = csv.reader(content)
    headers = next(reader)

    print("Headers:", headers)
    print("Required columns:", REQUIRED_COLUMNS)

    # 3. Validate required columns
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in headers
    ]

    if missing_columns:
        raise Exception(
            f"Missing required columns: {missing_columns}"
        )

    print("Columns are valid")

    # 4. Trigger Glue job
    response = glue.start_job_run(
        JobName=GLUE_JOB_NAME,
        Arguments={
            "--input_bucket": bucket,
            "--input_key": key,
        }
    )

    print(
        f"Glue job triggered successfully. "
        f"Run ID: {response['JobRunId']}"
    )

    return {
        "statusCode": 200,
        "message": "Glue job triggered successfully",
        "jobRunId": response["JobRunId"],
        "input": f"s3://{bucket}/{key}"
    }
