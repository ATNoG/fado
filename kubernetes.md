# Initialize Kubernetes cluster:
```bash
sudo kubeadm init --pod-network-cidr=192.168.0.0/16
```
> ⚠️ **Important:**  
> Save the `kubeadm join` command that gets printed!

Configure local user (this are commands printed from the last command):
```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```
