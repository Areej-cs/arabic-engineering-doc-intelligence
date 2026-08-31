"""Tests for src.app.nlp.data_generator (synthetic training data for the classifier)."""

import re

from src.app.nlp.data_generator import LABELS, _random_equipment_id, generate_dataset


def test_generate_dataset_is_balanced_across_labels() -> None:
    texts, labels = generate_dataset(samples_per_label=20, seed=1)

    assert len(texts) == len(labels) == 20 * len(LABELS)
    for label in LABELS:
        assert labels.count(label) == 20


def test_generate_dataset_is_reproducible_with_same_seed() -> None:
    texts_a, labels_a = generate_dataset(samples_per_label=10, seed=7)
    texts_b, labels_b = generate_dataset(samples_per_label=10, seed=7)

    assert texts_a == texts_b
    assert labels_a == labels_b


def test_generate_dataset_has_no_duplicate_reports() -> None:
    texts, _ = generate_dataset(samples_per_label=15, seed=3)
    assert len(texts) == len(set(texts))


def test_random_equipment_id_format() -> None:
    equipment_id = _random_equipment_id()
    assert re.fullmatch(r"[A-Z]+-\d{3}", equipment_id)
