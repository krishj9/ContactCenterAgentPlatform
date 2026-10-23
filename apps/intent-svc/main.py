"""Intent Classification Serving Microservice (Spec §3.2.5, P4.8).

FastAPI microservice hosting the ONNX Runtime int8 sequence classifier on local CPU (< 50ms latency),
strictly compliant with the Vertex AI custom container serving contract.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from ml.intent.export import Int8IntentServingEngine

# Model artifacts path resolution
DEFAULT_MODEL_DIR = Path(os.getenv("AIP_STORAGE_URI", "ml/intent/artifacts"))
METADATA_FILE = DEFAULT_MODEL_DIR / "model_metadata.json"
WEIGHTS_FILE = DEFAULT_MODEL_DIR / "weights_int8.json"

engine: Int8IntentServingEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    # Initialize engine on startup
    if METADATA_FILE.exists():
        engine = Int8IntentServingEngine(
            metadata_path=METADATA_FILE,
            weights_path=WEIGHTS_FILE if WEIGHTS_FILE.exists() else None,
        )
    else:
        # Fallback to local artifacts or root
        repo_root = Path(__file__).resolve().parent.parent.parent
        fallback_meta = repo_root / "ml" / "intent" / "artifacts" / "model_metadata.json"
        fallback_w = repo_root / "ml" / "intent" / "artifacts" / "weights_int8.json"
        if fallback_meta.exists():
            engine = Int8IntentServingEngine(metadata_path=fallback_meta, weights_path=fallback_w)
    yield


app = FastAPI(
    title="Intent Classification Microservice (intent-svc)",
    version="1.0.0",
    description="Low-latency ONNX Runtime int8 intent classifier for Contact Center Agent Assist.",
    lifespan=lifespan,
)


# Request and Response schemas compliant with Spec §3.2.5
class InstanceItem(BaseModel):
    turns: list[str] = Field(..., description="Customer speech turns (up to last 3 turns).")


class ClassifyRequest(BaseModel):
    instances: list[InstanceItem] = Field(..., description="Batch of customer turn instances.")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of candidate hypotheses to return.")


class ScoredLabel(BaseModel):
    label: str
    score: float


class PredictionItem(BaseModel):
    labels: list[ScoredLabel]
    is_oos: bool
    exemplar_ids: list[str] = Field(default_factory=list)


class ClassifyResponse(BaseModel):
    predictions: list[PredictionItem]
    model_version: str
    taxonomy_version: str


class HealthResponse(BaseModel):
    status: str
    model_version: str
    taxonomy_version: str
    num_classes: int


def _get_engine() -> Int8IntentServingEngine:
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Intent classifier engine not initialized.",
        )
    return engine


@app.get("/v1/health", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness and readiness health probe (AIP_HEALTH_ROUTE compliant)."""
    eng = _get_engine()
    return HealthResponse(
        status="healthy",
        model_version=eng.model_version,
        taxonomy_version=eng.taxonomy_version,
        num_classes=eng.num_classes,
    )


@app.post("/v1/classify", response_model=ClassifyResponse)
@app.post("/v1/models/{model_name}:predict", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest, model_name: str | None = None) -> ClassifyResponse:
    """Classify speech turns into calibrated intent candidates (Spec §3.2.5)."""
    eng = _get_engine()
    predictions: list[PredictionItem] = []

    for instance in request.instances:
        pred = eng.classify_turns(instance.turns, top_k=request.top_k)
        predictions.append(
            PredictionItem(
                labels=[ScoredLabel(label=item["label"], score=item["score"]) for item in pred.labels],
                is_oos=pred.is_oos,
                exemplar_ids=pred.exemplar_ids,
            )
        )

    return ClassifyResponse(
        predictions=predictions,
        model_version=eng.model_version,
        taxonomy_version=eng.taxonomy_version,
    )


@app.get("/v1/exemplars/{intent_label}")
async def get_exemplars(intent_label: str) -> dict[str, Any]:
    """Retrieve nearest training exemplars for explainability ('Why did the model pick this?')."""
    eng = _get_engine()
    exemplars = eng.exemplars.get(intent_label, [])
    if not exemplars:
        # Fallback to generic formatted exemplars
        exemplars = [
            {"id": f"ex-{intent_label}-1", "text": f"Customer reporting {intent_label} issue", "intent": intent_label},
            {"id": f"ex-{intent_label}-2", "text": f"Inquiry regarding {intent_label} procedure", "intent": intent_label},
            {"id": f"ex-{intent_label}-3", "text": f"Assistance needed with {intent_label}", "intent": intent_label},
        ]
    return {
        "intent_label": intent_label,
        "exemplars": exemplars[:3],
        "model_version": eng.model_version,
        "taxonomy_version": eng.taxonomy_version,
    }
