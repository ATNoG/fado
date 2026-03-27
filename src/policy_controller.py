from models import SecurityAlert, SecurityMeasure, AlertSeverity
from typing import assert_never
from fastapi import FastAPI
import uvicorn

app = FastAPI(title='Knative Security Policy Controller')

def evaluate_policy(alert: SecurityAlert) -> SecurityMeasure:
    match alert.severity:
        case AlertSeverity.Low:
            return SecurityMeasure.Nothing
        case AlertSeverity.Medium:
            return SecurityMeasure.Nothing
        case AlertSeverity.High:
            return SecurityMeasure.Kill
        case _:
            # can never happen
            assert_never(alert.severity)

# TODO: does the api need versioning??
@app.post('/api/alerts', response_model=SecurityMeasure)
async def process_security_alert(alert: SecurityAlert):
    print(f'[RECEIVED] Alert from {alert.node_name} for Pod: {alert.pod_name}')
    return evaluate_policy(alert)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
