#!/usr/bin/env python3
"""
X-IDS Frontend Server
Serves the web dashboard and handles file uploads
"""

import os
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CORSRequestHandler(SimpleHTTPRequestHandler):
    """HTTP handler with CORS support for frontend-to-API communication"""
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        logger.info(format % args)

def run_frontend_server(port=8080):
    """Start the frontend server"""
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent.absolute()
    os.chdir(frontend_dir)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          🌐 X-IDS FRONTEND SERVER STARTED                     ║
║                                                                ║
║  📊 Dashboard:   http://localhost:{port}                      ║
║  🔧 Backend API: http://localhost:8000                        ║
║                                                                ║
║  Features:                                                     ║
║  ✓ Real-time metrics and alerts                              ║
║  ✓ Quick threat predictions                                  ║
║  ✓ Manual feature entry (77 features)                        ║
║  ✓ CSV/JSON file upload                                      ║
║  ✓ Ensemble voting mode                                      ║
║  ✓ Live threat distribution charts                           ║
║                                                                ║
║  Press Ctrl+C to stop                                         ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"Serving files from: {frontend_dir}")
    print(f"Listening on http://0.0.0.0:{port}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✓ Frontend server stopped")
        sys.exit(0)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_frontend_server(port)
