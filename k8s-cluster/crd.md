# Apply the CRD
On the Kubernetes controller:
```bash
kubectl apply -f src/policies/crd.yml
```

And to remove it (if needed for some reason):
```bash
kubectl delete crd securitypolicies.security.ua.com # or kubectl delete -f src/policies/crd.yml
```

# Apply the policies themselves
To apply the 3 existing policies:
```bash
kubectl apply -f src/policies/low.yml
kubectl apply -f src/policies/medium.yml
kubectl apply -f src/policies/high.yml
```

And to remove them (for example, for high) (if needed for some reason):
```bash
kubectl delete sp block-critical-anomalies # or kubectl delete -f src/policies/high.yml
```

# Apply permissions
Give the nodes permissions to read the policies:
```bash
kubectl apply -f src/policies/rbac-nodes.yaml
```
