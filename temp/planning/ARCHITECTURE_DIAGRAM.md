# Architecture diagram

The editable Excalidraw source is `architecture.excalidraw`. Import it at https://excalidraw.com using **Open**. It can then be exported as PNG, SVG, or PDF for the report and presentation.

```mermaid
flowchart LR
    U[User / Streamlit] --> R{Document route}
    R -->|digital PDF| P[PyMuPDF]
    R -->|scanned/image| O[Tesseract OCR]
    U --> S3[Amazon S3\nOriginal invoice]
    U --> T[Amazon Textract\nAnalyzeExpense + confidence]
    P --> V[Field normalization\nValidation + human review]
    O --> V
    T --> V
    V --> D[DynamoDB\nInvoiceRecords]
    V --> C[CloudWatch Logs]
    D --> H[History dashboard]
    I[IAM / AWS CLI profile] -.-> S3
    I -.-> T
    I -.-> D
    I -.-> C
```
