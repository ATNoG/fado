# Install Helm
To deploy the DaemonSet, you will need Helm (on the controller):
```bash
wget https://get.helm.sh/helm-v4.1.4-linux-amd64.tar.gz
tar -xzf helm-v4.1.4-linux-amd64.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/
rm -rf linux-amd64/ helm-v4.1.4-linux-amd64.tar.gz
```

# Build and deploy the DaemonSet image
On any machine with Docker installed and from the root of this project:
```bash
docker build -t security-agent -f src/daemonset/Dockerfile .
```

Save the image:
```bash
docker tag security-agent:latest dev.local/security-agent:v1
docker save dev.local/security-agent:v1 -o security-agent.tar
```

Copy the image to the workers (do this for all workers):
```bash
scp security-agent.tar ubuntu@<WORKER_IP>:~
```

On each worker, load the image into containerd:
```bash
sudo ctr -n k8s.io images import security-agent.tar
```

# Create the DaemonSet on the cluster
Create the identity for the Pods (on the controller):
```bash
kubectl apply -f src/daemonset/service-account.yml
```

Apply the RBAC rules (on the controller):
```bash
kubectl apply -f src/daemonset/rbac.yml
```

Create the config map (on the controller):
```bash
kubectl apply -f src/daemonset/configmap.yml
```

# Deploy using Helm
```bash
helm install ebpf-security-agent src/security-agent
```
