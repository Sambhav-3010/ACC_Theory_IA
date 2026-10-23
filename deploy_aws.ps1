$ErrorActionPreference = "Stop"

function Test-AwsResourceCommand {
    param([string[]]$Arguments)
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & aws @Arguments 2>$null | Out-Null
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousPreference
    return $exitCode
}

Write-Host "Checking AWS identity..." -ForegroundColor Cyan
$identity = aws sts get-caller-identity --output json | ConvertFrom-Json
$accountId = $identity.Account
$region = aws configure get region
if ([string]::IsNullOrWhiteSpace($region)) { $region = "ap-south-1" }
$bucket = "invoice-idp-$accountId-$region"
$table = "InvoiceRecords"
$logGroup = "/invoice-idp/processing"
$logStream = "invoice-processing"

Write-Host "Account: $accountId | Region: $region" -ForegroundColor Green
Write-Host "S3 bucket: $bucket"

Write-Host "Checking/creating S3 bucket..." -ForegroundColor Cyan
$bucketCheck = Test-AwsResourceCommand @("s3api", "head-bucket", "--bucket", $bucket)
if ($bucketCheck -ne 0) {
    if ($region -eq "us-east-1") {
        aws s3api create-bucket --bucket $bucket --region $region | Out-Null
    } else {
        aws s3api create-bucket --bucket $bucket --region $region --create-bucket-configuration LocationConstraint=$region | Out-Null
    }
}
aws s3api put-public-access-block --bucket $bucket --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
$encryptionFile = Join-Path (Get-Location) ".aws-s3-encryption.json"
'{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' | Set-Content -Path $encryptionFile -Encoding ASCII -NoNewline
aws s3api put-bucket-encryption --bucket $bucket --server-side-encryption-configuration "file://$encryptionFile"
if ($LASTEXITCODE -ne 0) { Remove-Item -LiteralPath $encryptionFile -Force -ErrorAction SilentlyContinue; throw "S3 encryption configuration failed." }
Remove-Item -LiteralPath $encryptionFile -Force -ErrorAction SilentlyContinue

Write-Host "Checking/creating DynamoDB table..." -ForegroundColor Cyan
$tableCheck = Test-AwsResourceCommand @("dynamodb", "describe-table", "--table-name", $table, "--region", $region)
if ($tableCheck -ne 0) {
    aws dynamodb create-table --table-name $table --attribute-definitions AttributeName=invoice_id,AttributeType=S --key-schema AttributeName=invoice_id,KeyType=HASH --billing-mode PAY_PER_REQUEST --region $region | Out-Null
    aws dynamodb wait table-exists --table-name $table --region $region
}

Write-Host "Checking/creating CloudWatch log group and stream..." -ForegroundColor Cyan
Test-AwsResourceCommand @("logs", "create-log-group", "--log-group-name", $logGroup, "--region", $region) | Out-Null
Test-AwsResourceCommand @("logs", "create-log-stream", "--log-group-name", $logGroup, "--log-stream-name", $logStream, "--region", $region) | Out-Null

@"
AWS_REGION=$region
TEXTRACT_ENABLED=true
S3_BUCKET_NAME=$bucket
DYNAMODB_TABLE_NAME=$table
CLOUDWATCH_LOG_GROUP=$logGroup
CLOUDWATCH_LOG_STREAM=$logStream
"@ | Set-Content -Path ".env.aws.generated" -Encoding UTF8

Write-Host "" 
Write-Host "AWS resources are ready." -ForegroundColor Green
Write-Host "Generated configuration: .env.aws.generated" -ForegroundColor Green
Write-Host "No AWS secret keys were written to the project." -ForegroundColor Yellow
Write-Host "The app will use the AWS CLI default profile for credentials." -ForegroundColor Yellow
