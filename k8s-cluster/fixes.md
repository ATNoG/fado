# Fix `ip_forward` disabled when using `kubeadm init`:
Kubernetes requires `ip_forward` to be enabled before creating a cluster.
```bash
echo "net.ipv4.ip_forward = 1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```
