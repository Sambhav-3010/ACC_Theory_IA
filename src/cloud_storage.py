import os
import time
from pathlib import Path


def _client(service: str):
    import boto3
    return boto3.client(service, region_name=os.getenv("AWS_REGION", "ap-south-1"))


def cloud_status():
    return [("Amazon S3", bool(os.getenv("S3_BUCKET_NAME", "").strip()), "Original invoice storage"), ("Amazon Textract", os.getenv("TEXTRACT_ENABLED", "false").lower() == "true", "Cloud invoice analysis"), ("Amazon DynamoDB", bool(os.getenv("DYNAMODB_TABLE_NAME", "").strip()), "Structured cloud records"), ("Amazon CloudWatch", bool(os.getenv("CLOUDWATCH_LOG_GROUP", "").strip()), "Processing event logs")]


def upload_to_s3(file_bytes: bytes, filename: str) -> str:
    bucket = os.getenv("S3_BUCKET_NAME", "").strip()
    if not bucket:
        return ""
    from botocore.exceptions import BotoCoreError, ClientError
    key = f"invoices/{Path(filename).name}"
    try:
        _client("s3").put_object(Bucket=bucket, Key=key, Body=file_bytes)
        return key
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"S3 upload failed: {exc}") from exc


def save_to_dynamodb(record: dict) -> str:
    table_name = os.getenv("DYNAMODB_TABLE_NAME", "").strip()
    if not table_name:
        return "DynamoDB skipped (table not configured)"
    from botocore.exceptions import BotoCoreError, ClientError
    try:
        _client("dynamodb").put_item(TableName=table_name, Item={"invoice_id":{"S":f"{record['invoice_number'] or 'unknown'}-{record['uploaded_at']}"},"filename":{"S":record["filename"]},"vendor_name":{"S":record.get("vendor_name","")},"invoice_date":{"S":record.get("invoice_date","")},"total_amount":{"N":str(record.get("total_amount") or 0)},"validation_status":{"S":record["validation_status"]},"s3_object_key":{"S":record.get("cloud_object_key","")}})
        return "DynamoDB record saved"
    except (BotoCoreError, ClientError) as exc:
        return f"DynamoDB failed: {exc}"


def log_processing_event(record: dict, status: str) -> str:
    group = os.getenv("CLOUDWATCH_LOG_GROUP", "").strip()
    if not group:
        return "CloudWatch skipped (log group not configured)"
    from botocore.exceptions import BotoCoreError, ClientError
    stream = os.getenv("CLOUDWATCH_LOG_STREAM", "invoice-processing")
    try:
        client = _client("logs")
        try:
            client.create_log_group(logGroupName=group)
        except client.exceptions.ResourceAlreadyExistsException:
            pass
        try:
            client.create_log_stream(logGroupName=group, logStreamName=stream)
        except client.exceptions.ResourceAlreadyExistsException:
            pass
        client.put_log_events(logGroupName=group, logStreamName=stream, logEvents=[{"timestamp":int(time.time()*1000),"message":f"status={status} filename={record['filename']} invoice_number={record.get('invoice_number','')}"}])
        return "CloudWatch event logged"
    except (BotoCoreError, ClientError) as exc:
        return f"CloudWatch failed: {exc}"
