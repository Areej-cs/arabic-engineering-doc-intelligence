# same image is used for the api and the dashboard (see docker-compose.yml)
FROM python:3.11-slim-bookworm

# tesseract + arabic data, poppler for pdfs, glib for opencv, a font with arabic glyphs
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-ara tesseract-ocr-eng poppler-utils libglib2.0-0 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TESSERACT_CMD=/usr/bin/tesseract

WORKDIR /app

# cpu-only torch, the default one comes with CUDA and is huge
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu
RUN pip install torch==2.4.1 --index-url ${TORCH_INDEX_URL}

COPY requirements.txt .
RUN pip install -r requirements.txt

# download AraBERT and train the head during the build
COPY src ./src
COPY scripts ./scripts
RUN python -m scripts.download_model && python -m src.app.nlp.train

COPY app ./app
COPY .streamlit ./.streamlit
COPY migrations ./migrations
COPY alembic.ini .

RUN useradd --create-home appuser && mkdir -p data/uploads && chown -R appuser /app
USER appuser

EXPOSE 8000 8501
CMD ["./scripts/start-api.sh"]
