import json
import threading
import atexit
from http.server import BaseHTTPRequestHandler, HTTPServer


class _LoginHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/login":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
            except Exception:
                data = {}
            resp = {
                "username": data.get("username"),
                "role": "player",
                "message": "Login successful",
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp).encode())
        else:
            self.send_response(404)
            self.end_headers()


def _start_server():
    server = HTTPServer(("127.0.0.1", 8000), _LoginHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


_server = _start_server()
atexit.register(_server.shutdown)
