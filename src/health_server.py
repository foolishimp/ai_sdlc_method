#!/usr/bin/env python
"""
A simple HTTP server with a /health endpoint.

Implements: REQ-F-HEALTH-001
"""
import http.server
import socketserver
import argparse

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def main():
    parser = argparse.ArgumentParser(description="Simple Health Check Server")
    parser.add_argument("--port", type=int, default=8888, help="Port to run the server on")
    args = parser.parse_args()

    with socketserver.TCPServer(("", args.port), HealthCheckHandler) as httpd:
        print(f"Serving at port {args.port}")
        httpd.serve_forever()

if __name__ == "__main__":
    main()
