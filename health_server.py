"""
Health Check Server for Render.com
Prevents free tier from sleeping by providing HTTP endpoint
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import os

class HealthHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK - Stock Trading Bot is running')
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = b"""
            <html>
            <body>
                <h1>Stock Trading Bot</h1>
                <p>Status: Running</p>
                <p>Health Check: <a href="/health">/health</a></p>
            </body>
            </html>
            """
            self.wfile.write(html)
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress access logs"""
        pass

def start_health_server(port=10000):
    """
    Start health check HTTP server on specified port
    Render uses PORT env var, defaults to 10000
    """
    port = int(os.environ.get('PORT', port))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    
    # Run in background thread
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    
    print(f"✅ Health check server started on port {port}")
    print(f"   Access: http://localhost:{port}/health")
    
    return server

if __name__ == "__main__":
    # Test server locally
    server = start_health_server()
    print("Health server running. Press Ctrl+C to stop.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.shutdown()
