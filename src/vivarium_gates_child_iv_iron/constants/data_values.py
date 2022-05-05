from datetime import datetime
from typing import Dict, NamedTuple, Tuple

import pandas as pd
from scipy import stats

from vivarium_gates_child_iv_iron.constants.metadata import YEAR_DURATION
from vivarium_gates_child_iv_iron.utilities import get_norm


##########################
# Cause Model Parameters #
##########################

# diarrhea duration in days
DIARRHEA_DURATION: Tuple = (
    'diarrheal_diseases_duration', get_norm(mean=4.3,
                                            ninety_five_pct_confidence_interval=(4.2, 4.4))
)

# diarrhea birth prevalence
DIARRHEA_BIRTH_PREVALENCE = 0

# measles duration in days
MEASLES_DURATION: int = 10

# LRI duration in days
LRI_DURATION: Tuple = (
    'lri_duration', get_norm(mean=7.79,
                             ninety_five_pct_confidence_interval=(6.2, 9.64))
)

# duration > bin_duration, so there is effectively no remission,
# and duration within the bin is bin_duration / 2
EARLY_NEONATAL_CAUSE_DURATION: float = 3.5
