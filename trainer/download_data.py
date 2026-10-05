"""Baixa uma série diária BTC-USD e salva um CSV local para o treinamento."""

from pathlib import Path

import yfinance as yf


def main() -> None:
    output_path = Path("data/btc_usd.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # O download acontece somente quando este script é executado explicitamente.
    history = yf.download(
        "BTC-USD",
        period="5y",
        interval="1d",
        auto_adjust=True,
        progress=False,
    )
    if history.empty:
        raise RuntimeError("O Yahoo Finance não retornou dados para BTC-USD.")

    close = history["Close"]
    # Versões recentes do yfinance podem retornar colunas MultiIndex.
    if getattr(close, "ndim", 1) == 2:
        close = close.iloc[:, 0]
    output = close.rename("Close").rename_axis("Date").reset_index()
    output.to_csv(output_path, index=False, date_format="%Y-%m-%d")
    print(f"CSV salvo em {output_path} ({len(output)} observações diárias).")


if __name__ == "__main__":
    main()
