"""AraBERT-based report classifier: frozen encoder + a small trainable classification head."""

import os
from pathlib import Path

import torch
from dotenv import load_dotenv
from loguru import logger
from torch import nn
from transformers import AutoModel, AutoTokenizer

load_dotenv()

LABELS = ["Urgent", "Normal", "Low"]

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_LOCAL_MODEL_DIR = _PROJECT_ROOT / "saved_models" / "arabertv02"
_DEFAULT_MODEL_NAME = os.getenv("ARABERT_MODEL_NAME", "aubmindlab/bert-base-arabertv02")
_DEFAULT_HEAD_PATH = _PROJECT_ROOT / "saved_models" / "classifier" / "head.pt"

_DEVICE = os.getenv("DEVICE", "cpu")


def _model_source() -> str:
    """Prefer a local copy of the model (avoids relying on live Hub access)."""
    if _LOCAL_MODEL_DIR.exists() and any(_LOCAL_MODEL_DIR.iterdir()):
        return str(_LOCAL_MODEL_DIR)
    return _DEFAULT_MODEL_NAME


class ClassificationHead(nn.Module):
    """A small MLP trained on top of frozen AraBERT [CLS] embeddings."""

    def __init__(self, hidden_size: int = 768, num_labels: int = len(LABELS)):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(hidden_size, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, num_labels),
        )

    def forward(self, embeddings: torch.Tensor) -> torch.Tensor:
        return self.net(embeddings)


def load_encoder() -> tuple[AutoTokenizer, AutoModel]:
    source = _model_source()
    logger.info("Loading AraBERT encoder from: {}", source)
    is_local = source == str(_LOCAL_MODEL_DIR)
    tokenizer = AutoTokenizer.from_pretrained(source, local_files_only=is_local)
    model = AutoModel.from_pretrained(source, local_files_only=is_local)
    model.to(_DEVICE)
    model.eval()
    for param in model.parameters():
        param.requires_grad = False
    return tokenizer, model


@torch.no_grad()
def embed_texts(
    texts: list[str], tokenizer: AutoTokenizer, encoder: AutoModel, batch_size: int = 16
) -> torch.Tensor:
    """Mean-pool token embeddings (masked) into one vector per text."""
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        inputs = tokenizer(batch, padding=True, truncation=True, return_tensors="pt").to(_DEVICE)
        outputs = encoder(**inputs)
        mask = inputs["attention_mask"].unsqueeze(-1).float()
        summed = (outputs.last_hidden_state * mask).sum(dim=1)
        counts = mask.sum(dim=1).clamp(min=1e-9)
        all_embeddings.append(summed / counts)
    return torch.cat(all_embeddings, dim=0)


def save_head(head: ClassificationHead, path: Path = _DEFAULT_HEAD_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(head.state_dict(), path)


def load_head(path: Path = _DEFAULT_HEAD_PATH) -> ClassificationHead:
    if not path.exists():
        raise FileNotFoundError(
            f"No trained classification head found at {path}. Run src/app/nlp/train.py first."
        )
    head = ClassificationHead()
    head.load_state_dict(torch.load(path, map_location=_DEVICE))
    head.eval()
    return head


def predict(
    text: str, tokenizer: AutoTokenizer, encoder: AutoModel, head: ClassificationHead
) -> str:
    embedding = embed_texts([text], tokenizer, encoder)
    with torch.no_grad():
        logits = head(embedding)
    predicted_index = int(torch.argmax(logits, dim=-1).item())
    return LABELS[predicted_index]
