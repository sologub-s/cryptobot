FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

CMD python main.py webserver --chat_id=$TELEGRAM_CHAT_ID
