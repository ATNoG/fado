from pydantic import BaseModel
from enum import Enum

class AlertSeverity(Enum):
    Low = 0
    Medium = 1
    High = 2

class SecurityMeasure(Enum):
    Nothing = 0
    Kill = 1

class SecurityAlert(BaseModel):
    node_name: str
    pod_name: str
    container_id: str
    severity: AlertSeverity
