import boto3
import csv

s3 = boto3.client('s3')
glue = boto3.client('glue')

REQUIRED_COLUMNS = ['city', 'state', 'country']

def lambda_handler(event, context):
    print("Event:", event)

    # 1. Get file details from S3 event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    print(f"Processing file: {key}")

    # 2. Read file
    response = s3.get_object(Bucket=bucket, Key=key)
    content = response['Body'].read().decode('utf-8').splitlines()

    reader = csv.reader(content)
    headers = next(reader)

    print("Headers:", headers)

    # 3. Validate columns
    if not all(col in headers for col in REQUIRED_COLUMNS):
        raise Exception("Missing required columns")

    print("Columns are valid")

    # 4. Trigger Glue job
    glue.start_job_run(
        JobName='your-glue-job-name',
        Arguments={
            '--input_path': f's3://{bucket}/{key}'
        }
    )

    print("Glue job triggered")

    return "Success"