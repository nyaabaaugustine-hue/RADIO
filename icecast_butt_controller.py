import sys
import json
import subprocess
import requests
import webbrowser
import threading
import socket
from flask import Flask, request, jsonify
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox, QGroupBox, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer

# Flask Server Implementation
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

def run_server():
    try:
        server.run(host=SETTINGS_HOST, port=SETTINGS_PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Server error: {e}")

class IcecastButtController(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unified Icecast/BUTT Controller")
        self.setGeometry(100, 100, 800, 600)

        self.butt_process = None
        self.config_file = "config.json"
        self.host = "localhost"
        self.port = 8000

        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout()
        tab_widget = QTabWidget()
        controller_page = QWidget()
        controller_layout = QVBoxLayout()
        controller_page.setLayout(controller_layout)
        admin_page = QWidget()
        admin_layout = QVBoxLayout()
        admin_page.setLayout(admin_layout)

        # Connection & Auth Section
        connection_auth_group = QGroupBox("Connection & Authentication")
        connection_auth_layout = QFormLayout()

        self.admin_user_input = QLineEdit("admin")
        self.admin_password_input = QLineEdit("")
        self.admin_password_input.setEchoMode(QLineEdit.Password)
        self.source_password_input = QLineEdit("")
        self.source_password_input.setEchoMode(QLineEdit.Password)
        self.relay_password_input = QLineEdit()
        self.relay_password_input.setEchoMode(QLineEdit.Password)
        self.host_input = QLineEdit(self.host)
        self.port_input = QLineEdit(str(self.port))
        self.port_input.setValidator(None)

        connection_auth_layout.addRow("Admin User:", self.admin_user_input)
        connection_auth_layout.addRow("Admin Password:", self.admin_password_input)
        connection_auth_layout.addRow("Source Password:", self.source_password_input)
        connection_auth_layout.addRow("Relay Password (Optional):", self.relay_password_input)
        connection_auth_layout.addRow("Host:", self.host_input)
        connection_auth_layout.addRow("Port:", self.port_input)

        self.test_connection_button = QPushButton("Test Connection")
        self.test_connection_button.clicked.connect(self.test_icecast_connection)
        connection_auth_layout.addRow(self.test_connection_button)

        connection_auth_group.setLayout(connection_auth_layout)
        controller_layout.addWidget(connection_auth_group)

        # Stream Info Section
        stream_info_group = QGroupBox("Stream Information")
        stream_info_layout = QFormLayout()

        self.stream_title_input = QLineEdit("My Awesome Stream")
        self.stream_description_input = QLineEdit("A fantastic audio experience")
        self.stream_genre_input = QLineEdit("Various")
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["64", "96", "128", "192", "256", "320"])
        self.bitrate_combo.setCurrentText("128")
        self.channels_combo = QComboBox()
        self.channels_combo.addItems(["1", "2"])
        self.channels_combo.setCurrentText("2")
        self.samplerate_combo = QComboBox()
        self.samplerate_combo.addItems(["22050", "44100", "48000"])
        self.samplerate_combo.setCurrentText("44100")
        self.mountpoint_input = QLineEdit("/live")
        self.update_metadata_button = QPushButton("Update Metadata")
        self.update_metadata_button.clicked.connect(self.update_metadata)
        self.check_mount_button = QPushButton("Check Mount")
        self.check_mount_button.clicked.connect(self.check_mount_exists)

        stream_info_layout.addRow("Title:", self.stream_title_input)
        stream_info_layout.addRow("Description:", self.stream_description_input)
        stream_info_layout.addRow("Genre:", self.stream_genre_input)
        stream_info_layout.addRow("Bitrate (kbps):", self.bitrate_combo)
        stream_info_layout.addRow("Channels:", self.channels_combo)
        stream_info_layout.addRow("Samplerate (Hz):", self.samplerate_combo)
        stream_info_layout.addRow("Mountpoint:", self.mountpoint_input)

        stream_info_group.setLayout(stream_info_layout)
        controller_layout.addWidget(stream_info_group)

        # Stream Control Section
        stream_control_group = QGroupBox("Stream Control")
        stream_control_layout = QHBoxLayout()

        self.start_stream_button = QPushButton("Start Stream")
        self.start_stream_button.clicked.connect(self.start_stream)
        self.stop_stream_button = QPushButton("Stop Stream")
        self.stop_stream_button.clicked.connect(self.stop_stream)
        self.status_indicator = QLabel("Status: Idle")
        self.status_indicator.setStyleSheet("color: orange;")

        stream_control_layout.addWidget(self.start_stream_button)
        stream_control_layout.addWidget(self.stop_stream_button)
        stream_control_layout.addWidget(self.status_indicator)

        stream_control_group.setLayout(stream_control_layout)
        controller_layout.addWidget(stream_control_group)

        # Live Stats Section
        live_stats_group = QGroupBox("Live Statistics")
        live_stats_layout = QFormLayout()

        self.listeners_label = QLabel("Current: 0")
        self.peak_listeners_label = QLabel("Peak: 0")
        self.bytes_sent_label = QLabel("Total Bytes Sent: 0")
        self.stream_url_label = QLineEdit("http://localhost:8000/live")
        self.stream_url_label.setReadOnly(True)
        self.copy_url_button = QPushButton("Copy URL")
        self.copy_url_button.clicked.connect(self.copy_stream_url)
        self.open_url_button = QPushButton("Open URL")
        self.open_url_button.clicked.connect(self.open_stream_url)

        live_stats_layout.addRow("Listeners:", self.listeners_label)
        live_stats_layout.addRow("Peak Listeners:", self.peak_listeners_label)
        live_stats_layout.addRow("Bytes Sent:", self.bytes_sent_label)
        live_stats_layout.addRow("Stream URL:", self.stream_url_label)
        live_stats_layout.addRow("", self.copy_url_button)
        live_stats_layout.addRow("", self.open_url_button)

        live_stats_group.setLayout(live_stats_layout)
        controller_layout.addWidget(live_stats_group)

        # Config Management Section
        config_management_group = QGroupBox("Configuration Management")
        config_management_layout = QHBoxLayout()

        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self.save_settings)
        self.load_settings_button = QPushButton("Load Settings")
        self.load_settings_button.clicked.connect(self.load_settings)

        config_management_layout.addWidget(self.save_settings_button)
        config_management_layout.addWidget(self.load_settings_button)
        self.open_admin_button = QPushButton("Open Admin")
        self.open_admin_button.clicked.connect(self.open_admin)
        config_management_layout.addWidget(self.open_admin_button)
        self.test_admin_button = QPushButton("Test Admin")
        self.test_admin_button.clicked.connect(self.test_admin)
        config_management_layout.addWidget(self.test_admin_button)

        config_management_group.setLayout(config_management_layout)
        admin_layout.addWidget(config_management_group)

        admin_tools_group = QGroupBox("Mount & Metadata")
        admin_tools_layout = QHBoxLayout()
        admin_tools_layout.addWidget(self.update_metadata_button)
        admin_tools_layout.addWidget(self.check_mount_button)
        admin_tools_group.setLayout(admin_tools_layout)
        admin_layout.addWidget(admin_tools_group)

        settings_api_group = QGroupBox("Settings API")
        settings_api_layout = QFormLayout()
        self.settings_url_field = QLineEdit(f"http://{SETTINGS_HOST}:{SETTINGS_PORT}/settings")
        self.settings_url_field.setReadOnly(True)
        self.copy_settings_url_button = QPushButton("Copy Settings URL")
        self.copy_settings_url_button.clicked.connect(self.copy_settings_url)
        self.open_settings_url_button = QPushButton("Open Settings URL")
        self.open_settings_url_button.clicked.connect(self.open_settings_url)
        self.settings_status_label = QLabel("Status: Unknown")
        self.test_settings_api_button = QPushButton("Test Settings API")
        self.test_settings_api_button.clicked.connect(self.test_settings_api)
        settings_api_layout.addRow("URL:", self.settings_url_field)
        settings_api_layout.addRow("", self.copy_settings_url_button)
        settings_api_layout.addRow("", self.open_settings_url_button)
        settings_api_layout.addRow("Status:", self.settings_status_label)
        settings_api_layout.addRow("", self.test_settings_api_button)
        settings_api_group.setLayout(settings_api_layout)
        admin_layout.addWidget(settings_api_group)

        tab_widget.addTab(controller_page, "Stream")
        tab_widget.addTab(admin_page, "Admin")

        main_layout.addWidget(tab_widget)

        self.setLayout(main_layout)

        # Timer for updating live stats
        self.stats_timer = QTimer(self)
        self.stats_timer.setInterval(5000) # Update every 5 seconds
        self.stats_timer.timeout.connect(self.update_live_stats)
        self.stats_timer.start()

    def test_icecast_connection(self):
        host = (self.host_input.text() or self.host).strip()
        try:
            port = int((self.port_input.text() or str(self.port)).strip())
        except Exception:
            port = self.port
        try:
            # Prefer JSON status endpoint when available
            json_resp = requests.get(f"http://{host}:{port}/status-json.xsl", timeout=5)
            if json_resp.ok and json_resp.headers.get("Content-Type", "").lower().startswith("application/json"):
                QMessageBox.information(self, "Test Connection", "Successfully connected to Icecast server!")
                return
            # Fallback to classic status page
            response = requests.get(f"http://{host}:{port}/status.xsl", timeout=5)
            if response.ok:
                QMessageBox.information(self, "Test Connection", "Successfully connected to Icecast server!")
            else:
                QMessageBox.warning(self, "Test Connection", f"Could not connect to Icecast server. Status code: {response.status_code}")
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Test Connection", "Failed to connect to Icecast server. Is it running?")
        except Exception as e:
            QMessageBox.critical(self, "Test Connection", f"An error occurred: {e}")

    def start_stream(self):
        if self.butt_process and self.butt_process.poll() is None:
            QMessageBox.warning(self, "Start Stream", "BUTT is already running.")
            return

        source_password = self.source_password_input.text()
        stream_title = self.stream_title_input.text()
        stream_description = self.stream_description_input.text()
        stream_genre = self.stream_genre_input.text()
        bitrate = self.bitrate_combo.currentText()
        channels = self.channels_combo.currentText()
        samplerate = self.samplerate_combo.currentText()
        host = (self.host_input.text() or self.host).strip()
        try:
            port = int((self.port_input.text() or str(self.port)).strip())
        except Exception:
            port = self.port
        mount = (self.mountpoint_input.text() or "/live").strip()
        if not mount.startswith("/"):
            mount = "/" + mount

        # Construct BUTT command. Assuming 'butt.exe' is in the system's PATH or current directory.
        # You might need to provide the full path to butt.exe if it's not.
        butt_command = [
            "butt",
            "-s", source_password,
            "-h", host,
            "-p", str(port),
            "-m", mount,
            "-t", stream_title,
            "-d", stream_description,
            "-g", stream_genre,
            "-b", bitrate,
            "-c", channels,
            "-r", samplerate,
            "-D" # Run in daemon mode (non-interactive)
        ]

        try:
            self.butt_process = subprocess.Popen(butt_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            QMessageBox.information(self, "Start Stream", "BUTT started successfully!")
            self.status_indicator.setText("Status: Streaming")
            self.status_indicator.setStyleSheet("color: green;")
        except FileNotFoundError:
            QMessageBox.critical(self, "Start Stream Error", "BUTT executable not found. Make sure 'butt.exe' is in your system's PATH.")
        except Exception as e:
            QMessageBox.critical(self, "Start Stream Error", f"Failed to start BUTT: {e}")

    def stop_stream(self):
        if self.butt_process and self.butt_process.poll() is None:
            self.butt_process.terminate()
            self.butt_process.wait() # Wait for the process to actually terminate
            QMessageBox.information(self, "Stop Stream", "BUTT stopped successfully.")
            self.status_indicator.setText("Status: Idle")
            self.status_indicator.setStyleSheet("color: orange;")
        else:
            QMessageBox.warning(self, "Stop Stream", "BUTT is not running.")

    def update_live_stats(self):
        host = (self.host_input.text() or self.host).strip()
        try:
            port = int((self.port_input.text() or str(self.port)).strip())
        except Exception:
            port = self.port
        mount = (self.mountpoint_input.text() or "/live").strip()
        if not mount.startswith("/"):
            mount = "/" + mount
        url = f"http://{host}:{port}/status-json.xsl"
        try:
            resp = requests.get(url, timeout=5)
            if not resp.ok:
                return
            data = resp.json()
            icestats = data.get("icestats", {})
            source = icestats.get("source")

            selected_listeners = 0
            selected_peak = 0
            selected_bytes = 0
            selected_listenurl = f"http://{host}:{port}{mount}"

            def extract_bytes(s):
                if isinstance(s, dict):
                    if "total_bytes" in s:
                        return int(s.get("total_bytes") or 0)
                    if "total_kbytes" in s:
                        try:
                            return int(float(s.get("total_kbytes") or 0) * 1024)
                        except Exception:
                            return 0
                return 0

            # Handle single or multiple sources
            if isinstance(source, list):
                for s in source:
                    listenurl = s.get("listenurl", "")
                    if mount and listenurl.endswith(mount):
                        selected_listeners = int(s.get("listeners") or 0)
                        selected_peak = int(s.get("listener_peak") or 0)
                        selected_bytes = extract_bytes(s)
                        selected_listenurl = listenurl or selected_listenurl
                        break
            elif isinstance(source, dict):
                selected_listeners = int(source.get("listeners") or 0)
                selected_peak = int(source.get("listener_peak") or 0)
                selected_bytes = extract_bytes(source)
                selected_listenurl = source.get("listenurl", selected_listenurl)

            self.listeners_label.setText(f"Current: {selected_listeners}")
            self.peak_listeners_label.setText(f"Peak: {selected_peak}")
            self.bytes_sent_label.setText(f"Total Bytes Sent: {selected_bytes}")
            self.stream_url_label.setText(selected_listenurl)
        except Exception:
            # Silent failure is preferable to disruptive popups for periodic updates
            pass

    def copy_stream_url(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.stream_url_label.text())
        QMessageBox.information(self, "Copy URL", "Stream URL copied to clipboard!")

    def copy_settings_url(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.settings_url_field.text())
        QMessageBox.information(self, "Copy Settings URL", "Settings URL copied to clipboard!")

    def test_settings_api(self):
        url = self.settings_url_field.text().strip()
        try:
            r = requests.get(url.replace("/settings", "/"), timeout=3)
            if r.ok:
                self.settings_status_label.setText("Status: Online")
                self.settings_status_label.setStyleSheet("color: green;")
                QMessageBox.information(self, "Settings API", "Settings API is reachable.")
                return
        except Exception:
            pass
        self.settings_status_label.setText("Status: Offline")
        self.settings_status_label.setStyleSheet("color: red;")
        QMessageBox.warning(self, "Settings API", "Settings API is not reachable.")

    def save_settings(self):
        settings = {
            "admin_user": self.admin_user_input.text(),
            "admin_password": self.admin_password_input.text(),
            "source_password": self.source_password_input.text(),
            "relay_password": self.relay_password_input.text(),
            "host": (self.host_input.text() or self.host).strip(),
            "port": (self.port_input.text() or str(self.port)).strip(),
            "stream_title": self.stream_title_input.text(),
            "stream_description": self.stream_description_input.text(),
            "stream_genre": self.stream_genre_input.text(),
            "bitrate": self.bitrate_combo.currentText(),
            "channels": self.channels_combo.currentText(),
            "samplerate": self.samplerate_combo.currentText(),
            "mountpoint": (self.mountpoint_input.text() or "/live").strip(),
        }
        try:
            with open(self.config_file, "w") as f:
                json.dump(settings, f, indent=4)
            QMessageBox.information(self, "Save Settings", "Settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Save Settings Error", f"Failed to save settings: {e}")

    def load_settings(self):
        try:
            with open(self.config_file, "r") as f:
                settings = json.load(f)
            self.admin_user_input.setText(settings.get("admin_user", "admin"))
            self.admin_password_input.setText(settings.get("admin_password", ""))
            self.source_password_input.setText(settings.get("source_password", ""))
            self.relay_password_input.setText(settings.get("relay_password", ""))
            self.host_input.setText(settings.get("host", self.host))
            self.port_input.setText(settings.get("port", str(self.port)))
            self.stream_title_input.setText(settings.get("stream_title", "My Awesome Stream"))
            self.stream_description_input.setText(settings.get("stream_description", "A fantastic audio experience"))
            self.stream_genre_input.setText(settings.get("stream_genre", "Various"))
            self.bitrate_combo.setCurrentText(settings.get("bitrate", "128"))
            self.channels_combo.setCurrentText(settings.get("channels", "2"))
            self.samplerate_combo.setCurrentText(settings.get("samplerate", "44100"))
            self.mountpoint_input.setText(settings.get("mountpoint", "/live"))
            try:
                host = (self.host_input.text() or self.host).strip()
                port = int((self.port_input.text() or str(self.port)).strip())
            except Exception:
                host = self.host
                port = self.port
            mount = (self.mountpoint_input.text() or "/live").strip()
            if not mount.startswith("/"):
                mount = "/" + mount
            self.stream_url_label.setText(f"http://{host}:{port}{mount}")
            QMessageBox.information(self, "Load Settings", "Settings loaded successfully!")
        except FileNotFoundError:
            QMessageBox.warning(self, "Load Settings", "No config file found. Using default settings.")
        except Exception as e:
            QMessageBox.critical(self, "Load Settings Error", f"Failed to load settings: {e}")

    def open_stream_url(self):
        url = self.stream_url_label.text().strip()
        if url:
            webbrowser.open(url)

    def open_settings_url(self):
        url = self.settings_url_field.text().strip()
        if url:
            webbrowser.open(url)

    def check_mount_exists(self):
        host = (self.host_input.text() or self.host).strip()
        try:
            port = int((self.port_input.text() or str(self.port)).strip())
        except Exception:
            port = self.port
        mount = (self.mountpoint_input.text() or "/live").strip()
        if not mount.startswith("/"):
            mount = "/" + mount
        try:
            resp = requests.get(f"http://{host}:{port}/status-json.xsl", timeout=5)
            if not resp.ok:
                QMessageBox.warning(self, "Check Mount", f"Failed to fetch status. Code: {resp.status_code}")
                return
            data = resp.json()
            icestats = data.get("icestats", {})
            source = icestats.get("source")
            found = False
            if isinstance(source, list):
                for s in source:
                    listenurl = s.get("listenurl", "")
                    if listenurl.endswith(mount):
                        found = True
                        break
            elif isinstance(source, dict):
                listenurl = source.get("listenurl", "")
                if listenurl.endswith(mount):
                    found = True
            if found:
                QMessageBox.information(self, "Check Mount", f"Mount {mount} is active.")
            else:
                QMessageBox.warning(self, "Check Mount", f"Mount {mount} not found or inactive.")
        except Exception as e:
            QMessageBox.critical(self, "Check Mount Error", f"Error checking mount: {e}")

    def update_metadata(self):
        host = (self.host_input.text() or self.host).strip()
        try:
            port = int((self.port_input.text() or str(self.port)).strip())
        except Exception:
            port = self.port
        mount = (self.mountpoint_input.text() or "/live").strip()
        if not mount.startswith("/"):
            mount = "/" + mount
        title = self.stream_title_input.text().strip()
        description = self.stream_description_input.text().strip()
        genre = self.stream_genre_input.text().strip()
        params = {
            "mount": mount,
            "mode": "updinfo",
            "song": title or "Untitled"
        }
        admin_user = self.admin_user_input.text().strip()
        admin_pass = self.admin_password_input.text()
        try:
            url = f"http://{host}:{port}/admin/metadata"
            resp = requests.get(url, params=params, auth=(admin_user, admin_pass), timeout=5)
            if resp.status_code == 401:
                source_pass = self.source_password_input.text()
                resp = requests.get(url, params=params, auth=("source", source_pass), timeout=5)
            ok1 = resp.ok
            params2 = {"mount": mount, "mode": "updmeta"}
            if title:
                params2["title"] = title
            if description:
                params2["description"] = description
            if genre:
                params2["genre"] = genre
            resp2 = requests.get(url, params=params2, auth=(admin_user, admin_pass), timeout=5)
            if resp2.status_code == 401:
                source_pass = self.source_password_input.text()
                resp2 = requests.get(url, params=params2, auth=("source", source_pass), timeout=5)
            ok2 = resp2.ok
            if ok1 or ok2:
                QMessageBox.information(self, "Update Metadata", "Metadata updated.")
            else:
                QMessageBox.warning(self, "Update Metadata", f"Failed. Codes: {resp.status_code}, {resp2.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "Update Metadata Error", f"Error updating metadata: {e}")

    def open_admin(self):
        host = (self.host_input.text() or self.host).strip()
        try:
            port = int((self.port_input.text() or str(self.port)).strip())
        except Exception:
            port = self.port
        url = f"http://{host}:{port}/admin"
        try:
            resp = requests.get(url, timeout=5)
            if not resp.ok:
                QMessageBox.warning(self, "Open Admin", f"Admin unreachable (code {resp.status_code}). Opening browser anyway.")
            opened = webbrowser.open(url)
            if not opened:
                clipboard = QApplication.clipboard()
                clipboard.setText(url)
                QMessageBox.information(self, "Open Admin", "Failed to open browser. URL copied to clipboard.")
        except Exception:
            opened = webbrowser.open(url)
            if not opened:
                clipboard = QApplication.clipboard()
                clipboard.setText(url)
                QMessageBox.information(self, "Open Admin", "Failed to open browser. URL copied to clipboard.")

    def test_admin(self):
        host = (self.host_input.text() or self.host).strip()
        try:
            port = int((self.port_input.text() or str(self.port)).strip())
        except Exception:
            port = self.port
        url = f"http://{host}:{port}/admin"
        try:
            resp = requests.get(url, timeout=5)
            if resp.ok:
                QMessageBox.information(self, "Test Admin", "Admin is reachable.")
            else:
                QMessageBox.warning(self, "Test Admin", f"Admin responded with status {resp.status_code}.")
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(self, "Test Admin", "Failed to connect to Admin. Is Icecast running?")
        except Exception as e:
            QMessageBox.critical(self, "Test Admin", f"Error testing Admin: {e}")

if __name__ == "__main__":
    # Start Flask server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    app = QApplication(sys.argv)
    controller = IcecastButtController()
    controller.show()
    sys.exit(app.exec_())
