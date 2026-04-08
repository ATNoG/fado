from models import SecurityAlert, AlertSeverity, PolicyConfig, ActionType
import uvicorn, yaml, logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

app = FastAPI(title='Knative Security Policy Controller')
with open('./src/policies/policies.yml', 'r') as f:
    policy_config = PolicyConfig(**yaml.safe_load(f))

def evaluate_alert(alert_severity: AlertSeverity) -> list[ActionType]:
    # must be a list to ensure action order
    triggered_actions: list[ActionType] = []

    for rule in policy_config.rules:
        if rule.match.alert_severity != alert_severity:
            continue

        for action in rule.actions:
            if action not in triggered_actions:
                triggered_actions.append(action)

    if not triggered_actions:
        return [ActionType.NOTHING]

    return triggered_actions

# TODO: does the api need versioning??
@app.post('/api/alerts')
async def process_security_alert(alert: SecurityAlert):
    logger.warning(f'SECURITY ALERT | '
        f'Node: {alert.node_name} | '
        f'Pod: {alert.node_name} | '
        f'Container ID: {alert.container_id} | '
        f'Alert severity: {alert.severity} | '
        f'Window: {alert.window}'
    )

    return {'actions': evaluate_alert(alert.severity)}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
