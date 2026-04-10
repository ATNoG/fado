from enum import Enum

class AlertSeverity(str, Enum):
    Low = 'low'
    Medium = 'medium'
    High = 'high'
