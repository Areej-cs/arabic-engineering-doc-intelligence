"""Streamlit dashboard: upload an image/PDF, show OCR text and its priority classification.

STREAMLIT_MODE=local runs the pipeline here directly, STREAMLIT_MODE=api sends the file
to the FastAPI service and also shows the saved reports.
"""

import os
import sys
from pathlib import Path

_PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import httpx  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv()

MODE = os.getenv("STREAMLIT_MODE", "local").lower()
API_BASE_URL = os.getenv("STREAMLIT_API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")
PRIORITY_COLOR = {"Urgent": "red", "Normal": "blue", "Low": "gray"}

st.set_page_config(page_title="Arabic Engineering Document Intelligence", page_icon="📄")

st.title("Arabic Engineering Document Intelligence")
st.write("Upload a scanned image or PDF report to extract its text and classify its priority.")


def show_result(text: str, priority: str) -> None:
    st.subheader("Extracted text")
    st.text_area("OCR output", text, height=200)
    st.subheader("Classification")
    st.markdown(f"**Priority:** :{PRIORITY_COLOR.get(priority, 'gray')}[{priority}]")


def process_locally(data: bytes, suffix: str) -> tuple[str, str]:
    from src.app.services.pipeline import process_bytes

    with st.spinner("Extracting text and classifying (first run loads AraBERT)..."):
        result = process_bytes(data, suffix)
    return result.text, result.priority


def process_via_api(name: str, data: bytes, content_type: str | None) -> tuple[str, str]:
    with st.spinner("Sending to the API..."):
        response = httpx.post(
            f"{API_BASE_URL}/documents",
            files={"file": (name, data, content_type or "application/octet-stream")},
            timeout=180,
        )
    if response.status_code != 201:
        raise RuntimeError(response.json().get("detail", response.text))
    body = response.json()
    return body["extracted_text"], body["priority"]


def show_history() -> None:
    st.divider()
    st.header("Processed reports")
    try:
        stats = httpx.get(f"{API_BASE_URL}/documents/stats", timeout=10).json()
    except httpx.HTTPError as e:
        st.warning(f"Can't reach the API at {API_BASE_URL}: {e}")
        return

    cols = st.columns(4)
    cols[0].metric("Total", stats["total"])
    for col, label in zip(cols[1:], ["Urgent", "Normal", "Low"], strict=True):
        col.metric(label, stats["by_priority"].get(label, 0))

    choice = st.selectbox("Filter by priority", ["All", "Urgent", "Normal", "Low"])
    params = {"limit": 50} | ({} if choice == "All" else {"priority": choice})
    items = httpx.get(f"{API_BASE_URL}/documents", params=params, timeout=10).json()["items"]
    if not items:
        st.info("No reports yet.")
        return
    table = pd.DataFrame(items)[["created_at", "filename", "priority"]]
    table["created_at"] = pd.to_datetime(table["created_at"]).dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(table, hide_index=True, use_container_width=True)


uploaded_file = st.file_uploader(
    "Upload an image or PDF", type=["png", "jpg", "jpeg", "tif", "tiff", "bmp", "pdf"]
)

if uploaded_file is not None:
    # streamlit reruns the whole script on every click, without this the same file
    # is uploaded again whenever the filter changes
    upload_key = uploaded_file.file_id
    if st.session_state.get("upload_key") != upload_key:
        try:
            data = uploaded_file.getvalue()
            if MODE == "api":
                result = process_via_api(uploaded_file.name, data, uploaded_file.type)
            else:
                result = process_locally(data, Path(uploaded_file.name).suffix)
            st.session_state["upload_key"] = upload_key
            st.session_state["result"] = result
        except Exception as e:
            st.session_state.pop("upload_key", None)
            st.error(f"Failed to process file: {e}")
    if st.session_state.get("upload_key") == upload_key:
        show_result(*st.session_state["result"])

if MODE == "api":
    show_history()
