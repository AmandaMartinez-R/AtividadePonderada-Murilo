# Atividade Ponderada Murilo — M7 2026

#### Nome: Amanda Cristina Martinez da Rosa

## 1. Objetivo

Demonstrar um fluxo simples de Machine Learning: dados históricos de BTC-USD, treinamento em um container, exportação do modelo e previsões por uma API Python em outro container.

## 2. Arquitetura e diagrama UML

![Diagrama UML da arquitetura de treinamento e inferência](assets/architecture.png)

Eu organizei o desenho em partes para ficar fácil de acompanhar o caminho dos dados e do modelo:

- BTC-USD diário é a entrada. O CSV tem a data e o preço de fechamento; o trainer lê essa cópia local.
- O container tracejado “Treinamento” representa o serviço trainer. Dentro dele, train.py prepara as features, separa passado e futuro sem embaralhar as linhas, treina a regressão linear e calcula as métricas.
- model.joblib é o artefato laranja gerado pelo trainer. Ele guarda o modelo treinado, a ordem das features e os sete fechamentos mais recentes. O backend usa esses valores para montar a previsão do próximo dia.
- metrics.json também é gerado pelo treinamento e guarda as métricas do modelo e do baseline ingênuo.
- O container tracejado “Inferência” representa o backend FastAPI. Ele monta a mesma pasta de artefatos em modo de leitura e carrega o modelo quando inicia. Não treina de novo.
- O cliente é o script client.py ou um comando curl. Ele chama o backend por HTTP e recebe uma resposta JSON.

As setas azuis mostram o fluxo dos dados e as chamadas HTTP. As setas laranja mostram os arquivos criados no treinamento e o caminho do modelo até o backend. O Docker Compose espera o trainer terminar com sucesso antes de iniciar a API. Assim, o segundo container carrega o model.joblib gerado pelo primeiro.

O diagrama de sequência em docs/sequence.puml mostra essa ordem em mais detalhe: primeiro o treinamento salva o arquivo, depois o backend carrega o modelo e, por fim, o cliente chama as rotas.

## 3. Modelo

- **Moeda e frequência:** BTC-USD, dados diários.
- **Fonte usada:** Yahoo Finance, via `yfinance`; baixei cinco anos de dados diários e salvei as colunas `Date` e `Close` no CSV.
- **Features:** fechamentos dos três dias anteriores (`close_lag_1`, `close_lag_2`, `close_lag_3`) e média dos sete fechamentos anteriores (`close_mean_7`).
- **Alvo:** fechamento do próximo dia.
- **Algoritmo:** `LinearRegression`.
- **Separação:** cronológica; 80% inicial para treino e 20% final para teste, sem embaralhamento.
- **Métricas:** MAE, RMSE e R²; comparação com o baseline “o próximo fechamento será igual ao último”.

O treino salva as métricas em `artifacts/metrics.json`. O bundle em `artifacts/model.joblib` contém o estimador e os sete fechamentos mais recentes usados pela rota de previsão.

No teste temporal, o modelo teve MAE de 1311.26, RMSE de 1881.13 e R² de 0.98258. O baseline teve MAE de 1302.66, RMSE de 1867.24 e R² de 0.98284. Nesse recorte, o baseline ingênuo ficou ligeiramente melhor; a meta principal continua sendo demonstrar o fluxo do artefato até a API.

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
├── data/
│   └── btc_usd.csv
└── artifacts/
    ├── metrics.json
    └── model.joblib
```

## 5. Como executar

### Pré-requisitos

- Docker com Docker Compose;
- Python 3.11 ou mais recente para baixar os dados com o script local. Nesta execução usei Python 3.12.

### Baixar os dados

Na pasta do repositório, criei um ambiente Python local e instalei as dependências:

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r trainer/requirements.txt
.venv/Scripts/python.exe trainer/download_data.py
```

O CSV foi salvo em `data/btc_usd.csv`. Ele tem 1.827 observações, de 2021-10-05 a 2026-10-05. O download precisa de conexão com a internet; o treinamento posterior usa o arquivo local.

### Treinar o modelo

```bash
.venv/Scripts/python.exe trainer/train.py
```

O treinamento local terminou com 1.456 linhas de treino e 364 linhas de teste. A separação foi cronológica, sem embaralhar os dados. Ele gerou `artifacts/model.joblib` e `artifacts/metrics.json`.

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

## 8. Dev Log

