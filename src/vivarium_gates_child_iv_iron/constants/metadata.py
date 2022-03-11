import pandas as pd

from typing import NamedTuple

####################
# Project metadata #
####################

PROJECT_NAME = 'vivarium_gates_child_iv_iron'
CLUSTER_PROJECT = 'proj_simscience'
# # TODO use proj_csu if a csu project
# CLUSTER_PROJECT = 'proj_csu'

CLUSTER_QUEUE = 'all.q'
MAKE_ARTIFACT_MEM = '10G'
MAKE_ARTIFACT_CPU = '1'
MAKE_ARTIFACT_RUNTIME = '3:00:00'
MAKE_ARTIFACT_SLEEP = 10

LOCATIONS = [
    "Sub-Saharan Africa",
    "South Asia",
    "LMICs"
]

ARTIFACT_INDEX_COLUMNS = [
    'sex',
    'age_start',
    'age_end',
    'year_start',
    'year_end',
]

DRAW_COUNT = 1000
ARTIFACT_COLUMNS = pd.Index([f'draw_{i}' for i in range(DRAW_COUNT)])


class __Scenarios(NamedTuple):
    baseline: str = 'baseline'
    # TODO - add scenarios here


SCENARIOS = __Scenarios()
