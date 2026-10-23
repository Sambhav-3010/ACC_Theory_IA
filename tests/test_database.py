from src.database import connect, list_invoices, save_invoice


def test_save_and_list_invoice():
    conn = connect(":memory:")
    save_invoice(conn, {"filename": "a.pdf", "uploaded_at": "now", "invoice_number": "1", "vendor_name": "A", "invoice_date": "2026-10-20", "subtotal": 1.0, "tax_amount": 0.18, "total_amount": 1.18, "validation_status": "passed", "validation_messages": [], "source_type": "pdf-text", "cloud_object_key": "", "extracted_text": "text"})
    rows = list_invoices(conn)
    assert len(rows) == 1
    assert rows[0]["invoice_number"] == "1"
