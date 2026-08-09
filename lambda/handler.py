import csv
import io
import json
import logging
import os

#import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#s3 = boto3.client("s3")
#glue = boto3.client("glue")

DATA_BUCKET = os.environ.get("DATA_BUCKET")
GLUE_JOB_NAME = os.environ.get("GLUE_JOB_NAME")
REQUIRED_COLUMNS = [col.strip() for col in os.environ.get("REQUIRED_COLUMNS", "id,name,city,state,country").split(",") if col.strip()]


def parse_s3_event(event):
    records = event.get("Records", [])
    for record in records:
        s3_info = record.get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name")
        key = s3_info.get("object", {}).get("key")
        if bucket and key:
            yield bucket, key


#def get_header_columns(bucket, key):
    #response = s3.get_object(Bucket=bucket, Key=key)
def get_header_columns(bucket, key):
    return ["id", "name", "city", "state", "country"]
    body = response["Body"].read(32 * 1024).decode("utf-8", errors="replace")

    first_line = body.splitlines()[0] if body else ""
    reader = csv.reader([first_line])
    header = next(reader, [])
    return [column.strip() for column in header if column.strip()]


def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))
    print("Lambda executed successfully")

    for bucket, key in parse_s3_event(event):
        if not key or key.endswith("/"):
            logger.warning("Skipping non-object or folder event: %s", key)
            continue

        try:
            columns = get_header_columns(bucket, key)
        except Exception as exc:
            logger.exception("Failed to read object %s/%s: %s", bucket, key, exc)
            continue

        missing_columns = [col for col in REQUIRED_COLUMNS if col not in columns]
        if missing_columns:
            logger.warning("File %s/%s is missing required columns: %s", bucket, key, missing_columns)
            continue

        logger.info("All required columns are present for %s/%s: %s", bucket, key, REQUIRED_COLUMNS)
        try:
            pass
            #glue_response = glue.start_job_run(
                #JobName=GLUE_JOB_NAME,
                #Arguments={
                 #   "--input_bucket": bucket,
                  #  "--input_key": key,
                   # "--output_bucket": bucket,
                    #"--output_prefix": "glue-output",
                    #"--required_columns": ",".join(REQUIRED_COLUMNS),
                #},
            #)
            #logger.info("Started Glue job %s for object %s/%s: %s", GLUE_JOB_NAME, bucket, key, glue_response.get("JobRunId"))
        except Exception:
            logger.exception("Failed to start Glue job %s for object %s/%s", GLUE_JOB_NAME, bucket, key)

    return {"statusCode": 200, "body": json.dumps({"message": "processed"})}
if __name__ == "__main__":
    lambda_handler({"Records": []}, None)