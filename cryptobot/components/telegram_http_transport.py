import requests
from requests import Response

from cryptobot.ports.telegram_http_transport import TelegramHttpTransportComponentPort


class TelegramHttpTransportComponent():

    def request_post(self, url: str, data: dict|None=None, files: dict|None = None) -> Response | None:
        response = requests.post(url, data=data, files=files)
        #print(f"Telegram response: {response.status_code}, {response.text}")
        if not response.ok:
            print("ERROR: Cannot send message to Telegram:", response.text)
        return response