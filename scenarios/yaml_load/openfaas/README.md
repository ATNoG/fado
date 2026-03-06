# Running with OpenFaaS
This requires `faas`/`faas-cli`, and `ark`/`arkane`.

Create a KinD cluster and install the OpenFaaS Community Edition onto it:
```bash
kind create cluster --config ../kind/kind-config.yml
arkade install openfaas-ce
```

Port-forward the OpenFaaS dashboard:
```bash
kubectl port-forward -n openfaas svc/gateway 8080:8080
```

Log in `faas-cli` to the dashboard:
```bash
PASSWORD=$(kubectl get secret -n openfaas basic-auth -o jsonpath="{.data.basic-auth-password}" | base64 --decode; echo)
echo -n $PASSWORD | faas-cli login --username admin --password-stdin
```

And finally, log in into the dashboard (`http://127.0.0.1:8080`) with username `admin` and password:
```bash
echo $PASSWORD
```
