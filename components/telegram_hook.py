import json
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

def create_hook_listener():
    @app.route("/telegram/cryptobot", methods=["POST"])
    def telegram_hook():
        data = request.get_json(force=True, silent=True) or {}
        print(data)
        try:
            result = subprocess.run(
                ["python", "main.py", "hook"],
                input=json.dumps(data),
                text=True,
                capture_output=True,
            )
            print(result)
            return jsonify({"status": "ok", "output": result.stdout})
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 500

    # __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765)
    return