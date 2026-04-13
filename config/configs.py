from pathlib import Path

#### GENERAL CONFIGS ####

TOLERANCE = 0.6
WHITELIST_FREQUENCY = 0.1

MAX_QUEUE_SIZE = 1000

STATS  = Path.cwd() / 'data' / 'stats'
FIGS   = Path.cwd() / 'data' / 'figs'
MODELS = Path.cwd() / 'data' / 'models'
DB     = Path.cwd() / 'data' / 'logs'

IMAGE_MODEL_MAPPINGS = {
    'yaml_load:v1': 'YamlLoadWithStartup_5s_w2_10p',
    'sentiment_analyzer:v1': 'SentimentAnalyzerWithStartup_10s_w2_10p',
    'log4shell:v1': 'Log4ShellWithStartup_5s_w2_10p'
}
