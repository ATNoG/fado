from kubernetes.client import CustomObjectsApi
from multiprocessing import Manager
from kubernetes.watch import Watch
from kubernetes import config
from models import PolicyRule

def watch_policies(active_policies):
    print('Starting Policy Watcher...')
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

# def evaluate_alert(severity: str) -> list[ActionType]:
#     triggered_actions = set()
#     for rule in active_policies.values():
#         if rule.match.alert_severity == severity:
#             for action in rule.actions:
#                 triggered_actions.add(action)
#     return list(triggered_actions) if triggered_actions else [ActionType.NOTHING]

if __name__ == '__main__':
    config.load_kube_config(config_file='/etc/kubernetes/kubelet.conf')
    # active_policies: dict[str, PolicyRule] = {}
    manager = Manager()
    active_policies = manager.dict()
    watch_policies(active_policies)
