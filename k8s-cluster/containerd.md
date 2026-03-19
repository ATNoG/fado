# Remove old/incompatible packages
```bash
sudo apt autoremove -y docker.io docker-buildx containerd && sudo reboot
```

# Install Containerd:
This installs containerd 2.2.2 (latest version at the time of writing).
```bash
wget https://github.com/containerd/containerd/releases/download/v2.2.2/containerd-2.2.2-linux-amd64.tar.gz
sudo tar Cxzvf /usr/local containerd-2.2.2-linux-amd64.tar.gz
```

```bash
sudo mkdir -p /usr/local/lib/systemd/system/
sudo wget -O /usr/local/lib/systemd/system/containerd.service https://raw.githubusercontent.com/containerd/containerd/main/containerd.service
sudo systemctl daemon-reload
sudo systemctl enable --now containerd
```

## Install runc (required by containerd):
```bash
wget https://github.com/opencontainers/runc/releases/download/v1.4.1/runc.amd64
sudo install -m 755 runc.amd64 /usr/local/sbin/runc
```

## Install CNI plugins (required by containerd):
```bash
wget https://github.com/containernetworking/plugins/releases/download/v1.9.1/cni-plugins-linux-amd64-v1.9.1.tgz
mkdir -p /opt/cni/bin
sudo tar Cxzvf /opt/cni/bin cni-plugins-linux-amd64-v1.9.1.tgz
```

# Cleanup:
```bash
rm cni-plugins-linux-amd64-v1.9.1.tgz containerd-2.2.2-linux-amd64.tar.gz runc.amd64
```
