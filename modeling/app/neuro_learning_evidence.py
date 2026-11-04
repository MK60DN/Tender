"""Neuro-learning evidence catalog for Tender.

The catalog supports research calibration and construct validation. It does not
authorize direct brain reading, clinical diagnosis, learning-style matching, or
general cognitive enhancement claims.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

BASE = Path(__file__).resolve().parents[2] / "knowledge_data"
BEHAVIOR_DATASETS = BASE / "neuro_behavior_datasets.json"
BRAIN_DATASETS = BASE / "neuro_brain_datasets.json"
BEHAVIOR_RESEARCH = BASE / "neuro_behavior_research.json"
NEURO_EDUCATION_RESEARCH = BASE / "neuro_education_research.json"
CLAIM_BOUNDARIES = BASE / "neuro_learning_claim_boundaries.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _all_datasets() -> list[dict]:
    datasets = []
    datasets.extend(_load(BEHAVIOR_DATASETS).get("datasets", []))
    datasets.extend(_load(BRAIN_DATASETS).get("datasets", []))
    return datasets


def _all_research() -> list[dict]:
    research = []
    research.extend(_load(BEHAVIOR_RESEARCH).get("research", []))
    research.extend(_load(NEURO_EDUCATION_RESEARCH).get("research", []))
    return research


def _contains(values: Iterable[str], query: str | None) -> bool:
    if not query:
        return True
    needle = query.strip().lower()
    return any(needle in str(value).lower() for value in values)


def list_datasets(
    *,
    stage: str | None = None,
    modality: str | None = None,
    access: str | None = None,
    record_type: str | None = None,
) -> list[dict]:
    results = []
    for item in _all_datasets():
        if not _contains(item.get("life_stages", []), stage):
            continue
        if not _contains(item.get("modalities", []), modality):
            continue
        if access and access.lower() not in item.get("access", "").lower():
            continue
        if record_type and record_type.lower() not in item.get("record_type", "").lower():
            continue
        results.append(item)
    return results


def list_research(construct: str | None = None) -> list[dict]:
    results = []
    for item in _all_research():
        if construct and not _contains(item.get("constructs", []), construct):
            continue
        results.append(item)
    return results


def get_claim_boundary(claim_type: str) -> dict:
    boundaries = _load(CLAIM_BOUNDARIES)
    claim = boundaries.get("claim_boundaries", {}).get(claim_type)
    if claim is None:
        raise KeyError(f"unknown_claim_type:{claim_type}")
    return {"claim_type": claim_type, **claim}


def get_integration_layers() -> list[dict]:
    return _load(CLAIM_BOUNDARIES).get("integration_layers", [])


def runtime_neuro_inference_allowed() -> bool:
    for layer in get_integration_layers():
        if layer.get("id") == "neural_runtime_inference":
            return layer.get("status") not in {
                "not_implemented_and_not_claimed",
                "blocked",
            }
    return False


def catalog_summary() -> dict:
    datasets = _all_datasets()
    research = _all_research()
    return {
        "dataset_count": len(datasets),
        "research_count": len(research),
        "behavioral_dataset_count": len(_load(BEHAVIOR_DATASETS).get("datasets", [])),
        "brain_dataset_count": len(_load(BRAIN_DATASETS).get("datasets", [])),
        "stages": ["primary", "middle", "high", "university", "employment"],
        "runtime_neuro_inference_allowed": runtime_neuro_inference_allowed(),
        "current_model_boundary": "Tender 当前主要是语言、行为事件与规则推断，不是运行时神经解码系统。",
    }
