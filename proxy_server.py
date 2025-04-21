from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from urllib.parse import urlparse, parse_qs
import json

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL and get the target URL from query parameters
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        target_url = query_params.get('url', [None])[0]

        if not target_url:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Missing url parameter')
            return

        try:
            # Forward the request to Reddit
            response = requests.get(target_url, headers={
                'Authorization': self.headers.get('Authorization'),
                'User-Agent': self.headers.get('User-Agent')
            })

            # Send the response back to the client
            self.send_response(response.status_code)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response.content)

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

def run_server():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, ProxyHandler)
    print('Proxy server running on port 8080...')
    httpd.serve_forever()

if __name__ == '__main__':
    run_server() 