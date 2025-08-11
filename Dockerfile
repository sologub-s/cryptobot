FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y \
    dos2unix \
    cron \
    curl \
    gcc \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY cryptobot/crontab /etc/cron.d/cryptobot-cron
RUN chmod 0644 /etc/cron.d/cryptobot-cron
RUN dos2unix /etc/cron.d/cryptobot-cron

CMD service cron start && python -m cryptobot webserver --chat_id=$TELEGRAM_CHAT_ID
