import time
import hmac
import hashlib
import logging
from logging import error, info, warn

logging.basicConfig(level=logging.INFO)

import requests

class BinanceRawClientComponent:
    def __init__(self, binance_api_key: str, binance_api_secret: str, base_url: str):
        super().__init__()
        self.__binance_api_key = binance_api_key
        self.__binance_api_secret = binance_api_secret
        self.__base_url = base_url

    @classmethod
    def create(cls, binance_config: dict):
        return cls(
            base_url=binance_config['api']["base_url"],
            binance_api_key=binance_config['api']['key'],
            binance_api_secret=binance_config['api']['secret'],
        )

    def _sign_payload(self, payload: dict) -> str:
        """Sign the payload using API_SECRET"""
        query_string = "&".join([f"{k}={v}" for k, v in payload.items()])
        signature = hmac.new(
            self.__binance_api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _request(self, endpoint: str, params: dict):
        # dict is mutable !!!
        params = params.copy()
        # Adding signature
        params["recvWindow"] = 60000
        params["timestamp"] = int(time.time() * 1000)
        signature = self._sign_payload(params)
        params["signature"] = signature
        headers = {"X-MBX-APIKEY": self.__binance_api_key}
        url = self.__base_url + endpoint
        print(f'Params: {params}')
        #print(f'Headers: {headers}')
        try:
            r = requests.get(url, headers=headers, params=params)
            print(f'URL: {r.url}')
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error(f"HTTP error: '{e}' , Status code: '{r.status_code}' , Response text: '{r.text}'")
        except requests.exceptions.RequestException as e:
            error(f"Request failed: '{e}'")
        else:
            if r.text.strip():
                json_response = r.json()
            else:
                json_response = '{"empty_response": true}'
            info(f"Success! Response: '{json_response}'")
        return json_response

    def get_all_trades(self, binance_symbol: str) -> list[dict]:
        # Params
        params = {
            "symbol": binance_symbol,
            "limit": 1000,
            "fromId": 0,
        }

        result_list = []
        tries = 0

        while True and tries < 1000:
            tries += 1
            partial_list = self._request(endpoint="/api/v3/myTrades", params=params)
            for trade in partial_list:
                if int(trade['id']) > params['fromId']:
                    params['fromId'] = int(trade['id'])
            params['fromId'] += 1
            result_list += partial_list
            if len(partial_list) == 0:
                break
            if tries == 1000:
                error(f"max load myTrades tries: '{tries}'")

        return result_list

    """
    Get internal transfers history (Spot-to-Funding and vise-versa).
    transfer_type: MAIN_FUNDING, FUNDING_MAIN, MAIN_UMFUTURE, ...
    """
    def get_asset_transfer(self, type, start_time=None, end_time=None, limit=100):

        # Params
        params = {
            "limit": limit,
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if type:
            params["type"] = type

        return self._request(endpoint="/sapi/v1/asset/transfer", params=params)

    def get_asset_ledger(self, asset=None, start_time=None, end_time=None, limit=500):

        # Params
        params = {
            "limit": limit,
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if asset:
            params["asset"] = asset

        return self._request(endpoint="/sapi/v1/asset/ledger", params=params)

