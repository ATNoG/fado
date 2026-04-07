from pydantic import BaseModel
from enum import Enum

class AlertSeverity(str, Enum):
    Low = 'low'
    Medium = 'medium'
    High = 'high'

class SecurityAlert(BaseModel):
    node_name: str
    pod_name: str
    container_id: str
    window: list[int]
    severity: AlertSeverity
