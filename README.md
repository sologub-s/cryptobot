telegram hooks:
curl -F "url=https://cryptobot-hook.solohub.pp.ua/telegram/cryptobot" https://api.telegram.org/bot{TOKEN}/setWebhook

telegram hook listener:
python main.py webserver --chat_id=$TELEGRAM_CHAT_ID

docker:
docker build -t cryptobot . && docker run --env-file .env -d --name cryptobot --network=web -p 8765:8765 --restart unless-stopped cryptobot