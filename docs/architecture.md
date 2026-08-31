# Architecture Notes

Quick overview of how a document moves through the pipeline, mostly written
so I don't have to re-read all the code next time I come back to this.

## Pipeline

1. **Input** — a scanned image or photographed report comes in. Right now
   that's through the Streamlit uploader; an API endpoint is the plan once
   the FastAPI layer exists.
2. **OCR** (`src/app/ocr/extractor.py`) — PDFs are rasterized to images first
   (`pdf2image` + Poppler), then every page goes through Tesseract with
   `ara+eng`. Grayscale + adaptive thresholding before OCR made a noticeable
   difference on the phone-photo samples I tested with; less so on clean
   scans.
3. **Classification** (`src/app/nlp/classifier.py`) — the OCR'd text is
   embedded with a frozen AraBERT encoder (mean-pooled, masked), then a
   small trainable head (`Linear -> ReLU -> Dropout -> Linear`) maps that
   embedding to `Urgent` / `Normal` / `Low`.
4. **Output** — shown in the dashboard for now. Once the API + Postgres
   layer is in, the plan is to persist results so reports can be
   queried/filtered instead of processed one at a time.

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
- No API layer yet, so the dashboard is currently the only way to run the
  full pipeline end to end.
