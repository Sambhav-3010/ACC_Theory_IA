import json
import sqlite3
from pathlib import Path
from typing import Any


def connect(path: str = "data/invoices.db") -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL, uploaded_at TEXT NOT NULL,
        invoice_number TEXT, vendor_name TEXT, invoice_date TEXT, subtotal REAL, tax_amount REAL,
        total_amount REAL, validation_status TEXT NOT NULL, validation_messages TEXT NOT NULL,
        source_type TEXT, cloud_object_key TEXT, extracted_text TEXT)""")
    conn.commit()
    return conn


def save_invoice(conn: sqlite3.Connection, record: dict[str, Any]) -> int:
    fields = ["filename", "uploaded_at", "invoice_number", "vendor_name", "invoice_date", "subtotal", "tax_amount", "total_amount", "validation_status", "validation_messages", "source_type", "cloud_object_key", "extracted_text"]
    values = [json.dumps(record["validation_messages"]) if f == "validation_messages" else record.get(f) for f in fields]
    cur = conn.execute(f"INSERT INTO invoices ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})", values)
    conn.commit()
    return int(cur.lastrowid)


def list_invoices(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = [dict(row) for row in conn.execute("SELECT * FROM invoices ORDER BY id DESC")]
    for row in rows:
        row["validation_messages"] = json.loads(row["validation_messages"])
    return rows
