import sys
from logging import error, info

from commands import AbstractCommand
import json
import subprocess
from flask import Flask, request, jsonify

from components import ServiceComponent


class WebserverCommand(AbstractCommand):

    def set_payload(self, host: str, port: int, chat_id: int):
        self._payload["host"] = host
        self._payload["port"] = port
        self._payload["chat_id"] = chat_id
        self._initialized = True
        return self

    def set_deps(self, service_component: ServiceComponent):
        self._service_component = service_component
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

            if data.get('message'):
                chat_id = data["message"]["chat"]["id"]
            elif data.get('callback_query'):
                chat_id = data["callback_query"]["message"]["chat"]["id"]
            else:
                error(f"No 'message' or 'callback_query' field, data: {type(data)} : {json.dumps(data)}")
                return jsonify({"status": "error", "error": str("No 'message' or 'callback_query' field")}), 200

            if chat_id != self._payload['chat_id']:
                err: str = str(f"This chat_id is not allowed: {chat_id}")
                self._service_component.send_telegram_message(chat_id, err)
                error(err)
                return jsonify({"status": "error", "error": err}), 200

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

        @app.route("/cron", methods=["GET"])
        def cron_hook():
            #data = request.get_json(force=True, silent=True) or {}

            try:
                result = subprocess.run(
                    ["python", "main.py", "cron", f"--chat_id={self._payload['chat_id']}"],
                    #input=json.dumps(data),
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