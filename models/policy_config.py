from .security_alert import AlertSeverity
from pydantic import BaseModel
from enum import Enum

class ActionType(str, Enum):
    NOTHING = 'nothing'
    LOG = 'log'
    KILL = 'kill'

class MatchCriteria(BaseModel):
    alert_severity: AlertSeverity

class PolicyRule(BaseModel):
    name: str
    match: MatchCriteria
    actions: list[ActionType]

class PolicyConfig(BaseModel):
    rules: list[PolicyRule]
