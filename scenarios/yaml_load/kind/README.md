# Running in a Kubernetes Cluster with Kind
This requires `Kind` and `cloud-provider-kind`.

Create the Kubernetes Cluster (requires the yaml_load docker image built):
```bash
kind create cluster --config kind-config.yml
kind load docker-image yaml_load:latest
```

Deploy the app and load balancer service:
```bash
kubectl apply -f ../kubernetes/deployment.yml -f ../kubernetes/service.yml
cloud-provider-kind # or kubectl port-forward service/yaml-load-service 8000:8000
```
