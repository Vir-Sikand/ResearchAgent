FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "mcp[cli]" tavily-python openai
RUN git clone https://github.com/assafelovic/gpt-researcher.git /app
EXPOSE 8000
CMD ["python", "mcp/server.py", "--transport", "sse", "--port", "8000"]
