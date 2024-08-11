#!/usr/bin/env python3
import http.server, os, socketserver


class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith("/"):
            if os.path.exists(self.path[1:] + "index.wpym"):
                self.path += "index.wpym"
            elif os.path.exists(self.path[1:] + "index.html"):
                self.path += "index.html"

        return super().do_GET()


socket = socketserver.TCPServer(("0.0.0.0", 8950), CustomHTTPRequestHandler)
socket.serve_forever()
