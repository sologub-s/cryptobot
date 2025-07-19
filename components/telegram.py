import requests

class TelegramComponent:
    def __init__(self, bot_token: str):
        super().__init__()
        self.bot_token = bot_token

    @classmethod
    def create(cls, telegram_config: dict):
        return cls(telegram_config["bot_token"])

    @property
    def bot_token(self):
        return self.__bot_token

    @bot_token.setter
    def bot_token(self, bot_token: str):
        self.__bot_token = bot_token

    def send_telegram_message(self, chat_id: int, text: str):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data = data)
        #print(f"Telegram response: {response.status_code}, {response.text}")
        if not response.ok:
            print("ERROR: Cannot send message to Telegram:", response.text)