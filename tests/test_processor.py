from src.processor import parse_invoice, validate_invoice


def test_parse_complete_invoice():
    data = parse_invoice("Vendor: Acme Supplies\nInvoice Number: INV-42\nInvoice Date: 2026-10-20\nSubtotal: 100.00\nTax: 18.00\nTotal: 118.00")
    assert data["invoice_number"] == "INV-42"
    assert data["vendor_name"] == "Acme Supplies"
    assert data["total_amount"] == 118.0
    assert validate_invoice(data) == []


def test_validation_flags_missing_and_inconsistent_values():
    data = parse_invoice("Vendor: Acme\nInvoice Date: 31/99/2026\nSubtotal: 100\nTax: 18\nTotal: 120")
    messages = validate_invoice(data)
    assert any("Invoice number" in message for message in messages)
    assert any("date" in message.lower() for message in messages)
    assert any("match" in message for message in messages)
