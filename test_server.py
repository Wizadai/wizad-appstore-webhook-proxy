#!/usr/bin/env python3
"""
Simple test server to receive webhook notifications
Run this in a separate terminal to test your webhook proxy
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        print(f"\n=== Received webhook at {self.path} ===")
        print(f"Headers:")
        for header, value in self.headers.items():
            print(f"  {header}: {value}")
        
        print(f"\nBody:")
        try:
            # Try to parse as JSON for pretty printing
            json_body = json.loads(body.decode('utf-8'))
            print(json.dumps(json_body, indent=2))
        except:
            # If not JSON, print as text
            print(body.decode('utf-8'))
        
        print("=" * 50)
        
        # Send response
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format, *args):
        # Suppress default logging
        pass

def run_server(port=8001):
    server_address = ('', port)
    httpd = HTTPServer(server_address, WebhookHandler)
    print(f"Starting test webhook server on port {port}")
    print(f"Update your local.settings.json to use: http://localhost:{port}/webhook")
    print("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    run_server(port)
