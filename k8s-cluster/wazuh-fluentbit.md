# To install Wazuh
On an Ubuntu Vm outside of the Kubernetes cluster (just for a clear separation):
```bash
curl -sO https://packages.wazuh.com/4.14/wazuh-install.sh && sudo bash ./wazuh-install.sh -a
```

# Configure Wazuh
To enable syslog support, go to `/var/ossec/etc/ossec.conf` and scroll down until you see the existing `<remote>` block (it will say <connection>secure</connection> and port 1514), and add the following configuration inside the `<ossec_config>` tags:
```
<remote>
    <connection>syslog</connection>
    <port>514</port>
    <protocol>tcp</protocol>
    <allowed-ips>any</allowed-ips>
  </remote>
```

Then, restart the wazuh manager:
```bash
sudo systemctl restart wazuh-manager
```

# Collect the logs from Kubernetes
For wazuh to receive the logs from k8s, we need to install FluentBit on the cluster:
```bash
kubectl apply -f src/fluentbit/fluentbit.yml
```
