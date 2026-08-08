# Lambda Glue Repository

This repository deploys an AWS pipeline with:
- S3 bucket for incoming CSV files
- Lambda function to validate required columns
- AWS Glue job to partition data by `city`, `state`, and `country`
- GitHub Actions workflow using OIDC authentication to AWS

## Architecture

1. File lands in S3 bucket
2. S3 triggers Lambda on object create
3. Lambda reads CSV header and checks required columns
4. Lambda starts Glue job when columns are valid
5. Glue job writes partitioned output and coalesced output files into S3

## Files created

- `.github/workflows/deploy.yml` - GitHub Actions workflow with AWS OIDC auth
- `cloudformation/template.yaml` - CloudFormation stack for bucket, Lambda, IAM, Glue job
- `lambda/handler.py` - Lambda function source
- `glue/job.py` - Glue ETL script

## Required GitHub secrets

Add these secrets to your repository settings:
- `AWS_OIDC_ROLE_ARN` - IAM role ARN that GitHub Actions can assume via OIDC
- `AWS_REGION` - AWS region to deploy into
- `CFN_STAGING_BUCKET` - existing S3 bucket for packaging code and Glue script

## AWS IAM role setup

The role referenced by `AWS_OIDC_ROLE_ARN` should trust GitHub Actions via OIDC. Example trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:YOUR_ORG/YOUR_REPO:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

## Deployment

1. Confirm `CFN_STAGING_BUCKET` exists and is writable.
2. Push to `main` or `develop` branch.
3. GitHub Actions will package `lambda/handler.py`, upload it and `glue/job.py` to the staging bucket, then deploy the CloudFormation stack.

## Notes

- The Lambda validates CSV headers using the first row.
- The Glue job partitions data by `city`, `state`, and `country` and also writes a coalesced output into `glue-output/final-output/`.
- The CloudFormation stack creates a fresh data S3 bucket and the Lambda is configured with an S3 object-created trigger.

## License

This project is licensed under the MIT License.
