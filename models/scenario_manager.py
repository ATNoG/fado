from .base_simulation import BaseSimulation
from enum import Enum

# TODO: maybe this could just be a str enum?? instead of using a property for the image name
class Scenario(Enum):
    YAML_LOAD        = 0
    SENTIMENTANALYER = 1
    LOG4SHELL        = 2

    @property
    def image_name(self):
        mappings = {
            Scenario.YAML_LOAD: 'yaml_load',
            Scenario.SENTIMENTANALYER: 'sentiment_analyzer',
            Scenario.LOG4SHELL: 'log4shell'
        }

        return mappings[self]

class ScenarioManager:
    def __init__(self):
        from scenarios import yaml_load, sentiment_analyzer, log4shell
        self.registry = {
            Scenario.YAML_LOAD: yaml_load.get_scenario,
            Scenario.SENTIMENTANALYER: sentiment_analyzer.get_scenario,
            Scenario.LOG4SHELL: log4shell.get_scenario
        }

    def get_scenario(self, scenario: Scenario) -> BaseSimulation:
        return self.registry[scenario]()
