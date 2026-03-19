# Initialize the Kubernetes cluster:
```bash
sudo kubeadm init --pod-network-cidr=192.168.0.0/16
```
> ⚠️ **Important:**  
> Save the `kubeadm join` command that gets printed!

Configure the local user (these are commands printed from the last command):
```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

# Install a CNI (Calico):
Kubernetes requires a CNI.  
This install Calico version 3.31.4 (latest version at the time of writing).
```bash
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.31.4/manifests/calico.yaml
```

# Join the nodes (the workers):
To join the workers simply run the `kubeadm join` command from the first step on all the workers (as root).
