from __future__ import annotations

import os
import re
from typing import Any


FIELD_MAP = {"INVOICE_RECEIPT_ID":"invoice_number", "INVOICE_RECEIPT_DATE":"invoice_date", "VENDOR_NAME":"vendor_name", "SUBTOTAL":"subtotal", "TAX":"tax_amount", "TOTAL":"total_amount"}


def _amount(value: str) -> float | None:
    cleaned = re.sub(r"[^0-9.,-]", "", value or "").replace(",", "")
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def analyze_expense(file_bytes: bytes) -> tuple[dict[str, Any], float | None, int, dict[str, Any]]:
    """Analyze one invoice with Textract AnalyzeExpense and normalize key fields."""
    import boto3

    client = boto3.client("textract", region_name=os.getenv("AWS_REGION", "ap-south-1"))
    response = client.analyze_expense(Document={"Bytes": file_bytes})
    fields: dict[str, Any] = {}
    confidences: list[float] = []
    line_item_count = 0
    summary_rows: list[dict[str, Any]] = []
    line_item_rows: list[dict[str, Any]] = []
    for document in response.get("ExpenseDocuments", []):
        for summary in document.get("SummaryFields", []):
            field_type = summary.get("Type", {}).get("Text", "")
            value = summary.get("ValueDetection", {}).get("Text", "").strip()
            confidence = summary.get("ValueDetection", {}).get("Confidence")
            summary_rows.append({"Type": field_type, "Label": summary.get("LabelDetection", {}).get("Text", ""), "Value": value, "Confidence": round(float(confidence), 1) if confidence is not None else None})
            target = FIELD_MAP.get(field_type)
            if target and value:
                fields[target] = _amount(value) if target in {"subtotal", "tax_amount", "total_amount"} else value
            for detection in (summary.get("Type", {}), summary.get("ValueDetection", {})):
                if detection.get("Confidence") is not None:
                    confidences.append(float(detection["Confidence"]))
        for group in document.get("LineItemGroups", []):
            for line_item in group.get("LineItems", []):
                line_item_count += 1
                values = {}
                for item_field in line_item.get("LineItemExpenseFields", []):
                    item_type = item_field.get("Type", {}).get("Text", "")
                    item_value = item_field.get("ValueDetection", {}).get("Text", "")
                    if item_type or item_value:
                        values[item_type or "VALUE"] = item_value
                line_item_rows.append(values)
    confidence = round(sum(confidences) / len(confidences), 1) if confidences else None
    return fields, confidence, line_item_count, {"summary_fields": summary_rows, "line_items": line_item_rows, "raw_response": response}
