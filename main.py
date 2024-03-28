from datetime import datetime
import json
import logging
import mimetypes
import socket

from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from urllib.parse import unquote_plus, urlparse

from jinja2 import Environment, FileSystemLoader


BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_HOST = "0.0.0.0"
HTTP_PORT = 3000
SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 5000
STORAGE = Path("storage/data.json")
# STORAGE = BASE_DIR / "storage" / "data.json"

if not STORAGE.parent.exists():
    Path.mkdir(STORAGE.parent)


jinja = Environment(loader=FileSystemLoader("templates"))


class GoitFrameWork(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urlparse(self.path)
        match route.path:
            case "/":
                # self.send_html("error.html")
                self.render_template("home.html")
            case "/message":
                # self.send_html("message.html")
                self.render_template("message.html")
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.render_template("error.html")

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        with open(filename, "rb") as file:
            self.wfile.write(file.read())

    def render_template(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        template = jinja.get_template(filename)
        html = template.render()
        self.wfile.write(html.encode())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Content-Type", mime_type)
        else:
            self.send_header("Content-Type", "text/plain")
        self.end_headers()
        with open(filename, "rb") as file:
            self.wfile.write(file.read())

    def do_POST(self):
        size = self.headers.get("Content-Length")
        data = self.rfile.read(int(size))

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header("Location", "/message")
        self.end_headers()


def save_data_from_form(data):
    parse_data = unquote_plus(data.decode("utf-8"))
    cur_date = datetime.now().isoformat()
    try:
        parse_dict = {
            key: value for key, value in [el.split("=") for el in parse_data.split("&")]
        }
        exiting_data = {}
        if STORAGE.exists():
            with open(STORAGE, "r", encoding="utf-8") as file:
                exiting_data = json.load(file)

        exiting_data[cur_date] = parse_dict
        with open(STORAGE, "w", encoding="utf-8") as file:
            json.dump(exiting_data, file, ensure_ascii=False, indent=4)
    except ValueError as e:
        logging.error(e)
    except OSError as e:
        logging.error(e)


def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, GoitFrameWork)
    logging.info(f"HTTP server is started on {host}:{port}")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info(f"Socket server is started on {host}:{port}")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            save_data_from_form(msg)
            logging.info(f"Socket received: {address}: {msg}")
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(threadName)s - %(message)s")
    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()
    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()
