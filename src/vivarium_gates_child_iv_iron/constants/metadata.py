import pandas as pd

from typing import NamedTuple

####################
# Project metadata #
####################

PROJECT_NAME = 'vivarium_gates_child_iv_iron'
CLUSTER_PROJECT = 'proj_simscience'

CLUSTER_QUEUE = 'all.q'
MAKE_ARTIFACT_MEM = '10G'
MAKE_ARTIFACT_CPU = '1'
MAKE_ARTIFACT_RUNTIME = '3:00:00'
MAKE_ARTIFACT_SLEEP = 10

YEAR_DURATION: float = 365.25

LOCATIONS = [
    "Sub-Saharan Africa",
    "South Asia",
    "LMICs",
    "Ethiopia",
    "India",
    "Nigeria",
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
GBD_2019_ROUND_ID = 6


class __Scenarios(NamedTuple):
    baseline: str = 'baseline'
    # TODO - add scenarios here


SCENARIOS = __Scenarios()


class __AgeGroup(NamedTuple):
    BIRTH_ID = 164
    EARLY_NEONATAL_ID = 2
    LATE_NEONATAL_ID = 3
    POST_NEONATAL = 4
    YEARS_1_TO_4 = 5

    GBD_2019_LBWSG_EXPOSURE = {BIRTH_ID, EARLY_NEONATAL_ID, LATE_NEONATAL_ID}
    GBD_2019_LBWSG_RELATIVE_RISK = {EARLY_NEONATAL_ID, LATE_NEONATAL_ID}
    GBD_2019_SIDS = {LATE_NEONATAL_ID}

    GBD_2019 = {
        EARLY_NEONATAL_ID,
        LATE_NEONATAL_ID,
        POST_NEONATAL,
        YEARS_1_TO_4,
    }


AGE_GROUP = __AgeGroup()

NEONATAL_END_AGE = 0.076712
