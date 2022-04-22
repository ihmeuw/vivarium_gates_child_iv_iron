import numpy as np
import pandas as pd
from typing import List, Set, Union, Tuple

from gbd_mapping import causes, covariates, risk_factors, Cause, ModelableEntity, RiskFactor
from vivarium.framework.artifact import EntityKey
from vivarium_gbd_access import constants as gbd_constants, gbd
from vivarium_gbd_access.utilities import get_draws, query
from vivarium_inputs import globals as vi_globals, utilities as vi_utils, utility_data
from vivarium_inputs.validation.raw import check_metadata


def get_data(key: EntityKey, entity: ModelableEntity, location: str, source: str, gbd_id_type: str,
             age_group_ids: Set[int], gbd_round_id: int, decomp_step: str = 'iterative') -> pd.DataFrame:
    age_group_ids = list(age_group_ids)

    # from interface.get_measure
    # from vivarium_inputs.core.get_data
    location_id = utility_data.get_location_id(location) if isinstance(location, str) else location

    # from vivarium_inputs.core.get_{measure}
    # from vivarium_inputs.extract.extract_data
    check_metadata(entity, key.measure)

    # from vivarium_inputs.extract.extract_{measure}
    # from vivarium_gbd_access.gbd.get_{measure}
    data = get_draws(gbd_id_type=gbd_id_type,
                     gbd_id=entity.gbd_id,
                     source=source,
                     location_id=location_id,
                     sex_id=gbd_constants.SEX.MALE + gbd_constants.SEX.FEMALE,
                     age_group_id=age_group_ids,
                     gbd_round_id=gbd_round_id,
                     decomp_step=decomp_step,
                     status='best')
    return data