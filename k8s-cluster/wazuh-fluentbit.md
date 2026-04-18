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
  <allowed-ips>10.255.41.0/24</allowed-ips>
</remote>
```

Add a rule to `/var/ossec/etc/rules/local_rules.xml` at the bottom of the file (just make sure that the rule id is not duplicated):
```
<group name="ebpf_alerts,kubernetes,">
  <rule id="100002" level="10">
    <decoded_as>json</decoded_as>
    <field name="kubernetes.labels.app">security-agent</field>
    <description>eBPF security agent: Severity '$(log.alert_severity)' detected on pod $(log.pod_name)</description>
  </rule>
</group>
```

Create a custom decoder to `/var/ossec/etc/decoders/local_decoder.xml` at the bottom of the file:
```
<decoder name="security-agent-decoder">
  <prematch>security-agent</prematch>
  <plugin_decoder>JSON_Decoder</plugin_decoder>
</decoder>
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
