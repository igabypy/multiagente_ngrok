# Multi-Agent Dockerfile
FROM python:3.11-slim
WORKDIR /code

COPY app/requirements_multi_agent.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main_multi_agent:api", "--host", "0.0.0.0", "--port", "8000"]
