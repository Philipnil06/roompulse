FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
COPY backend ./backend
COPY mcp_server ./mcp_server
RUN pip install --no-cache-dir .

ENV ROOMPULSE_DB_PATH=/data/roompulse.db
EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