### Etapa 1: Diagrama

Comecei pelo diagrama para entender como os containers e o arquivo do modelo iam se conectar antes de seguir com o restante. Com apoio de IA, montei uma primeira versão da imagem e dos arquivos PlantUML. A prévia SVG não apareceu no chat, então gerei uma versão PNG para revisar. Depois da aprovação, coloquei a imagem em assets/architecture.png e deixei os fontes em docs/.

O desenho mostra o CSV chegando ao trainer, o trainer gerando o modelo e as métricas, e o backend carregando o mesmo modelo pelo volume compartilhado. Também mostra o cliente chamando a API por HTTP. Registrei essa etapa no commit 637b5d9, “Adiciona diagrama UML”. O histórico local estava vazio e a referência origin/main não estava disponível, então mantive os commits no repositório local, sem push.

### Etapa 2: Modelo

Com apoio de IA, preparei o downloader do BTC-USD e o código de treinamento. Escolhi LinearRegression e features com os fechamentos anteriores: três lags e a média dos sete últimos fechamentos. O código separa treino e teste em ordem cronológica e calcula MAE, RMSE e R², além de comparar com o baseline “amanhã igual a hoje”.

O trainer salva model.joblib e metrics.json. O artefato também leva os últimos sete preços e as informações que o backend precisa para prever. O código desta etapa ficou no commit a46e596, “Adiciona modelo de previsão”.

- Na primeira tentativa de pip install, o Windows bloqueou a conexão de rede com WinError 10013. Depois da liberação de rede, instalei as dependências na .venv do projeto.
- Executei `.venv/Scripts/python.exe trainer/download_data.py`; o arquivo veio do Yahoo Finance e ficou com 1.827 observações diárias, de 2021-10-05 a 2026-10-05.
- Executei `.venv/Scripts/python.exe trainer/train.py`; o corte ficou com 1.456 linhas de treino e 364 de teste.
- Métricas reais: LinearRegression — MAE 1311.26, RMSE 1881.13, R² 0.98258. Baseline — MAE 1302.66, RMSE 1867.24, R² 0.98284.
- Reabri o model.joblib com joblib, validei o JSON das métricas e rodei uma previsão direta pelo objeto salvo: 85619.84.
- Neste recorte, o baseline teve erros um pouco menores que a regressão linear.
- Commitei o CSV, o artefato e as métricas no commit c52be98, “Registra dados e métricas do treino”.

### Etapa 3: Deploy

Com apoio de IA, preparei o backend em Python com FastAPI, o cliente simples e o Docker Compose. O backend carrega o artefato ao iniciar e tem as rotas /health e /predict/latest. No Compose, os dois serviços compartilham a pasta artifacts: o trainer grava nela e o backend monta em modo de leitura. Também configurei a API para iniciar depois que o trainer terminar com sucesso.

Registrei o código desta etapa no commit bfae6e2, “Adiciona API e Docker Compose”.

- O Docker não estava disponível, então instalei as dependências da API na .venv e iniciei o backend localmente com `.venv/Scripts/python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000`. O log confirmou que o modelo foi carregado de artifacts/model.joblib.
- Instalei as dependências do backend com `.venv/Scripts/python.exe -m pip install -r backend/requirements.txt`.
- GET /health respondeu HTTP 200: `{"status":"ok","model_loaded":true}`.
- GET /predict/latest respondeu HTTP 200: `{"currency":"BTC-USD","prediction":85619.84,"target":"next_day_close","model":"LinearRegression","based_on_date":"2026-10-05"}`.
- Executei `.venv/Scripts/python.exe client/client.py`; o cliente consultou as duas rotas e imprimiu as respostas.
- Registrei essas verificações locais no commit 808a5c2, “Registra teste local da API”.

### Etapa 4: Execução

- O comando `docker --version` não foi reconhecido neste ambiente, e não encontrei o executável do Docker Desktop no caminho usual.
- Compilei os arquivos Python e validei a sintaxe YAML localmente. O Compose lista trainer e backend, com o backend esperando o trainer terminar com sucesso.
- O build e a execução do Compose: {...}
- Outros testes e resultados: {...}

### Fontes PlantUML

- [Diagrama de arquitetura](docs/architecture.puml)
- [Diagrama de sequência](docs/sequence.puml)

O código inicial e os diagramas tiveram apoio de IA. As métricas, respostas e evidências ficam registradas conforme os resultados observados.
