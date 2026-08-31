# Arabic Engineering Document Intelligence System

An OCR + NLP system for reading Arabic industrial maintenance and safety reports, extracting
the information they contain, and automatically classifying them by priority.

Maintenance teams in Arabic-speaking industrial environments generate large volumes of
scanned reports and photographed forms — equipment inspection notes, safety observations,
incident logs — that are slow to review manually and hard to search or aggregate. This
project turns those documents into structured, classified text: it reads mixed Arabic/English
text out of scanned images and PDFs, then uses a fine-tuned Arabic language model to flag how
urgent each report is (`Urgent` / `Normal` / `Low`), so teams can triage a backlog of reports
without reading every one by hand.

## Features

- **OCR extraction** — pulls mixed Arabic/English text out of images and PDFs using
  Tesseract, with image preprocessing (grayscale + adaptive thresholding) to improve accuracy
  on scanned documents.
- **Report classification** — classifies report text into `Urgent`, `Normal`, or `Low`
  priority using a lightweight classification head trained on top of frozen AraBERT sentence
  embeddings.
- **Interactive dashboard** — a single-page Streamlit app to upload a report and see its
  extracted text and priority classification directly.

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| OCR | Tesseract (with optional AWS Textract / EasyOCR support) |
| NLP | AraBERT (`aubmindlab/bert-base-arabertv02`) |
| Dashboard | Streamlit |
| Database | PostgreSQL |
| Storage / Infrastructure | AWS (S3, etc.) |

## Project Structure

```
arabic-engineering-doc-intelligence/
├── src/app/                # Application code
│   ├── ocr/                 # OCR engine and image processing
│   ├── nlp/                 # AraBERT classification and information extraction
│   └── utils/                # Shared utilities
├── app/                       # Streamlit dashboard (user interface)
│   └── main.py
├── data/                      # Data (raw / processed / annotated / samples)
├── saved_models/               # Trained model weights (not committed to git)
├── deployment/aws/             # Infrastructure (Terraform, deployment scripts)
├── tests/                     # Tests
├── docs/                       # Documentation
├── scripts/                    # General-purpose helper scripts
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── .env.example
```

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements-dev.txt
copy .env.example .env
```

OCR requires a local Tesseract installation (with the Arabic `ara` language data) and Poppler
(for PDF support). Set `TESSERACT_CMD`, `TESSDATA_PREFIX`, and `POPPLER_PATH` in `.env` if
they aren't discoverable on your system `PATH`.

Classification requires the AraBERT model weights. Point `ARABERT_MODEL_NAME` at the
Hugging Face model ID (default `aubmindlab/bert-base-arabertv02`), or place a local copy of
the model under `saved_models/arabertv02/` to avoid depending on network access.

## Usage

Extract text from a sample document:

```bash
python -m src.app.ocr.demo
```

Train the classification head on synthetic data and classify a sample report:

```bash
python -m src.app.nlp.train
python -m src.app.nlp.demo
```

Launch the Streamlit dashboard to upload a document and see its extracted text and
classification interactively:

```bash
streamlit run app/main.py
```

## License

MIT — see [LICENSE](LICENSE).
