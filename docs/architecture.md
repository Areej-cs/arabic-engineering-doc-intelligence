# Architecture Notes

Quick overview of how a document moves through the pipeline, mostly written
so I don't have to re-read all the code next time I come back to this.

## Pipeline

1. **Input** — a scanned image or photographed report comes in, either
   through `POST /api/v1/documents` (FastAPI) or the Streamlit uploader. The
   original file is saved through `src/app/storage/` — local disk in
   development, S3 in production (`STORAGE_BACKEND`).
2. **OCR** (`src/app/ocr/extractor.py`) — PDFs are rasterized to images first
   (`pdf2image` + Poppler), then every page goes through Tesseract with
   `ara+eng`. Grayscale + adaptive thresholding before OCR made a noticeable
   difference on the phone-photo samples I tested with; less so on clean
   scans.
3. **Classification** (`src/app/nlp/classifier.py`) — the OCR'd text is
   embedded with a frozen AraBERT encoder (mean-pooled, masked), then a
   small trainable head (`Linear -> ReLU -> Dropout -> Linear`) maps that
   embedding to `Urgent` / `Normal` / `Low`.
4. **Output** — the OCR text + priority are saved as a row in PostgreSQL
   (`documents` table, Alembic migrations), so reports can be listed,
   filtered by priority and counted (`/documents`, `/documents/stats`)
   instead of processed one at a time.

## Two ways to run the dashboard

- `STREAMLIT_MODE=local` — the dashboard runs OCR + AraBERT itself. No
  database, easiest for trying the project.
- `STREAMLIT_MODE=api` (docker-compose default) — the dashboard is a thin
  client of the API. Only the API process loads AraBERT, so there's one copy
  of the model in memory, and every upload is stored and searchable.

## Why the API runs OCR/AraBERT in a thread pool

Both are CPU-bound, blocking calls. Calling them directly inside an `async`
endpoint would freeze the event loop, so `/documents` uploads would block
health checks and list requests. `run_in_threadpool` keeps the API
responsive while a document is being processed.

## Why storage is behind an interface

`LocalStorage` and `S3Storage` share `save()` / `load()`. Tests and local
development need no AWS account, and production switches to S3 with one
environment variable. On EC2 the S3 client authenticates through the
instance's IAM role, so no access keys exist in the code or `.env`.

## Why a frozen encoder + a small head

Fine-tuning all of AraBERT needs more labeled data than I have — the
training set is currently synthetic/templated (see
`src/app/nlp/data_generator.py`), not real reports. Freezing the encoder and
only training the head keeps the parameter count small enough that it
doesn't just memorize the synthetic phrasing, and training the head takes
seconds on CPU instead of needing a GPU.

## Known limitations

- Training data is synthetic, so real-world accuracy on messier phrasing is
  still untested.
- OCR accuracy drops on skewed or low-contrast phone photos — preprocessing
  helps but doesn't fully fix it.
- Processing is synchronous per request; a large multi-page PDF keeps the
  request open until OCR finishes. A job queue (e.g. SQS + a worker) would
  be the next step for heavy loads.
