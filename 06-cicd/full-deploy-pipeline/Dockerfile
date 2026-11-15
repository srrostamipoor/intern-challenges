FROM python:3.11-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 -r requirements.txt
COPY app/ .
ENV APP_ENV=production
EXPOSE 8080
CMD ["python", "main.py"]
