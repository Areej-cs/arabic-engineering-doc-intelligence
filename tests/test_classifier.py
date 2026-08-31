"""Tests for the trainable part of src.app.nlp.classifier.

load_encoder() loads the full AraBERT model and needs either network access
or a local copy under saved_models/, so it isn't exercised here. These tests
only cover ClassificationHead, which is plain torch and needs neither.
"""

import torch
from src.app.nlp.classifier import LABELS, ClassificationHead


def test_classification_head_output_shape() -> None:
    head = ClassificationHead(hidden_size=16, num_labels=len(LABELS))
    embeddings = torch.randn(4, 16)

    logits = head(embeddings)

    assert logits.shape == (4, len(LABELS))


def test_classification_head_default_num_labels_matches_labels_list() -> None:
    head = ClassificationHead(hidden_size=16)
    embeddings = torch.randn(2, 16)

    logits = head(embeddings)

    assert logits.shape[-1] == len(LABELS)
