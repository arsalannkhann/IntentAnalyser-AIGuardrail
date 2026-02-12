FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app ./app
COPY main.py . 
# (Note: main.py is likely redundant if we run app.main, but keeping structure clean)

# Environment
ENV INTENT_ANALYZER_MODEL=bart
ENV PORT=8002
ENV HOME=/tmp
ENV TRANSFORMERS_CACHE=/tmp/.cache

# Download models during build to speed up startup and avoid network timeouts at runtime
RUN python3 -c "from transformers import pipeline; pipeline('zero-shot-classification', model='facebook/bart-large-mnli')"
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

EXPOSE 8002

# Use a longer timeout for worker boot to handle model loading
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--timeout-keep-alive", "120"]
