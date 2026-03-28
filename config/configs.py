from pathlib import Path

POLICY_CONTROLLER = 'http://localhost:8000'

TOLERANCE = 0.6
WHITELIST_FREQUENCY = 0.1

STATS = Path.cwd() / 'data' / 'stats'
FIGS  = Path.cwd() / 'data' / 'figs'
FILES = Path.cwd() / 'data' / 'models'
DB    = Path.cwd() / 'data' / 'logs'
