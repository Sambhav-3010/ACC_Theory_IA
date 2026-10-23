import os
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.cloud_storage import cloud_status, log_processing_event, save_to_dynamodb, upload_to_s3
from src.database import connect, list_invoices, save_invoice
from src.processor import extract_text, parse_invoice, validate_invoice
from src.textract_service import analyze_expense

load_dotenv(".env.aws.generated", override=True)
load_dotenv(override=False)
st.set_page_config(page_title="InvoiceFlow IDP", page_icon="📄", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--ink:#e7eefc;--muted:#9fb1cf;--glass:rgba(18,31,58,.68);--line:rgba(148,163,184,.20);--blue:#67a4ff;--cyan:#62e6e0}
.stApp{background:radial-gradient(circle at 15% 0%,#203b70 0%,transparent 34%),radial-gradient(circle at 100% 20%,#123c5c 0%,transparent 30%),#081326;color:var(--ink);font-family:'DM Sans',sans-serif}
.stApp:before{content:'';position:fixed;inset:0;pointer-events:none;background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);background-size:42px 42px;mask-image:linear-gradient(to bottom,black,transparent 85%)}
.block-container{padding-top:2rem;max-width:1180px;position:relative}.hero{background:linear-gradient(135deg,rgba(36,78,150,.78),rgba(15,125,145,.42));border:1px solid rgba(160,210,255,.30);box-shadow:0 24px 70px rgba(0,0,0,.28),inset 0 1px rgba(255,255,255,.18);backdrop-filter:blur(20px);padding:2.3rem 2.5rem;border-radius:26px;color:white;margin-bottom:1.5rem;position:relative;overflow:hidden}.hero:after{content:'';position:absolute;width:240px;height:240px;border-radius:50%;right:-60px;top:-100px;background:rgba(98,230,224,.18);filter:blur(5px)}.hero h1{font-family:'Space Grotesk',sans-serif;font-size:2.5rem;margin:0 0 .4rem;color:white;letter-spacing:-.04em;position:relative;z-index:1}.hero p{margin:0;color:#d9e9ff;font-size:1.08rem;position:relative;z-index:1}.section-label{text-transform:uppercase;letter-spacing:.14em;font-size:.72rem;font-weight:700;color:var(--muted);margin:1.5rem 0 .65rem}.cloud-card{border:1px solid var(--line);background:var(--glass);box-shadow:0 18px 42px rgba(0,0,0,.18),inset 0 1px rgba(255,255,255,.10);backdrop-filter:blur(18px);border-radius:18px;padding:1.15rem 1.25rem;margin-bottom:.6rem}.cloud-card h3{font-family:'Space Grotesk',sans-serif;color:#fff;margin-top:0}.cloud-card p{color:var(--muted)}
[data-testid="stSidebar"]{background:rgba(5,14,30,.76);border-right:1px solid var(--line);backdrop-filter:blur(22px)}[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{font-family:'Space Grotesk',sans-serif;color:#fff}h1,h2,h3{font-family:'Space Grotesk',sans-serif;color:#f7fbff}p,small,span,label{color:var(--ink)}.stCaption{color:var(--muted)}
[data-testid="stFileUploader"]{background:rgba(23,39,70,.54);border:1px dashed rgba(103,164,255,.65);border-radius:18px;padding:.8rem;backdrop-filter:blur(14px)}[data-testid="stFileUploader"] section{border:0;background:transparent}.stTextInput>div>div,.stTextArea>div>div{background:rgba(15,29,55,.72);border:1px solid var(--line);border-radius:12px}.stTextInput input{color:#fff}.stButton>button{border:1px solid rgba(103,164,255,.45);border-radius:12px;background:linear-gradient(135deg,#326bd2,#178f9b);color:#fff;font-weight:700;box-shadow:0 10px 24px rgba(23,116,177,.25);transition:.2s}.stButton>button:hover{border-color:var(--cyan);transform:translateY(-1px);box-shadow:0 14px 30px rgba(23,116,177,.35)}.stAlert{border-radius:14px;background:rgba(20,37,68,.72);border:1px solid var(--line)}[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden}
</style>
""", unsafe_allow_html=True)


def _number(value: str):
    try:
        return float(value.replace(",", "").replace("₹", "").replace("$", "").strip()) if value.strip() else None
    except ValueError:
        return None


conn = connect()
st.markdown('<div class="hero"><div style="text-transform:uppercase;letter-spacing:.18em;font-size:.72rem;color:#a9eaff;margin-bottom:.6rem">INTELLIGENT DOCUMENT PROCESSING</div><h1>📄 InvoiceFlow</h1><p>Turn unstructured invoices into validated, searchable records — with a transparent cloud workflow.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Workspace")
    page = st.radio("Go to", ["Process invoice", "Invoice history", "Cloud architecture"], label_visibility="collapsed")
    st.divider()
    st.markdown("### Cloud services")
    for name, configured, detail in cloud_status():
        icon = "🟢" if configured else "⚪"
        st.markdown(f"{icon} **{name}**  \n<small>{detail}</small>", unsafe_allow_html=True)
    st.caption("SQLite remains available as a local development fallback.")

if page == "Cloud architecture":
    st.subheader("Four AWS services, one complete invoice workflow")
    st.caption("Cloud services activate when their environment variables are configured.")
    cols = st.columns(4)
    cards = [("Amazon S3", "Original files", "Private invoice object storage."), ("Amazon Textract", "AI extraction", "Invoice fields, line items, confidence."), ("DynamoDB", "Structured records", "Cloud invoice data and status."), ("CloudWatch", "Observability", "Processing success/failure events.")]
    for col, (service, role, detail) in zip(cols, cards):
        with col:
            st.markdown(f'<div class="cloud-card"><h3>{service}</h3><b>{role}</b><p>{detail}</p></div>', unsafe_allow_html=True)
    st.info("The app can use Amazon Textract for cloud AI extraction, while local PyMuPDF/Tesseract remains the fallback path. S3, DynamoDB, and CloudWatch complete the storage and monitoring workflow.")
    st.graphviz_chart('''digraph { graph [bgcolor="transparent", rankdir=LR, pad="0.2"]; node [shape=box, style="rounded,filled", fontname="Arial", color="#67a4ff", fontcolor="white", fillcolor="#162d58"]; edge [color="#62e6e0", fontcolor="white"]; User [label="User\nStreamlit"]; S3 [label="Amazon S3\nOriginal invoice"]; Textract [label="Amazon Textract\nAnalyzeExpense"]; Local [label="Local fallback\nPyMuPDF / Tesseract"]; Validate [label="Validation +\nhuman review"]; DDB [label="DynamoDB\nStructured record"]; CW [label="CloudWatch\nProcessing logs"]; User -> S3 [label="store original"]; User -> Textract [label="cloud analysis"]; User -> Local [label="offline fallback"]; S3 -> Textract [style=dashed, label="S3 object option"]; Textract -> Validate; Local -> Validate; Validate -> DDB [label="save"]; Validate -> CW [label="event"]; }''')
    st.code("Upload → S3 → Textract AnalyzeExpense → validation/review → DynamoDB + CloudWatch", language="text")

elif page == "Process invoice":
    st.subheader("Process a new invoice")
    st.write("Upload a synthetic invoice, review the extracted fields, correct anything necessary, and save the record.")
    uploaded = st.file_uploader("Choose a PDF or image", type=["pdf", "png", "jpg", "jpeg"], help="Try the sample files in sample_invoices after exporting them to PDF.")
    use_ocr = st.toggle("Enable OCR fallback", value=True, help="Needed for scanned PDFs and images. Tesseract must be installed.")
    use_textract = st.toggle("Use Amazon Textract cloud AI", value=os.getenv("TEXTRACT_ENABLED", "false").lower() == "true", help="Textract extracts invoice fields using AWS machine learning. Requires textract:AnalyzeExpense permission.")
    if uploaded:
        file_bytes = uploaded.getvalue()
        try:
            with st.spinner("Reading and analyzing invoice..."):
                text, source_type = extract_text(file_bytes, uploaded.name, use_ocr=use_ocr)
                fields = parse_invoice(text)
                textract_confidence = None
                textract_line_items = 0
                textract_analysis = None
                if use_textract:
                    try:
                        textract_fields, textract_confidence, textract_line_items, textract_analysis = analyze_expense(file_bytes)
                        fields = {**fields, **textract_fields}
                        source_type = "amazon-textract"
                    except Exception as exc:
                        st.warning(f"Textract unavailable; using local extraction instead: {exc}")
                messages = validate_invoice(fields)
            st.success(f"Processed using **{source_type}**")
            if source_type == "amazon-textract":
                st.caption(f"Amazon Textract confidence: {textract_confidence or 'not returned'}% · line items detected: {textract_line_items}")
                with st.expander("View Amazon Textract analysis", expanded=True):
                    analysis_cols = st.columns(2)
                    with analysis_cols[0]:
                        st.metric("Average confidence", f"{textract_confidence or '—'}%")
                    with analysis_cols[1]:
                        st.metric("Line items", textract_line_items)
                    st.markdown("**Normalized summary fields returned by Textract**")
                    st.dataframe(textract_analysis["summary_fields"], use_container_width=True, hide_index=True)
                    if textract_analysis["line_items"]:
                        st.markdown("**Line-item analysis**")
                        st.dataframe(textract_analysis["line_items"], use_container_width=True, hide_index=True)
                    with st.expander("Raw AnalyzeExpense JSON"):
                        st.json(textract_analysis["raw_response"])
            st.markdown('<div class="section-label">Review extracted information</div>', unsafe_allow_html=True)
            edited = {}
            labels = {"invoice_number":"Invoice number","vendor_name":"Vendor name","invoice_date":"Invoice date","subtotal":"Subtotal","tax_amount":"Tax amount","total_amount":"Total amount"}
            columns = st.columns(3)
            for index, (key, label) in enumerate(labels.items()):
                with columns[index % 3]:
                    value = fields.get(key)
                    edited[key] = st.text_input(label, "" if value is None else str(value), key=f"edit_{key}")
            if messages:
                st.warning("**Needs review**\n\n" + "\n".join(f"- {message}" for message in messages))
            else:
                st.success("All MVP validation checks passed.")
            with st.expander("View extracted text"):
                st.text(text or "No text extracted")
            if st.button("Save invoice", type="primary", use_container_width=True):
                edited_for_validation = {**edited, "subtotal": _number(edited["subtotal"]), "tax_amount": _number(edited["tax_amount"]), "total_amount": _number(edited["total_amount"])}
                messages = validate_invoice(edited_for_validation)
                Path("data/uploads").mkdir(parents=True, exist_ok=True)
                safe_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{Path(uploaded.name).name}"
                Path("data/uploads", safe_name).write_bytes(file_bytes)
                record = {**edited_for_validation, "filename": uploaded.name, "uploaded_at": datetime.now(timezone.utc).isoformat(), "validation_status": "passed" if not messages else "needs_review", "validation_messages": messages, "source_type": source_type, "cloud_object_key": "", "extracted_text": text}
                cloud_messages = []
                try:
                    record["cloud_object_key"] = upload_to_s3(file_bytes, safe_name)
                    if record["cloud_object_key"]: cloud_messages.append("S3 upload complete")
                except Exception as exc:
                    cloud_messages.append(f"S3 failed: {exc}")
                try:
                    cloud_messages.append(save_to_dynamodb(record))
                except Exception as exc:
                    cloud_messages.append(f"DynamoDB failed: {exc}")
                try:
                    cloud_messages.append(log_processing_event(record, "success"))
                except Exception as exc:
                    cloud_messages.append(f"CloudWatch failed: {exc}")
                invoice_id = save_invoice(conn, record)
                st.success(f"Invoice #{invoice_id} saved locally.")
                for message in cloud_messages:
                    if message and "failed" in message.lower(): st.warning(message)
                    elif message: st.info(message)
        except (ValueError, RuntimeError) as exc:
            st.error(str(exc))
else:
    st.subheader("Invoice history")
    rows = list_invoices(conn)
    if rows:
        st.metric("Processed invoices", len(rows))
        st.dataframe([{k: row[k] for k in ("id","filename","invoice_number","vendor_name","invoice_date","total_amount","validation_status","cloud_object_key")} for row in rows], use_container_width=True, hide_index=True)
    else:
        st.info("No invoice records yet. Process your first invoice from the sidebar.")
