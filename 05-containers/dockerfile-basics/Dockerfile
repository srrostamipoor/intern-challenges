FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY app.py .

ENV APP_ENV=production
EXPOSE 8080

CMD ["python", "app.py"]