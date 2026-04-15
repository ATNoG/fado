from models import BpfTrackedContainer, BpfProbe, BpfTrackedContainersRegistry, PolicyRule, Alert, ActionType
from multiprocessing import Process, Queue, set_start_method, Manager
from config import MODELS, IMAGE_MODEL_MAPPINGS, MAX_QUEUE_SIZE
from kubernetes.client import CoreV1Api, CustomObjectsApi
import socket, os, subprocess, json, logging
from kubernetes import config as K8sconfig
from kubernetes.watch import Watch
from bcc.table import HashTable
from bcc import BPF

def create_ebpf_map() -> tuple[BPF, HashTable]:
    text = open('./src/bpf/bpf.program', 'r').read()
    ebpf = BPF(text=text, cflags=['-Wno-microsoft-anon-tag', '-fms-extensions'])
    ebpf_map = ebpf.get_table('mnt_ns_set')
    print('[+] eBPF map is setup...')
    return (ebpf, ebpf_map)

def add_container(ebpf_map, containers_registry: BpfTrackedContainersRegistry, image: str, container_id: str, pod_name: str, node_name: str, alerts: Queue[Alert]):
    # get the PID from the local container runtime and the respective namespace id
    result = subprocess.run(['crictl', 'inspect', container_id], capture_output=True, text=True, check=True)
    container_pid = json.loads(result.stdout)['info']['pid']

    ns_id = os.stat(f'/proc/{container_pid}/ns/mnt').st_ino
    model_path = MODELS / (IMAGE_MODEL_MAPPINGS[image] + '.pkl')
    bpf_tracked_container = BpfTrackedContainer(image, container_id, model_path, pod_name, node_name, Queue(maxsize=MAX_QUEUE_SIZE), alerts)
    if not containers_registry.add_container(ns_id, bpf_tracked_container):
        return

    key = ebpf_map.Key(ns_id)
    value = ebpf_map.Leaf(0)
    ebpf_map[key] = value
    print(f'[+] Container created with image: {image} and ID: {container_id}')

def remove_container(ebpf_map, containers_registry: BpfTrackedContainersRegistry, container_id: str):
    ns_id = containers_registry.remove_container(container_id)
    if ns_id == None:
        return

    key = ebpf_map.Key(ns_id)
    del ebpf_map[key]
    print(f'[+] Container removed with ID: {container_id}')

def load_k8s_config():
    try:
        K8sconfig.load_incluster_config()
    except K8sconfig.ConfigException:
        K8sconfig.load_kube_config(config_file='/etc/kubernetes/kubelet.conf')

def containers_manager(ebpf_map, containers_registry: BpfTrackedContainersRegistry, alerts: Queue[Alert]):
    load_k8s_config()
    node_name = socket.gethostname()
    node_selector = f'spec.nodeName={node_name}'
    for event in Watch().stream(CoreV1Api().list_namespaced_pod, namespace='default', field_selector=node_selector):
        # the other event types are not usefull
        if type(event) != dict:
            continue

        pod = event['object']
        if not pod.metadata.labels or 'serving.knative.dev/revision' not in pod.metadata.labels:
            continue

        # example: nginxdemos/hello:plain-text
        container_image = pod.metadata.annotations['client.knative.dev/user-image'].split('/')[1]
        if container_image not in IMAGE_MODEL_MAPPINGS:
            continue

        if not pod.status.container_statuses:
            continue

        event_type = event['type']
        pod_name = pod.metadata.name
        old_cid = containers_registry.get_pod_container_id(pod_name)
        if event_type == 'MODIFIED' and pod.metadata.deletion_timestamp is not None:
            # container got removed/deleted
            if old_cid != None:
                remove_container(ebpf_map, containers_registry, old_cid)

            continue

        if event_type in ('ADDED', 'MODIFIED') and pod.status.phase == 'Running' and pod.metadata.deletion_timestamp is None:
            for container_status in pod.status.container_statuses:
                if container_status.name != 'user-container' or not container_status.container_id:
                    continue

                # ensure that the container is actually up and running
                if not container_status.state or not container_status.state.running:
                    continue

                current_cid = container_status.container_id.split('://')[-1]
                if old_cid == None or old_cid != current_cid:
                    # the container was restarted, we must clean up and re-add the container
                    if old_cid != None:
                        remove_container(ebpf_map, containers_registry, old_cid)
                        print('    ⮡ Container restart')

                    add_container(ebpf_map, containers_registry, container_image, current_cid, pod_name, node_name, alerts)

                break

def watch_policies(active_policies):
    print('[+] Starting Policy Engine...')
    load_k8s_config()
    stream = Watch().stream(CustomObjectsApi().list_cluster_custom_object, group='security.ua.com', version='v1', plural='securitypolicies')
    for event in stream:
        # the other event types are not usefull
        if type(event) != dict:
            continue

        event_type = event['type']
        obj = event['object']
        policy_name = obj['metadata']['name']

        if event_type in ['ADDED', 'MODIFIED']:
            try:
                rule = PolicyRule(**obj['spec'])
                active_policies[policy_name] = rule
                print(f'[Policy Engine] Loaded/Updated: {policy_name}')
            except Exception as e:
                print(f'[Policy Engine] Parse Error "{policy_name}": {e}')

        elif event_type == 'DELETED':
            if policy_name in active_policies:
                del active_policies[policy_name]
                print(f'[Policy Engine] Removed: {policy_name}')

# TODO: what about alerts for containers that were already killed (but not removed yet) or that do not exist?
def alert_manager(alerts: Queue[Alert], active_policies):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    if not logger.hasHandlers():
        logger.addHandler(handler)

    while True:
        alert = alerts.get(block=True, timeout=None)
        for action in alert.evaluate_alert(active_policies):
            match action:
                case ActionType.NOTHING:
                    pass
                case ActionType.LOG:
                    logger.warning(f'SECURITY ALERT | '
                        f'Node: {alert.node_name} | '
                        f'Pod: {alert.pod_name} | '
                        f'Container ID: {alert.container_id} | '
                        f'Alert severity: {alert.alert_severity} | '
                        f'Window: {alert.window}'
                    )
                case ActionType.KILL:
                    subprocess.run(['crictl', 'stop', '--timeout', '0', alert.container_id], capture_output=True, text=True, check=True)
                case _:
                    raise RuntimeError('Invalid ActionType value.')

if __name__ == '__main__':
    set_start_method('spawn')

    # policies watcher
    active_policies = Manager().dict()
    Process(target=watch_policies, args=(active_policies,), daemon=True).start()

    # alert manager
    alerts = Queue(maxsize=MAX_QUEUE_SIZE)
    Process(target=alert_manager, args=(alerts, active_policies)).start()

    # eBPF probing
    ebpf, ebpf_map = create_ebpf_map()
    containers_registry = BpfTrackedContainersRegistry()
    BpfProbe(containers_registry, ebpf)

    # k8s container events
    containers_manager(ebpf_map, containers_registry, alerts)
