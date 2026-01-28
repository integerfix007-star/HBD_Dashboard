FROM python:3.11-slim

WORKDIR /app


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt
RUN pip install playwright

RUN playwright install --with-deps chromium

RUN mkdir -p /app/tmp/uploads

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "gunicorn app:app -b 0.0.0.0:${PORT:-8000}"]