from pathlib import Path

#### INTERNAL CONFIGS ####
# -> (applicable to running as a script in a k8s worker, with Docker or as a DaemonSet)

TOLERANCE = 0.6
WHITELIST_FREQUENCY = 0.1

MAX_QUEUE_SIZE = 1000

STATS  = Path.cwd() / 'data' / 'stats'
FIGS   = Path.cwd() / 'data' / 'figs'
MODELS = Path.cwd() / 'data' / 'models'
DB     = Path.cwd() / 'data' / 'logs'

#### MODEL CONFIGS ####
# -> (applicable to running as a script in a k8s worker or with Docker)

IMAGE_MODEL_MAPPINGS = {
    'yaml_load': 'YamlLoadWithStartup_5s_w2_10p',
    'sentiment_analyzer': 'SentimentAnalyzerWithStartup_10s_w2_10p',
    'log4shell': 'Log4ShellWithStartup_5s_w2_10p'
}
