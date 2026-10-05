"""Cliente mínimo para consultar saúde e previsão da API."""

import json
import os
from urllib.request import urlopen


def get_json(url: str) -> dict:
    with urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    # Por padrão o cliente chama a API publicada na porta 8000 da máquina.
    base_url = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
    # Primeiro confiro a saúde do serviço; depois peço a previsão.
    health = get_json(f"{base_url}/health")
    print("Health:", json.dumps(health, ensure_ascii=False))
    prediction = get_json(f"{base_url}/predict/latest")
    print("Predição:", json.dumps(prediction, ensure_ascii=False))


if __name__ == "__main__":
    main()
