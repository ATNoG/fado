from models import SecurityAlert, AlertSeverity, PolicyConfig, ActionType
from fastapi import FastAPI
import uvicorn, yaml

app = FastAPI(title='Knative Security Policy Controller')
with open('./src/policies/policies.yml', 'r') as f:
    policy_config = PolicyConfig(**yaml.safe_load(f))

def evaluate_alert(alert_severity: AlertSeverity) -> set[ActionType]:
    triggered_actions: set[ActionType] = set()

    for rule in policy_config.rules:
        if rule.match.alert_severity != alert_severity:
            continue

        for action in rule.actions:
            triggered_actions.add(action)

    if not triggered_actions:
        return {ActionType.NOTHING}

    return triggered_actions

# TODO: does the api need versioning??
@app.post('/api/alerts')
async def process_security_alert(alert: SecurityAlert):
    print(f'[RECEIVED] Alert from {alert.node_name} for Pod: {alert.pod_name}')
    return {'actions': list(evaluate_alert(alert.severity))}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
