import json
import socket
from flask import Flask, request, jsonify

server = Flask(__name__)

@server.route('/', methods=['GET'])
def index():
    return jsonify({"ok": True, "routes": ["/settings"]})

SETTINGS_HOST = '127.0.0.1'

def find_free_port(start=8001, tries=20):
    for p in range(start, start + tries):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((SETTINGS_HOST, p))
            s.close()
            return p
        except OSError:
            s.close()
            continue
    return start

SETTINGS_PORT = find_free_port()

@server.route('/settings', methods=['GET', 'POST'])
def settings():
    config_file = "config.json"
    if request.method == 'GET':
        try:
            with open(config_file, 'r') as f:
                settings = json.load(f)
            return jsonify(settings)
        except FileNotFoundError:
            return jsonify({"error": "Config file not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    elif request.method == 'POST':
        try:
            new_settings = request.json
            with open(config_file, 'w') as f:
                json.dump(new_settings, f, indent=4)
            return jsonify({"message": "Settings saved successfully"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    server.run(host=SETTINGS_HOST, port=SETTINGS_PORT, debug=False)
