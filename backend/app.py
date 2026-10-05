"""API de inferência: carrega um artefato já treinado na inicialização."""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
MODEL_PATH = Path(os.getenv("MODEL_PATH", "artifacts/model.joblib"))
model_bundle: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Carrega o arquivo persistido uma vez; não há treinamento na API."""
    global model_bundle
    if not MODEL_PATH.is_file():
        raise RuntimeError(f"Artefato não encontrado: {MODEL_PATH}")
    model_bundle = joblib.load(MODEL_PATH)
    required = {"model", "features", "last_closes", "last_observation_date"}
    if not required.issubset(model_bundle):
        raise RuntimeError("O artefato não contém os dados necessários à inferência.")
    if len(model_bundle["last_closes"]) < 7:
        raise RuntimeError("O artefato precisa conter sete fechamentos recentes.")
    logger.info("Modelo %s carregado de %s", model_bundle.get("model_name"), MODEL_PATH)
    yield


app = FastAPI(title="BTC-USD next-day prediction", lifespan=lifespan)


def predict_next_close(closes: list[float]) -> float:
    """Monta as mesmas features do treino para os preços recebidos."""
    if len(closes) < 7:
        raise ValueError("Informe pelo menos sete fechamentos diários.")
    recent = np.asarray(closes[-7:], dtype=float)
    if not np.isfinite(recent).all() or (recent <= 0).any():
        raise ValueError("Os fechamentos devem ser números positivos e finitos.")

    # A ordem é cronológica: o último item é o fechamento mais recente.
    features = {
        "close_lag_1": recent[-1],
        "close_lag_2": recent[-2],
        "close_lag_3": recent[-3],
        "close_mean_7": float(recent.mean()),
    }
    ordered = [[features[name] for name in model_bundle["features"]]]
    return float(model_bundle["model"].predict(ordered)[0])


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "model_loaded": bool(model_bundle)}


@app.get("/predict/latest")
def predict_latest() -> dict[str, Any]:
    if not model_bundle:
        raise HTTPException(status_code=503, detail="Modelo ainda não carregado.")
    prediction = predict_next_close(model_bundle["last_closes"])
    return {
        "currency": model_bundle.get("currency", "BTC-USD"),
        "prediction": round(prediction, 2),
        "target": model_bundle.get("target", "next_day_close"),
        "model": model_bundle.get("model_name", "LinearRegression"),
        "based_on_date": model_bundle["last_observation_date"],
    }
