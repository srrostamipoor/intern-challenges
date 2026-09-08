import os
import http.server
import socketserver


PORT = 8080
SERVER_ID = os.environ.get("SERVER_ID","unknown")

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type","text/plain")
        self.end_headers()
        message = f"Response from SERVER {SERVER_ID}\n"
        self.wfile.write(message.encode())

with socketserver.TCPServer(("0.0.0.0",PORT),Handler) as httpd:
        print(f"Server {SERVER_ID} running on port {PORT}")
        httpd.serve_forever()


