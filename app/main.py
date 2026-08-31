"""Single-page Streamlit demo: upload an image/PDF, show OCR text and its priority
classification."""

import sys
import tempfile
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st  # noqa: E402
from src.app.nlp.classifier import load_encoder, load_head, predict  # noqa: E402
from src.app.ocr.extractor import extract_text  # noqa: E402

st.set_page_config(page_title="Arabic Engineering Document Intelligence", page_icon="📄")

st.title("Arabic Engineering Document Intelligence")
st.write("Upload a scanned image or PDF report to extract its text and classify its priority.")


@st.cache_resource
def get_classifier():
    tokenizer, encoder = load_encoder()
    head = load_head()
    return tokenizer, encoder, head


_PRIORITY_COLOR = {"Urgent": "red", "Normal": "blue", "Low": "gray"}

uploaded_file = st.file_uploader(
    "Upload an image or PDF", type=["png", "jpg", "jpeg", "tif", "tiff", "bmp", "pdf"]
)

if uploaded_file is not None:
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = Path(tmp.name)

    try:
        with st.spinner("Extracting text..."):
            text = extract_text(tmp_path)

        st.subheader("Extracted text")
        st.text_area("OCR output", text, height=200)

        with st.spinner("Classifying priority..."):
            tokenizer, encoder, head = get_classifier()
            label = predict(text, tokenizer, encoder, head)

        st.subheader("Classification")
        color = _PRIORITY_COLOR.get(label, "gray")
        st.markdown(f"**Priority:** :{color}[{label}]")
    except Exception as e:
        st.error(f"Failed to process file: {e}")
    finally:
        tmp_path.unlink(missing_ok=True)
