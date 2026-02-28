# Running in a Kubernetes Cluster with minikube
This requires `minikube`.

Create the Kubernetes Cluster (requires the yaml_load docker image built):
```bash
minikube start --nodes 4 # 1 master and 3 worked nodes
minikube image load yaml_load:latest
```

Deploy the app and load balancer service:
```bash
kubectl apply -f ../kubernetes/deployment.yml -f ../kubernetes/service.yml
minikube tunnel # or kubectl port-forward service/yaml-load-service 8000:8000
```
