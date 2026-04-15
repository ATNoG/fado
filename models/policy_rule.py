from .alert import AlertSeverity
from pydantic import BaseModel
from enum import Enum

class ActionType(str, Enum):
    NOTHING = 'nothing'
    LOG = 'log'
    KILL = 'kill'

class MatchCriteria(BaseModel):
    alert_severity: AlertSeverity

class PolicyRule(BaseModel):
    match: MatchCriteria
    actions: list[ActionType]
