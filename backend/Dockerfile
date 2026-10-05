FROM python:3.11-slim

# A API e seus arquivos ficam dentro desta pasta no container.
WORKDIR /app

# Instalo as bibliotecas necessárias para servir as rotas e carregar o modelo.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copio o backend; o modelo chega pelo volume configurado no Compose.
COPY backend/ ./backend/

# A API escuta nesta porta dentro do container.
EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
