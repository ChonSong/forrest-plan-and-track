#!/usr/bin/env python3
"""
OneTag proxy — no 401, no Cloudflare challenges.
First visit: shows login form (200 OK).
After login: sets cookie, proxies to Streamlit on localhost:8502.
All requests (incl. WebSocket) are proxied with the session cookie.
"""
import base64
import hashlib
import hmac
import http.client
import http.server
import json
import os
import select
import socket
import sys
import time

LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8501
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8502

AUTH_USER = "sa"
AUTH_PASS = "dawnofdarren"
SECRET = hashlib.sha256(b"onetag-hmas-sydney-2026").hexdigest()
SESSION_COOKIE = "session=" + hmac.new(SECRET.encode(), AUTH_USER.encode(), hashlib.sha256).hexdigest()[:16]


def proxy_http(method, path, headers, body):
    skip = {"host", "authorization", "connection", "transfer-encoding",
            "keep-alive", "proxy-connection", "upgrade",
            "sec-websocket-key", "sec-websocket-version"}
    fwd = {k: v for k, v in headers.items() if k.lower() not in skip}
    fwd["Host"] = BACKEND_HOST + ":" + str(BACKEND_PORT)
    try:
        conn = http.client.HTTPConnection(BACKEND_HOST, BACKEND_PORT, timeout=120)
        conn.request(method, path, body=body, headers=fwd)
        resp = conn.getresponse()
        hdrs = [(h, v) for h, v in resp.getheaders()
                if h.lower() not in ("transfer-encoding", "connection")]
        body = resp.read()
        conn.close()
        return resp.status, hdrs, body
    except Exception as e:
        return 502, [("Content-Type", "text/plain")], ("Backend error: " + str(e)).encode()


def tunnel_ws(client_sock, backend_sock):
    socks = [client_sock, backend_sock]
    try:
        while True:
            readable, _, err = select.select(socks, [], socks, 120)
            if err or not readable:
                break
            for s in readable:
                try:
                    data = s.recv(65536)
                    if not data:
                        return
                    (backend_sock if s is client_sock else client_sock).sendall(data)
                except (ConnectionResetError, BrokenPipeError, OSError):
                    return
    except Exception:
        pass
    finally:
        try:
            backend_sock.close()
        except Exception:
            pass


LOGIN_PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OneTag — Login</title>
<style>
body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:2rem;width:320px;box-shadow:0 4px 24px rgba(0,0,0,.3)}
h1{font-size:1.3rem;margin:0 0 .25rem;color:#f8fafc}
.sub{color:#94a3b8;font-size:.85rem;margin-bottom:1.5rem}
label{display:block;font-size:.8rem;color:#94a3b8;margin-bottom:.25rem;margin-top:.75rem}
input[type=text],input[type=password]{width:100%;padding:.5rem .75rem;border:1px solid #475569;border-radius:6px;background:#0f172a;color:#e2e8f0;font-size:.9rem;box-sizing:border-box}
input:focus{outline:none;border-color:#60a5fa}
button{width:100%;margin-top:1.25rem;padding:.6rem;background:#2563eb;color:#fff;border:none;border-radius:6px;font-size:.9rem;cursor:pointer}
button:hover{background:#1d4ed8}
</style></head><body>
<div class="card">
<h1>🏭 OneTag HMAS Sydney</h1>
<p class="sub">Database Explorer — Log in to continue</p>
<form method="POST" action="/_auth/login">
<label>Username</label><input type="text" name="username" required autofocus>
<label>Password</label><input type="password" name="password" required>
<button type="submit">Log In</button>
</form>
</div></body></html>"""


class ProxyHandler(http.server.BaseHTTPRequestHandler):

    def _has_session(self):
        cookie = self.headers.get("Cookie", "")
        for part in cookie.split(";"):
            if "session=" in part:
                return True
        return False

    def _handle(self):
        # Auth login form submission
        if self.path == "/_auth/login" and self.command == "POST":
            cl = int(self.headers.get("Content-Length", 0) or "0")
            body = self.rfile.read(cl) if cl > 0 else b""
            params = dict(p.split("=", 1) for p in body.decode("utf-8", errors="ignore").split("&") if "=" in p)
            user = params.get("username", "")
            pwd = params.get("password", "")
            if user == AUTH_USER and pwd == AUTH_PASS:
                # Set cookie and redirect to main page
                self.send_response(302)
                self.send_header("Set-Cookie", SESSION_COOKIE + "; Path=/; HttpOnly; SameSite=Lax; Max-Age=3600")
                self.send_header("Location", "/")
                self.end_headers()
                return
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(LOGIN_PAGE.replace("Log in to continue", "Invalid credentials — try again").encode())
                return

        # Check session
        if not self._has_session():
            # Show login page (200 OK — no 401, no Cloudflare challenge)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(LOGIN_PAGE)))
            self.end_headers()
            self.wfile.write(LOGIN_PAGE.encode())
            return

        # WebSocket?
        upgrade = self.headers.get("Upgrade", "").lower()
        ws_key = self.headers.get("Sec-WebSocket-Key")
        if upgrade == "websocket" and ws_key:
            self._handle_ws(ws_key)
            return

        # HTTP proxy to streamlit
        cl = int(self.headers.get("Content-Length", 0) or "0")
        body = self.rfile.read(cl) if cl > 0 else None
        status, hdrs, resp_body = proxy_http(self.command, self.path, dict(self.headers), body)
        self.send_response(status)
        for h, v in hdrs:
            self.send_header(h, v)
        self.end_headers()
        if resp_body:
            self.wfile.write(resp_body)

    def do_GET(self):
        self._handle()

    def do_POST(self):
        self._handle()

    def do_PUT(self):
        self._handle()

    def do_DELETE(self):
        self._handle()

    def do_PATCH(self):
        self._handle()

    def do_HEAD(self):
        self._handle()

    def _handle_ws(self, ws_key):
        magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        accept = base64.b64encode(hashlib.sha1((ws_key + magic).encode()).digest()).decode()

        self.send_response(101)
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept", accept)
        self.end_headers()

        bs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            bs.connect((BACKEND_HOST, BACKEND_PORT))
            req = "GET " + self.path + " HTTP/1.1\r\n"
            req += "Host: " + BACKEND_HOST + ":" + str(BACKEND_PORT) + "\r\n"
            req += "Upgrade: websocket\r\n"
            req += "Connection: Upgrade\r\n"
            req += "Sec-WebSocket-Key: " + ws_key + "\r\n"
            req += "Sec-WebSocket-Version: 13\r\n"
            req += "Cookie: " + SESSION_COOKIE + "\r\n"
            origin = self.headers.get("Origin")
            if origin:
                req += "Origin: " + origin + "\r\n"
            req += "\r\n"
            bs.sendall(req.encode())

            resp_data = b""
            while b"\r\n\r\n" not in resp_data:
                chunk = bs.recv(4096)
                if not chunk:
                    return
                resp_data += chunk

            he = resp_data.find(b"\r\n\r\n") + 4
            body_part = resp_data[he:]
            if body_part:
                self.connection.sendall(body_part)

            self.connection.setblocking(True)
            bs.setblocking(True)
            tunnel_ws(self.connection, bs)
        except Exception:
            pass
        finally:
            try:
                bs.close()
            except Exception:
                pass

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    server = http.server.HTTPServer((LISTEN_HOST, LISTEN_PORT), ProxyHandler)
    print("OneTag proxy on " + LISTEN_HOST + ":" + str(LISTEN_PORT))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
