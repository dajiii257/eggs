#!/usr/bin/env python3
"""
Frontend server with API proxy to backend
"""
import http.server
import socketserver
import urllib.request
import urllib.error
import json
import os

PORT = 3000
BACKEND_URL = "http://localhost:8080"  # Backend API URL

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy_request('GET')
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_request('POST')
        else:
            self.send_error(405, "Method Not Allowed")
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def proxy_request(self, method):
        """Proxy API requests to backend"""
        try:
            # Read request body for POST
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Build backend URL
            backend_path = f"{BACKEND_URL}{self.path}"
            
            # Create request
            if method == 'POST' and body:
                req = urllib.request.Request(
                    backend_path,
                    data=body,
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
            else:
                req = urllib.request.Request(backend_path, method=method)
            
            # Forward request to backend
            with urllib.request.urlopen(req, timeout=10) as response:
                response_body = response.read()
                
                # Send response
                self.send_response(response.status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response_body)
                
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_body = e.read()
            self.wfile.write(error_body)
            
        except Exception as e:
            print(f"Proxy error: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = json.dumps({"error": str(e)}).encode()
            self.wfile.write(error_response)
    
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def log_message(self, format, *args):
        if self.path.startswith('/api/'):
            print(f"[API Proxy] {self.path} -> {BACKEND_URL}{self.path}")
        else:
            print(f"[Static] {format%args}")

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print(f"""
╔══════════════════════════════════════════════════════╗
║        Frontend Server with API Proxy Started!       ║
╠══════════════════════════════════════════════════════╣
║   Frontend: http://localhost:{PORT}                  ║
║   Backend:  {BACKEND_URL}                  ║
║                                                      ║
║   📂 Static files: served from current directory     ║
║   🔄 API requests: proxied to backend                ║
║                                                      ║
║   Press Ctrl+C to stop                               ║
╚══════════════════════════════════════════════════════╝
""")

with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
