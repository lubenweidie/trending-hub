"""本地 HTTP 图片服务 — 将本地图片目录暴露给浏览器，解决跨域问题"""
import http.server
import threading
import socketserver
from pathlib import Path


def start_image_server(root_dir: Path) -> int:
    """在 18900-18909 端口范围内启动 CORS 图片服务器，返回实际端口号"""

    class CORSHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root_dir), **kwargs)

        def end_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Connection", "close")
            super().end_headers()

        def do_OPTIONS(self):
            self.send_response(200)
            self.end_headers()

        def log_message(self, format, *args):
            pass

    for port in range(18900, 18910):
        try:
            server = socketserver.TCPServer(("127.0.0.1", port), CORSHandler)
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            return port
        except OSError:
            continue
    raise RuntimeError("无法启动图片服务器（端口18900-18909均被占用）")
