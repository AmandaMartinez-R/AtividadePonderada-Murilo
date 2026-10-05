FROM python:3.11-slim

# Defino a pasta de trabalho que será usada dentro do container.
WORKDIR /app

# Instalo as dependências antes de copiar o código do trainer.
COPY trainer/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copio somente os arquivos do treinamento para a imagem.
COPY trainer/ ./trainer/

# O treinamento usa o CSV local montado em /data.
CMD ["python", "trainer/train.py"]
