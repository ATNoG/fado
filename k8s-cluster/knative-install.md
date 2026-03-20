# Install Knative
This installs Knative 1.21 (latest version at the time of writing).

# Install Knatice CLI
```bash
wget https://github.com/knative/client/releases/download/knative-v1.21.0/kn-linux-amd64
mv kn-linux-amd64 kn
chmod +x kn
sudo mv kn /usr/local/bin
```

# Install Knative Serving
```bash
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.21.1/serving-crds.yaml
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.21.1/serving-core.yaml
```

## Install a networking layer (Kourier)
```bash
kubectl apply -f https://github.com/knative-extensions/net-kourier/releases/download/knative-v1.21.0/kourier.yaml
```

And tell Knative Serving to use Kourier by default:
```bash
kubectl patch configmap/config-network \
    --namespace knative-serving \
    --type merge \
    --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'
```

## Bind the Kourier load balancer to the IP of the first worker node (hack)
This must be done since we don't have a real load balancer that would give the Kourier load balancer an external ip.  
Replace `<WORKER_1_IP>` with the ip address of the first worker.
```bash
kubectl patch svc kourier -n kourier-system -p '{"spec": {"externalIPs": ["<WORKER_1_IP>"]}}'
```

## Configure Magic DNS (sslip.io)
```bash
kubectl apply -f https://github.com/knative/serving/releases/download/knative-v1.21.1/serving-default-domain.yaml
```

## Fix the url for a service in knative (hack)
Replace `<WORKER_1_IP>` with the ip address of the first worker.
```bash
kubectl patch configmap/config-domain \
    -n knative-serving \
    --type merge \
    -p '{"data":{"<WORKER_1_IP>.sslip.io":""}}'
```
