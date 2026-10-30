FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY agent_layer ./agent_layer
COPY knowledge_data ./knowledge_data
COPY experiments ./experiments
COPY docs ./docs
COPY site ./site

RUN useradd --create-home --uid 10001 tender \
    && chown -R tender:tender /app/agent_layer

USER tender
WORKDIR /app/agent_layer
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
