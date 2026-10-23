# Project Plan

## Dependency order

1. Setup and sample documents
2. Core extraction
3. Field parsing and validation
4. SQLite storage
5. Streamlit interface
6. S3 integration
7. Testing and presentation

## Phase 1 — Setup

**Goal:** Reproducible Python environment. **Tasks:** create a virtual environment, install `requirements.txt`, copy `.env.example`, run tests, and initialize Git. **Files:** `requirements.txt`, `.env.example`, `.gitignore`. **Done when:** `pytest` passes and `streamlit run app.py` starts.

## Phase 2 — Samples and extraction

**Goal:** Prove digital PDF and optional OCR paths. Use synthetic invoices created by the team or public sample documents with no private data. Test a selectable-text PDF, a scanned image, and an unreadable/unsupported file. **Files:** `src/processor.py`, `tests/test_processor.py`. **Done when:** text extraction returns text for the digital sample and clearly reports missing Tesseract for OCR.

## Phase 3 — Parsing and validation

**Goal:** Convert text into fields and explain warnings. Test complete, missing-date, invalid-date, and inconsistent-total cases. **Files:** `src/processor.py`, `tests/test_processor.py`. **Done when:** expected fields and warnings are deterministic.

## Phase 4 — Persistence

**Goal:** Save and retrieve records. **Files:** `src/database.py`, `tests/test_database.py`. **Done when:** an in-memory/temp SQLite database can insert and list a record.

## Phase 5 — UI

**Goal:** Demonstrable upload, review, save, and history screens. **File:** `app.py`. **Done when:** a teammate can process a digital PDF without editing code.

## Phase 6 — Cloud component

**Goal:** Upload original files to private S3 using environment variables. **Files:** `src/cloud_storage.py`, `.env.example`, `README.md`. **Done when:** configured upload returns an object key and the UI displays success; unconfigured mode explains how to enable it without crashing.

## Phase 7 — Final verification

Run all tests, process two or three synthetic invoices, show one validation warning, retrieve history, and capture the S3 upload. Record limitations honestly.

## Folder structure

```text
app.py
requirements.txt
.env.example
.gitignore
README.md
PROJECT_SPECIFICATION.md
PROJECT_PLAN.md
src/
  __init__.py
  processor.py
  database.py
  cloud_storage.py
tests/
  test_processor.py
  test_database.py
data/uploads/.gitkeep
```

## Environment and Git workflow

Windows: `py -3.12 -m venv .venv`, `.venv\\Scripts\\Activate.ps1`, `python -m pip install -r requirements.txt`, then `streamlit run app.py`. Keep secrets in `.env`; never commit it. Use small branches/commits such as `feat/extraction`, review before merging, and push only source/config templates.

## Testing checklist

- [ ] Digital PDF extracts text.
- [ ] Image/scanned PDF uses OCR when installed.
- [ ] Missing required field produces a warning.
- [ ] Invalid date is reported.
- [ ] Inconsistent totals are reported.
- [ ] Unsupported extension is rejected.
- [ ] Unreadable file produces a friendly error.
- [ ] Repeated uploads remain separate records and do not overwrite files.
- [ ] SQLite save/retrieval works.
- [ ] S3 success and S3 failure are both handled.

## Debugging guide

If PDF text is empty, the document is probably scanned; install Tesseract and ensure it is on PATH. If OCR fails, verify `pytesseract.get_tesseract_version()`. If S3 fails, check region, bucket name, credentials, IAM permission, and network; continue with local mode for development. If parsing misses a field, inspect the extracted text in the UI and add a small label pattern with a regression test.

## Acceptance checklist

- [ ] MVP features are implemented and demonstrated.
- [ ] Cloud role is explained as S3 object storage, not exaggerated as autoscaling.
- [ ] No real confidential invoices or secrets are included.
- [ ] Tests pass on the presentation machine.
- [ ] Report includes architecture, workflow, cloud rationale, limitations, and screenshots.

## 7–8 minute video script

0:00–0:45 problem and objectives; 0:45–1:30 architecture/cloud role; 1:30–3:00 upload a digital PDF and review fields; 3:00–4:00 show validation warning/edit; 4:00–5:00 save and retrieve history; 5:00–6:00 show OCR sample or explain fallback; 6:00–7:00 show S3 object/status; 7:00–7:45 limitations, scalability as future work, and conclusion.

## Report outline

Abstract; problem statement; objectives; related concepts; requirements; architecture; implementation; extraction/OCR; validation; database and S3; test cases/results; screenshots; limitations; future work; conclusion; references.

## Allocation and stretch goals

Samiksha: UI and video coordination. Sambhav: processor, parsing, validation. Sahil: SQLite, S3, tests/report integration. Everyone reviews and rehearses. Stretch goals only after MVP: duplicate detection by file hash, CSV export, confidence indicators, cloud deployment, or a provider document-AI API.

## Requirements traceability

| Requirement | Phase | Component | Test | Status |
|---|---|---|---|---|
| Upload PDF/image | 5 | `app.py` | UI upload | Planned |
| Digital PDF text | 2 | `src/processor.py` | processor test | Planned |
| OCR fallback | 2 | `src/processor.py` | OCR/manual test | Planned |
| Field extraction | 3 | `src/processor.py` | parser tests | Planned |
| Validation | 3 | `src/processor.py` | warning tests | Planned |
| Save/retrieve | 4 | `src/database.py` | database tests | Planned |
| Cloud storage | 6 | `src/cloud_storage.py` | mocked/configured upload | Planned |
| Demonstration | 7 | all | acceptance checklist | Planned |
