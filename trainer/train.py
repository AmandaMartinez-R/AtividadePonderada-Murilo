"""Treina uma regressão linear para estimar o fechamento do próximo dia."""

import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# Features são as entradas; target é o valor que quero estimar para o dia atual.
FEATURES = ["close_lag_1", "close_lag_2", "close_lag_3", "close_mean_7"]
TARGET = "target_next_close"


def load_prices(csv_path: Path) -> pd.DataFrame:
    """Lê as colunas Date e Close e remove registros inválidos."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV não encontrado em {csv_path}. Execute "
            "python trainer/download_data.py antes do treinamento."
        )

    prices = pd.read_csv(csv_path)
    normalized_names = {str(name).strip().lower(): name for name in prices.columns}
    if "close" not in normalized_names:
        raise ValueError("O CSV precisa conter uma coluna 'Close'.")
    close_name = normalized_names["close"]
    date_name = normalized_names.get("date")
    if date_name is None:
        raise ValueError("O CSV precisa conter uma coluna 'Date'.")

    prices = prices[[date_name, close_name]].rename(
        columns={date_name: "date", close_name: "close"}
    )
    prices["date"] = pd.to_datetime(prices["date"], errors="coerce", utc=True)
    prices["close"] = pd.to_numeric(prices["close"], errors="coerce")
    # Ordeno por data, removo duplicatas e descarto fechamentos vazios ou inválidos.
    prices = prices.dropna().sort_values("date").drop_duplicates("date")
    prices = prices[prices["close"] > 0].reset_index(drop=True)
    if len(prices) < 20:
        raise ValueError("São necessárias pelo menos 20 observações válidas.")
    return prices


def make_features(prices: pd.DataFrame) -> pd.DataFrame:
    """Cria lags passados; o alvo é o fechamento da data corrente.

    Lag é o fechamento de um ou mais dias anteriores. A média móvel usa os
    sete fechamentos anteriores. O shift impede que a data-alvo entre nas
    próprias features. As linhas iniciais sem histórico completo viram NaN e
    são removidas porque não há valores suficientes para calcular as entradas.
    """
    close = prices["close"]
    result = pd.DataFrame(index=prices.index)
    result["close_lag_1"] = close.shift(1)
    result["close_lag_2"] = close.shift(2)
    result["close_lag_3"] = close.shift(3)
    result["close_mean_7"] = close.shift(1).rolling(window=7).mean()
    result[TARGET] = close
    result["date"] = prices["date"]
    return result.dropna().reset_index(drop=True)


def calculate_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    # MAE e RMSE medem o tamanho do erro; R² resume quanto da variação o modelo explica.
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def main() -> None:
    data_path = Path(os.getenv("DATA_PATH", "data/btc_usd.csv"))
    artifacts_dir = Path(os.getenv("ARTIFACTS_DIR", "artifacts"))
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    prices = load_prices(data_path)
    dataset = make_features(prices)
    x = dataset[FEATURES]
    y = dataset[TARGET]

    # O corte preserva a ordem: os 80% iniciais treinam e os 20% finais avaliam.
    split_index = int(len(dataset) * 0.8)
    if split_index == 0 or split_index == len(dataset):
        raise ValueError("Não foi possível criar treino e teste cronológicos.")
    x_train, x_test = x.iloc[:split_index], x.iloc[split_index:]
    y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]

    model = LinearRegression()
    # O backend recria as colunas na ordem registrada no artefato e envia uma
    # matriz numérica; treinar também com matriz evita depender de DataFrame.
    model.fit(x_train.to_numpy(), y_train.to_numpy())
    model_metrics = calculate_metrics(y_test.to_numpy(), model.predict(x_test.to_numpy()))
    baseline_metrics = calculate_metrics(
        y_test.to_numpy(), x_test["close_lag_1"].to_numpy()
    )

    # O backend recebe o estimador pronto e os sete últimos preços para formar
    # as features da próxima data; nenhuma etapa de treinamento roda na API.
    bundle = {
        "model": model,
        "features": FEATURES,
        "currency": "BTC-USD",
        "target": "next_day_close",
        "model_name": "LinearRegression",
        "last_closes": prices["close"].tail(7).astype(float).tolist(),
        "last_observation_date": prices["date"].iloc[-1].date().isoformat(),
    }
    # Salvo o modelo separado das métricas para que o backend só carregue o bundle.
    joblib.dump(bundle, artifacts_dir / "model.joblib")

    metrics = {
        "currency": "BTC-USD",
        "frequency": "daily",
        "target": "next_day_close",
        "features": FEATURES,
        "algorithm": "LinearRegression",
        "split": {
            "method": "chronological",
            "train_fraction": 0.8,
            "train_rows": int(len(x_train)),
            "test_rows": int(len(x_test)),
            "test_start": dataset["date"].iloc[split_index].date().isoformat(),
            "test_end": dataset["date"].iloc[-1].date().isoformat(),
        },
        "model": model_metrics,
        "naive_baseline_close_lag_1": baseline_metrics,
    }
    # Guardo os números do teste para comparar o modelo com a previsão ingênua.
    (artifacts_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Treinamento concluído: {len(x_train)} linhas de treino, {len(x_test)} de teste.")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"Artefato salvo em {artifacts_dir / 'model.joblib'}")


if __name__ == "__main__":
    main()
