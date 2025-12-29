import json
import socket
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return """
    <html>
        <head>
            <title>Radio Controller</title>
            <style>
                body { font-family: sans-serif; text-align: center; padding: 50px; }
                .box { border: 1px solid #ccc; padding: 20px; border-radius: 8px; max-width: 500px; margin: 0 auto; }
                code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="box">
                <h1>Radio Controller Active</h1>
                <p>This is the <strong>Control API</strong> service.</p>
                <p>To listen to the radio or view the player, please visit your <strong>Icecast Service URL</strong>.</p>
                <p>Status: <span style="color: green;">OK</span></p>
                <p><small>API Endpoint: <code>/settings</code></small></p>
            </div>
        </body>
    </html>
    """

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

@app.route('/settings', methods=['GET', 'POST'])
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
    app.run(host=SETTINGS_HOST, port=SETTINGS_PORT, debug=False)
