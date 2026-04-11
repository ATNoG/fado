# Deploy the `yaml_load` docker image to Knative
This requires the `yaml_load` image to be built.
```bash
docker tag yaml_load:latest dev.local/yaml_load:v1
docker save dev.local/yaml_load:v1 -o yaml_load.tar
```

Copy the image to the workers (do this for all workers):
```bash
scp yaml_load.tar ubuntu@<WORKER_IP>:~
```

On each worker, load the image into containerd:
```bash
sudo ctr -n k8s.io images import yaml_load.tar
```

To check if it is there:
```bash
sudo ctr -n k8s.io images list | grep yaml_load
```

And finally, to deploy on Knative (run on the controller):
```bash
kn service create yaml-load --image dev.local/yaml_load:v1 --port 8000
```
