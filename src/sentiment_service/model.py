"""Wrapper around a Hugging Face sentiment model."""
from __future__ import annotations

from typing import Dict, Optional

from transformers import pipeline


class SentimentModel:
    def __init__(
        self,
        model_name: str,
        revision: Optional[str] = None,
        device: Optional[str] = None,
        label_mapping: Optional[Dict[str, str]] = None,
    ) -> None:
        kwargs = {
            "task": "text-classification",
            "model": model_name,
            "tokenizer": model_name,
            "return_all_scores": True,
        }
        if revision:
            kwargs["revision"] = revision
        # transformers accepts either torch device id (int) or str like "cpu"
        if device is not None:
            kwargs["device"] = device
        self._classifier = pipeline(**kwargs)
        self._label_mapping = {k.lower(): v for k, v in (label_mapping or {}).items()}

    def predict(self, text: str) -> Dict[str, float]:
        """Return normalized scores keyed by canonical labels."""
        if not text:
            raise ValueError("Text is required for sentiment scoring")
        raw_output = self._classifier(
            text,
            truncation=True,
            max_length=512,
            padding=True,
        )
        scores = _flatten_scores(raw_output)
        normalized: Dict[str, float] = {}
        for label, score in scores.items():
            canonical = self._label_mapping.get(label.lower(), label.lower())
            normalized[canonical] = score
        return normalized


def _flatten_scores(raw_output: object) -> Dict[str, float]:
    """Normalize pipeline outputs into a simple label→score dict."""
    if isinstance(raw_output, list):
        if not raw_output:
            return {}
        # return_all_scores=True produces List[List[dict]] for str input
        first = raw_output[0]
        if isinstance(first, list):
            entries = first
        elif isinstance(first, dict) and "label" in first:
            entries = raw_output
        else:
            raise ValueError(f"Unsupported pipeline output format: {raw_output}")
    else:
        raise ValueError(f"Unsupported pipeline output type: {type(raw_output)}")
    return {entry["label"].lower(): float(entry["score"]) for entry in entries}
