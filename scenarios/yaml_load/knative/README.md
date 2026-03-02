# Running with Knative
This requires `kn`, `kn-quickstart` and `kind`.

Create the Knative Cluster (please keep in mind that the kubernetes version might have to be updated):
```bash
kn quickstart kind --registry -k 1.33.7
```
