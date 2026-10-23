FROM python:3.11-slim-bookworm
WORKDIR /app
COPY pyproject.toml README.md ./
COPY ai_daily ./ai_daily
RUN pip install --no-cache-dir Pillow cryptography
ENV PYTHONPATH=/app
EXPOSE 8787
CMD ["python", "-m", "ai_daily", "serve", "--host", "0.0.0.0", "--port", "8787", "--root", "/app/runtime"]
