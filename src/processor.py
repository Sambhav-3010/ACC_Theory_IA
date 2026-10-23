from __future__ import annotations

import io
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz


FIELD_KEYS = ("invoice_number", "vendor_name", "invoice_date", "subtotal", "tax_amount", "total_amount")


def extract_text(file_bytes: bytes, filename: str, use_ocr: bool = True) -> tuple[str, str]:
    ext = Path(filename).suffix.lower()
    if ext not in {".pdf", ".png", ".jpg", ".jpeg"}:
        raise ValueError("Unsupported file type. Upload a PDF, PNG, JPG, or JPEG.")
    if ext == ".pdf":
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc).strip()
        if text:
            return text, "pdf-text"
        if not use_ocr:
            return "", "scanned-pdf"
    if not use_ocr:
        return "", "image"
    try:
        import pytesseract
        from PIL import Image
        if ext == ".pdf":
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            images = []
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                images.append(Image.open(io.BytesIO(pix.tobytes("png"))))
        else:
            images = [Image.open(io.BytesIO(file_bytes))]
        text = "\n".join(pytesseract.image_to_string(image) for image in images).strip()
        return text, "ocr"
    except ImportError as exc:
        raise RuntimeError("OCR requires pytesseract and Pillow.") from exc
    except Exception as exc:
        raise RuntimeError("OCR could not process this file. Install Tesseract and ensure it is on PATH.") from exc


def _first(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip(" :#\t")
    return ""


def _amount(value: str) -> float | None:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9.,-]", "", value).replace(",", "")
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def parse_invoice(text: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        "invoice_number": _first([r"invoice\s*(?:no|number|#)\s*[:\-]?\s*([^\n]+)"], text),
        "vendor_name": _first([r"(?:vendor|seller|supplier)\s*(?:name)?\s*[:\-]\s*([^\n]+)"], text),
        "invoice_date": _first([r"invoice\s*date\s*[:\-]?\s*([^\n]+)", r"date\s*[:\-]\s*([^\n]+)"], text),
        "subtotal": _amount(_first([r"^\s*sub\s*total\s*[:\-]?\s*([$₹€£]?\s*[\d,]+(?:\.\d{1,2})?)"], text)),
        "tax_amount": _amount(_first([r"^\s*(?:tax|gst|vat)\s*(?:amount)?\s*[:\-]?\s*([$₹€£]?\s*[\d,]+(?:\.\d{1,2})?)"], text)),
        "total_amount": _amount(_first([r"^\s*(?:grand\s*total|total\s*amount|total)\s*[:\-]?\s*([$₹€£]?\s*[\d,]+(?:\.\d{1,2})?)"], text)),
    }
    return data


def validate_invoice(data: dict[str, Any]) -> list[str]:
    messages: list[str] = []
    for key, label in (("invoice_number", "Invoice number"), ("vendor_name", "Vendor name"), ("invoice_date", "Invoice date"), ("total_amount", "Total amount")):
        if not data.get(key):
            messages.append(f"Missing required field: {label}.")
    if data.get("invoice_date"):
        valid = False
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                datetime.strptime(str(data["invoice_date"]).strip(), fmt)
                valid = True
                break
            except ValueError:
                pass
        if not valid:
            messages.append("Invoice date is not in a recognized format.")
    for key in ("subtotal", "tax_amount", "total_amount"):
        if data.get(key) is not None and data[key] < 0:
            messages.append(f"{key.replace('_', ' ').title()} cannot be negative.")
    if data.get("subtotal") is not None and data.get("tax_amount") is not None and data.get("total_amount") is not None:
        if abs(data["subtotal"] + data["tax_amount"] - data["total_amount"]) > 0.05:
            messages.append("Subtotal plus tax does not match total amount.")
    return messages
