# CVE-2017-18342 | Insecure Deserialization - Remote Code Execution

Adapted from [here](https://github.com/we45/DVFaaS-Damn-Vulnerable-Functions-as-a-Service/tree/master/insecure_deserialization).

[CVE-2017-18342](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2017-18342): In PyYAML before 5.1, the yaml.load() API could execute arbitrary code if used with untrusted data. The load() function has been deprecated in version 5.1 and the 'UnsafeLoader' has been introduced for backward compatibility with the function. 

## SETUP

```
cd backend/
docker build -t yaml_load .
docker run -p 8000:8000 -v /host/shared:/shared yaml_load
```
Exposes port 8000

## Malicious Payload
```
curl -X POST http://localhost:8000/yaml_upload/test@exploit.com -F 'file=@exploit.yaml'
```

## To run Frontend interface

```
cd frontend/
npm run dev
```

Exposes port 3000
