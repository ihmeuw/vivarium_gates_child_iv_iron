from datetime import datetime
from typing import Dict, NamedTuple, Tuple

import pandas as pd
from scipy import stats

from vivarium_gates_child_iv_iron.constants.metadata import YEAR_DURATION
from vivarium_gates_child_iv_iron.utilities import (
    get_norm_from_quantiles,
    get_lognorm_from_quantiles,
    get_truncnorm_from_quantiles,
    get_truncnorm_from_sd
)

##########################
# Cause Model Parameters #
##########################

# diarrhea and lower respiratory infection birth prevalence
BIRTH_PREVALENCE_OF_ZERO = 0

# diarrhea duration in days
DIARRHEA_DURATION: Tuple = (
    'diarrheal_diseases_duration', get_norm_from_quantiles(mean=4.3, lower=4.3, upper=4.3)
)

# measles duration in days
MEASLES_DURATION: int = 10

# LRI duration in days
LRI_DURATION: Tuple = (
    'lri_duration', get_norm_from_quantiles(mean=7.79, lower=6.2, upper=9.64)
)


# duration > bin_duration, so there is effectively no remission,
# and duration within the bin is bin_duration / 2
EARLY_NEONATAL_CAUSE_DURATION: float = 3.5


##########################
# LBWSG Model Parameters #
##########################
class __LBWSG(NamedTuple):

    TMREL_GESTATIONAL_AGE_INTERVAL: pd.Interval = pd.Interval(38.0, 42.0)
    TMREL_BIRTH_WEIGHT_INTERVAL: pd.Interval = pd.Interval(3500.0, 4500.0)

    STUNTING_EFFECT_PER_GRAM: Tuple[str, stats.norm] = (
        'stunting_effect_per_gram', stats.norm(loc=1e-04, scale=3e-05)
    )
    WASTING_EFFECT_PER_GRAM: float = 5.75e-05


LBWSG = __LBWSG()


class __MaternalSupplementation(NamedTuple):

    DISTRIBUTION: str = 'dichotomous'
    CATEGORIES: Dict[str, str] = {
        'cat1': 'uncovered',
        'cat2': 'covered',
    }

    IFA_BIRTH_WEIGHT_SHIFT: Tuple[str, stats.norm] = (
        'ifa_birth_weight_shift', get_norm_from_quantiles(mean=57.73, lower=7.66, upper=107.79)
    )

    BASELINE_MMN_COVERAGE: float = 0.0
    MMN_BIRTH_WEIGHT_SHIFT: Tuple[str, stats.norm] = (
        'mmn_birth_weight_shift', get_norm_from_quantiles(mean=45.16, lower=32.31, upper=58.02)
    )

    BASELINE_BEP_COVERAGE: float = 0.0
    BEP_BIRTH_WEIGHT_SHIFT: Tuple[str, stats.norm] = (
        'bep_birth_weight_shift', get_norm_from_quantiles(mean=66.96, lower=13.13, upper=120.78)
    )

    ALTERNATIVE_COVERAGE: float = 0.9


MATERNAL_SUPPLEMENTATION = __MaternalSupplementation()