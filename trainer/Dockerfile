FROM python:3.11-slim

WORKDIR /app

COPY trainer/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY trainer/ ./trainer/

# O treinamento usa o CSV local montado em /data.
CMD ["python", "trainer/train.py"]
