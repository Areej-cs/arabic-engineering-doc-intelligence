"""Download AraBERT into saved_models/arabertv02 (used by the Dockerfile).

python -m scripts.download_model
"""

import os
from pathlib import Path

from transformers import AutoModel, AutoTokenizer

MODEL_NAME = os.getenv("ARABERT_MODEL_NAME", "aubmindlab/bert-base-arabertv02")
TARGET_DIR = Path(__file__).resolve().parents[1] / "saved_models" / "arabertv02"


def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    AutoTokenizer.from_pretrained(MODEL_NAME).save_pretrained(TARGET_DIR)
    AutoModel.from_pretrained(MODEL_NAME).save_pretrained(TARGET_DIR)
    print(f"saved {MODEL_NAME} to {TARGET_DIR}")


if __name__ == "__main__":
    main()
