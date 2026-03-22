from kubernetes import client, config, watch
import socket

# load_incluster_config() if running inside a pod
config.load_kube_config(config_file="/etc/kubernetes/kubelet.conf")
v1 = client.CoreV1Api()
w = watch.Watch()

print(f"Listening for Knative Pod events...")

node_selector = f"spec.nodeName={socket.gethostname()}"
for event in w.stream(v1.list_namespaced_pod, namespace="default", field_selector=node_selector):
    if type(event) != dict:
        continue

    event_type = event['type']
    pod = event['object']

    # filter for Knative pods using Knative's default labels
    if pod.metadata.labels and 'serving.knative.dev/revision' in pod.metadata.labels:
        # check if the container is running
        if event_type in ('ADDED', 'MODIFIED') and pod.status.phase == 'Running':
            image = pod.metadata.annotations['client.knative.dev/user-image']
            name = pod.metadata.name
            print(f"Pod started with image: {image}")
            print(pod)
        else:
            print(f"got action: {event_type}")

        # if event_type == 'ADDED':
        #     print(f"Knative Pod Created: {pod_name}")
        # elif event_type == 'MODIFIED':
        #     if pod.status.phase == 'Terminating':
        #         print(f"Knative Pod Terminating: {pod_name}")
        # elif event_type == 'DELETED':
        #     print(f"Knative Pod Deleted: {pod_name}")
