FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir requests
COPY nfc_vincular.py .
CMD ["python3", "nfc_vincular.py"]
