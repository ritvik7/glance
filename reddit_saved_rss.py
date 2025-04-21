import requests
import base64
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import json
import time
from dotenv import load_dotenv
import os
from pathlib import Path

# Get the absolute path to the .env file
ENV_PATH = str(Path(__file__).parent / '.env')

# Load environment variables from .env file
load_dotenv(ENV_PATH)

# Get credentials from .env file
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8081")
REFRESH_TOKEN = os.getenv("REDDIT_REFRESH_TOKEN", None)

if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in .env file")

def get_refresh_token():
    # Create the authorization URL
    auth_url = f"https://www.reddit.com/api/v1/authorize?client_id={CLIENT_ID}&response_type=code&state=random_state&redirect_uri={REDIRECT_URI}&duration=permanent&scope=read"
    
    print(f"Opening browser to authorize Reddit access...")
    webbrowser.open(auth_url)
    
    # Start local server to receive the code
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if 'code' in query:
                code = query['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Authorization successful! You can close this window.")
                
                # Exchange code for refresh token
                auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
                headers = {
                    'Authorization': f'Basic {auth}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                data = {
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': REDIRECT_URI
                }
                
                response = requests.post('https://www.reddit.com/api/v1/access_token', headers=headers, data=data)
                tokens = response.json()
                refresh_token = tokens.get('refresh_token')
                print(tokens, 'tokens')

                if refresh_token:
                    print("\nYour refresh token is:")
                    print(refresh_token)
                    save_to_env("REDDIT_REFRESH_TOKEN", refresh_token)
                else:
                    print("Failed to obtain refresh token.")
                
                # Stop the server
                self.server.running = False
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Authorization failed!")
    
    server = HTTPServer(('localhost', 8081), Handler)
    server.running = True
    while server.running:
        server.handle_request()


def refresh_access_token():
    global REFRESH_TOKEN
    if not REFRESH_TOKEN:
        print("No refresh token found. Please authenticate using `get_refresh_token()` first.")
        return None

    auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN
    }

    response = requests.post('https://www.reddit.com/api/v1/access_token', headers=headers, data=data)
    tokens = response.json()

    if 'access_token' in tokens:
        access_token = tokens['access_token']
        save_to_env("REDDIT_ACCESS_TOKEN", access_token)
        save_to_env("REDDIT_TOKEN_FETCHED_AT", time.strftime('%Y-%m-%d %H:%M:%S'))
        print("\nNew access token obtained and saved to .env file.")
        return access_token
    else:
        print("Failed to refresh access token. Response:", tokens)
        exit()


def save_to_env(key, value):
    print()
    with open(ENV_PATH, "r") as file:
        lines = file.readlines()

    found = False
    with open(ENV_PATH, "w") as file:
        for line in lines:
            if line.startswith(f"{key}="):
                file.write(f"{key}={value}\n")
                found = True
            else:
                file.write(line)
        
        if not found:
            file.write(f"{key}={value}\n")


if __name__ == "__main__":
    if not REFRESH_TOKEN:
        get_refresh_token()
    else:
        while True:
            refresh_access_token()
            # Refresh token every 50 minutes (recommended by Reddit)
            time.sleep(3000)