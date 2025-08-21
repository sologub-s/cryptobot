import hashlib
import hmac
import json
import time
from logging import error, info

import requests

from cryptobot.ports.binance_api_adapter import BinanceApiAdapterPort


class BinanceApiAdapter(BinanceApiAdapterPort):
    def __init__(self,
        base_url: str,
        binance_api_key: str,
        binance_api_secret: str,
    ):
        super().__init__(base_url, binance_api_key, binance_api_secret)
        self.base_url = base_url
        self.binance_api_key = binance_api_key
        self.binance_api_secret = binance_api_secret

    @classmethod
    def create(cls, base_url: str, binance_api_key: str, binance_api_secret: str):
        return cls(
            base_url=base_url,
            binance_api_key=binance_api_key,
            binance_api_secret=binance_api_secret,
        )

    def _sign_payload(self, payload: dict) -> str:
        """Sign the payload using API_SECRET"""
        query_string = "&".join([f"{k}={v}" for k, v in payload.items()])
        signature = hmac.new(
            self.binance_api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature

    def request(self, endpoint: str, params: dict) -> dict | list:
        # dict is mutable !!!
        params = params.copy()
        # Adding signature
        params["recvWindow"] = 60000
        params["timestamp"] = int(time.time() * 1000)
        signature = self._sign_payload(params)
        params["signature"] = signature
        headers = {"X-MBX-APIKEY": self.binance_api_key}
        url = self.base_url + endpoint
        try:
            r = requests.get(url, headers=headers, params=params)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            json_response = {'status': e.response.status_code, 'error': e.response.text,}
            error(f"HTTP error: '{e}' , Status code: '{r.status_code}' , Response text: '{r.text}'")
        except requests.exceptions.RequestException as e:
            json_response = {'status': e.response.status_code, 'error': e.response.text,}
            error(f"Request failed: '{e}'")
        else:
            if r.text.strip():
                json_response = r.json()
            else:
                json_response = {"empty_response": True,}
            info(f"Success! Response: '{json.dumps(json_response)}'")
        print('json_response')
        print(json_response)
        return json_response