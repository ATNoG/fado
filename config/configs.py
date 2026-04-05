from pathlib import Path

# TODO: maybe add the max queue size here??

#### GENERAL CONFIGS ####

POLICY_CONTROLLER = 'http://localhost:8000'

TOLERANCE = 0.6
WHITELIST_FREQUENCY = 0.1

STATS  = Path.cwd() / 'data' / 'stats'
FIGS   = Path.cwd() / 'data' / 'figs'
MODELS = Path.cwd() / 'data' / 'models'
DB     = Path.cwd() / 'data' / 'logs'

MNTNSMAP = '/sys/fs/bpf/mnt_ns_set'

IMAGE_MODEL_MAPPINGS = {
    'yaml_load:v1': 'YamlLoadWithStartup_5s_w2_10p',
    'sentiment_analyzer:v1': 'SentimentAnalyzerWithStartup_10s_w2_10p'
}
