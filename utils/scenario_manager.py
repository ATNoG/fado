from scenarios import yaml_load, sentiment_analyzer, log4shell
from enum import Enum
from .abstract_scenario import BaseSimulation


class Scenario(Enum):
    YAML_LOAD = 0
    SENTIMENTANALYER = 1
    LOG4SHELL = 2

class ScenarioManager:
    def __init__(self):
        self.registry = {
            Scenario.YAML_LOAD: yaml_load.get_scenario,
            Scenario.SENTIMENTANALYER: sentiment_analyzer.get_scenario,
            Scenario.LOG4SHELL: log4shell.get_scenario
        }

    def get_scenario(self, scenario: Scenario) -> BaseSimulation:
        return self.registry[scenario]()