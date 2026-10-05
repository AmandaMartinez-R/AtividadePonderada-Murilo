# Atividade Ponderada Murilo — M7 2026

#### Nome: Amanda Cristina Martinez da Rosa

## 1. Objetivo

Demonstrar um fluxo simples de Machine Learning: dados históricos de BTC-USD, treinamento em um container, exportação do modelo e previsões por uma API Python em outro container.

## 2. Arquitetura e diagrama UML

![Diagrama UML da arquitetura de treinamento e inferência](assets/architecture.png)

O serviço `trainer` lê `data/btc_usd.csv`, prepara as features, treina o modelo e grava `artifacts/model.joblib` e `artifacts/metrics.json`. O serviço `backend` só inicia depois que o treinamento termina com sucesso. Ele monta `artifacts/` em modo de leitura e carrega o modelo ao iniciar. O cliente acessa a API por HTTP.

## 3. Modelo

- **Moeda e frequência:** BTC-USD, dados diários.
- **Fonte planejada:** Yahoo Finance, usando `yfinance`; o download configura os últimos cinco anos e salva `Date` e `Close` em CSV.
- **Features:** fechamentos dos três dias anteriores (`close_lag_1`, `close_lag_2`, `close_lag_3`) e média dos sete fechamentos anteriores (`close_mean_7`).
- **Alvo:** fechamento do próximo dia.
- **Algoritmo:** `LinearRegression`.
- **Separação:** cronológica; 80% inicial para treino e 20% final para teste, sem embaralhamento.
- **Métricas:** MAE, RMSE e R²; comparação com o baseline “o próximo fechamento será igual ao último”.

O treino salva as métricas em `artifacts/metrics.json`. O bundle em `artifacts/model.joblib` contém o estimador e os sete fechamentos mais recentes usados pela rota de previsão.

## 4. Estrutura do projeto

```text
.
├── README.md
├── docker-compose.yml
├── assets/
│   └── architecture.png
├── backend/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── client/
│   └── client.py
├── docs/
│   ├── architecture.puml
│   └── sequence.puml
├── trainer/
│   ├── Dockerfile
│   ├── download_data.py
│   ├── requirements.txt
│   └── train.py
├── data/       # CSV criado pelo download
└── artifacts/  # modelo e métricas criados pelo treino
```

## 5. Como executar

### Pré-requisitos

- Docker com Docker Compose;
- Python 3.11 para baixar os dados com o script local.

### Baixar os dados

Na pasta do repositório:

```bash
python -m pip install -r trainer/requirements.txt
python trainer/download_data.py
```

O CSV será salvo em `data/btc_usd.csv`. O download precisa de conexão com a internet; o treinamento posterior usa o arquivo local.

### Construir e iniciar

```bash
docker compose build
docker compose up
```

O Compose inicia o `trainer`, que cria os artefatos. Após o treinamento concluir com sucesso, o `backend` inicia e disponibiliza a porta 8000. Deixe esse terminal aberto e use outro terminal para consultar a API.

### Health check e previsão

```bash
curl http://localhost:8000/health
curl http://localhost:8000/predict/latest
```

No Windows, se `curl` apontar para o alias do PowerShell, use `curl.exe`.

### Cliente

Com os containers ativos:

```bash
python client/client.py
```

Para encerrar:

```bash
docker compose down
```

## 6. API

- `GET /health`: informa se o serviço está ativo e se o modelo foi carregado.
- `GET /predict/latest`: prevê o fechamento do próximo dia com base nos últimos dados incluídos no artefato.

## 7. Limitações

O modelo usa somente preços históricos e poucas features. Bitcoin é volátil; o resultado é experimental, tem finalidade educacional e não é recomendação de investimento.

## 8. Documentação e Dev Log

- [Diagrama UML em PlantUML](docs/architecture.puml)
- [Diagrama de sequência em PlantUML](docs/sequence.puml)

Registre no Dev Log, durante a execução, suas decisões, comandos realmente usados, resultados, dificuldades e correções. Inclua as métricas e as respostas HTTP observadas. Registre também que a preparação inicial do código teve apoio de IA. Não registre como executado o que ainda não foi feito.

## 9. Estado atual

Os arquivos de código, a arquitetura e as instruções de reprodução estão preparados. O download do CSV, o treinamento, a geração dos artefatos e os testes dos containers ainda precisam ser executados; portanto, ainda não há métricas ou respostas reais da API para registrar.
