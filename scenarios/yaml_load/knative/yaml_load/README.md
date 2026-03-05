# Running yaml_load in Knative
This requires the yaml_load Docker image to be built and a Knative cluster to be running.

Tag the image, push it to the local repository and create the Knative the service.
```bash
docker tag yaml_load:latest localhost:5001/yaml_load:latest
docker push localhost:5001/yaml_load:latest
kn service create yaml-load --image localhost:5001/yaml_load:latest --port 8000
```
