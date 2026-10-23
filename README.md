# Invoice IDP

## Run locally

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
pytest
streamlit run app.py
```

Copy `.env.example` to `.env` for optional AWS S3. Set `S3_BUCKET_NAME`, `AWS_REGION`, and credentials through a safe local mechanism. The bucket should be private and use least-privilege `s3:PutObject` access. Do not use real invoices.

Tesseract is optional for digital PDFs. For scanned documents, install the Tesseract executable separately and ensure `tesseract.exe` is on PATH. The app remains useful in local mode if OCR is unavailable.

## AWS services used

The cloud architecture uses four AWS services:

1. **Amazon S3** stores original uploaded invoice files.
2. **Amazon Textract** performs cloud-based invoice analysis through `AnalyzeExpense`.
3. **Amazon DynamoDB** stores extracted invoice fields and validation status.
4. **Amazon CloudWatch Logs** records processing events.

To enable them, create a private S3 bucket, a DynamoDB table with partition key `invoice_id` (String), and a CloudWatch log group. Copy `.env.example` to `.env` and set the names. Configure AWS credentials using the AWS CLI/profile or environment variables; never commit credentials.

```text
S3_BUCKET_NAME=your-private-bucket
DYNAMODB_TABLE_NAME=InvoiceRecords
CLOUDWATCH_LOG_GROUP=/invoice-idp/processing
CLOUDWATCH_LOG_STREAM=invoice-processing
TEXTRACT_ENABLED=true
```

If any cloud setting is blank, that service is skipped and the local SQLite workflow still works. The Cloud architecture page in the app shows which services are configured.

Textract requires the AWS identity used by Boto3 to have `textract:AnalyzeExpense`. The app labels the source as `amazon-textract` and shows average returned confidence and detected line-item count. If Textract fails, the app falls back to local PyMuPDF/Tesseract extraction so the demonstration remains usable.
