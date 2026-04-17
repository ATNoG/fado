from pydantic import BaseModel
from enum import Enum

class AlertSeverity(str, Enum):
    Low    = 'low'
    Medium = 'medium'
    High   = 'high'

class ActionType(str, Enum):
    NOTHING = 'nothing'
    LOG     = 'log'
    KILL    = 'kill'

class MatchCriteria(BaseModel):
    alert_severity: AlertSeverity

class PolicyRule(BaseModel):
    match: MatchCriteria
    actions: list[ActionType]

class Alert(BaseModel):
    image: str
    container_id: str
    alert_severity: AlertSeverity
    window: list[int]

    def evaluate_alert(self, active_policies) -> list[ActionType]:
        # must be a list to ensure action order
        triggered_actions: list[ActionType] = []

        for rule in active_policies.values():
            if rule.match.alert_severity != self.alert_severity:
                continue

            for action in rule.actions:
                if action not in triggered_actions:
                    triggered_actions.append(action)

        if not triggered_actions:
            return [ActionType.NOTHING]

        return triggered_actions
