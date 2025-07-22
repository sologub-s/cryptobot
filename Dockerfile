FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD python main.py telegram_hook_listener --chat_id=$TELEGRAM_CHAT_ID
