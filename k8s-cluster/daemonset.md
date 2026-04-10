# Create the DaemonSet
Create the identity for the Pods (on the controller):
```bash
kubectl apply -f src/daemonset/service-account.yml
```

Apply the RBAC rules (on the controller):
```bash
kubectl apply -f src/daemonset/rbac.yml
```

Create the DaemonSet (on the controller):
```bash
kubectl apply -f src/daemonset/daemonset.yml
```
