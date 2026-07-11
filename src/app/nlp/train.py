"""Trains the classification head on synthetic Arabic maintenance-report data."""

import torch
from loguru import logger
from torch import nn

from src.app.nlp.classifier import (
    LABELS,
    ClassificationHead,
    embed_texts,
    load_encoder,
    save_head,
)
from src.app.nlp.data_generator import generate_dataset


def train_head(
    epochs: int = 30, lr: float = 1e-3, samples_per_label: int = 80, val_split: float = 0.2
) -> ClassificationHead:
    texts, labels = generate_dataset(samples_per_label=samples_per_label)
    label_to_index = {label: i for i, label in enumerate(LABELS)}
    targets = torch.tensor([label_to_index[label] for label in labels])

    tokenizer, encoder = load_encoder()
    logger.info("Computing frozen AraBERT embeddings for {} samples", len(texts))
    embeddings = embed_texts(texts, tokenizer, encoder)

    split_index = int(len(texts) * (1 - val_split))
    train_x, val_x = embeddings[:split_index], embeddings[split_index:]
    train_y, val_y = targets[:split_index], targets[split_index:]

    head = ClassificationHead()
    optimizer = torch.optim.Adam(head.parameters(), lr=lr)
    loss_fn = nn.CrossEntropyLoss()

    for epoch in range(1, epochs + 1):
        head.train()
        optimizer.zero_grad()
        logits = head(train_x)
        loss = loss_fn(logits, train_y)
        loss.backward()
        optimizer.step()

        if epoch % 5 == 0 or epoch == epochs:
            head.eval()
            with torch.no_grad():
                val_accuracy = (head(val_x).argmax(dim=-1) == val_y).float().mean().item()
            logger.info(
                "epoch {}/{} - train_loss={:.4f} val_accuracy={:.2%}",
                epoch, epochs, loss.item(), val_accuracy,
            )

    save_head(head)
    logger.info("Saved trained classification head to saved_models/classifier/head.pt")
    return head


if __name__ == "__main__":
    train_head()
