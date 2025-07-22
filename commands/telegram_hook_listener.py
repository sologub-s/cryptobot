import sys
from logging import error, info

from commands import AbstractCommand
import json
import subprocess
from flask import Flask, request, jsonify

class TelegramHookListenerCommand(AbstractCommand):

    def set_payload(self, host: str, port: int, chat_id: int):
        self._payload["host"] = host
        self._payload["port"] = port
        self._payload["chat_id"] = chat_id
        self._initialized = True
        return self

    def execute(self):
        if not self._initialized:
            print(f"ERROR: Command {self.__class__.__name__} is NOT initialized")
            return False

        print(f"Starting to listen to Telegram hook for chat_id={self._payload['chat_id']} ...")

        app = Flask(__name__)
        @app.route("/telegram/cryptobot", methods=["POST"])
        def telegram_hook():
            data = request.get_json(force=True, silent=True) or {}
            if "message" not in data:
                error(f"No 'message' field, data: {type(data)} : {data}")
                return jsonify({"status": "error", "error": str("No 'message' field")}), 200
            if self._payload["chat_id"] != data["message"]["chat"]["id"]:
                error(f"Payload chat_id: '{self._payload["chat_id"]}', data_message_chat_id: { data["message"]["chat"]["id"]}")
                return jsonify({"status": "error", "error": str("Forbidden chat_id")}), 403

            try:
                result = subprocess.run(
                    ["python", "main.py", "hook"],
                    input=json.dumps(data),
                    text=True,
                    #capture_output=True,
                    stdout=sys.stdout,
                    stderr=sys.stderr
                )
                info(f" result: {type(result)} : {result}")
                return jsonify({"status": "ok", "output": result.stdout})
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)}), 500

        app.run(host = self._payload["host"], port = self._payload["port"])
        return True