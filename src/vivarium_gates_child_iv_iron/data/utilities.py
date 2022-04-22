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


def process_exposure(data: pd.DataFrame, key: str, entity: Union[RiskFactor, AlternativeRiskFactor],
                     location: str, gbd_round_id: int, age_group_ids: List[int] = None) -> pd.DataFrame:
    data['rei_id'] = entity.gbd_id

    # from vivarium_inputs.extract.extract_exposure
    allowable_measures = [vi_globals.MEASURES['Proportion'], vi_globals.MEASURES['Continuous'],
                          vi_globals.MEASURES['Prevalence']]
    proper_measure_id = set(data.measure_id).intersection(allowable_measures)
    if len(proper_measure_id) != 1:
        raise vi_globals.DataAbnormalError(f'Exposure data have {len(proper_measure_id)} measure id(s). '
                                           f'Data should have exactly one id out of {allowable_measures} '
                                           f'but came back with {proper_measure_id}.')
    data = data[data.measure_id == proper_measure_id.pop()]

    # from vivarium_inputs.core.get_exposure
    data = data.drop('modelable_entity_id', 'columns')

    if entity.name in vi_globals.EXTRA_RESIDUAL_CATEGORY:
        # noinspection PyUnusedLocal
        cat = vi_globals.EXTRA_RESIDUAL_CATEGORY[entity.name]
        data = data.drop(labels=data.query('parameter == @cat').index)
        data[vi_globals.DRAW_COLUMNS] = data[vi_globals.DRAW_COLUMNS].clip(lower=vi_globals.MINIMUM_EXPOSURE_VALUE)

    if entity.distribution in ['dichotomous', 'ordered_polytomous', 'unordered_polytomous']:
        tmrel_cat = utility_data.get_tmrel_category(entity)
        exposed = data[data.parameter != tmrel_cat]
        unexposed = data[data.parameter == tmrel_cat]
        #  FIXME: We fill 1 as exposure of tmrel category, which is not correct.
        data = pd.concat([normalize_age_and_years(exposed, fill_value=0, gbd_round_id=gbd_round_id),
                          normalize_age_and_years(unexposed, fill_value=1, gbd_round_id=gbd_round_id)],
                         ignore_index=True)

        # normalize so all categories sum to 1
        cols = list(set(data.columns).difference(vi_globals.DRAW_COLUMNS + ['parameter']))
        data = data.set_index(cols + ['parameter'])
        sums = (
            data.groupby(cols)[vi_globals.DRAW_COLUMNS].sum()
                .reindex(index=data.index)
        )
        data = data.divide(sums).reset_index()
    else:
        data = vi_utils.normalize(data, fill_value=0)

    data = data.filter(vi_globals.DEMOGRAPHIC_COLUMNS + vi_globals.DRAW_COLUMNS + ['parameter'])
    data = validate_and_reshape_gbd_data(data, entity, key, location, gbd_round_id, age_group_ids)
    return data


def process_relative_risk(data: pd.DataFrame, key: str, entity: Union[RiskFactor, AlternativeRiskFactor],
                          location: str, gbd_round_id: int, age_group_ids: List[int] = None,
                          whitelist_sids: bool = False) -> pd.DataFrame:
    # from vivarium_gbd_access.gbd.get_relative_risk
    data['rei_id'] = entity.gbd_id

    # from vivarium_inputs.extract.extract_relative_risk
    data = vi_utils.filter_to_most_detailed_causes(data)

    # from vivarium_inputs.core.get_relative_risk
    yll_only_causes = set([c.gbd_id for c in causes if c.restrictions.yll_only
                           and (c != causes.sudden_infant_death_syndrome if whitelist_sids else True)])
    data = data[~data.cause_id.isin(yll_only_causes)]

    data = vi_utils.convert_affected_entity(data, 'cause_id')
    morbidity = data.morbidity == 1
    mortality = data.mortality == 1
    data.loc[morbidity & mortality, 'affected_measure'] = 'incidence_rate'
    data.loc[morbidity & ~mortality, 'affected_measure'] = 'incidence_rate'
    data.loc[~morbidity & mortality, 'affected_measure'] = 'excess_mortality_rate'
    data = filter_relative_risk_to_cause_restrictions(data)

    data = data.filter(vi_globals.DEMOGRAPHIC_COLUMNS + ['affected_entity', 'affected_measure', 'parameter']
                       + vi_globals.DRAW_COLUMNS)
    data = (data.groupby(['affected_entity', 'parameter'])
            .apply(normalize_age_and_years, fill_value=1, gbd_round_id=gbd_round_id, age_group_ids=age_group_ids)
            .reset_index(drop=True))

    if entity.distribution in ['dichotomous', 'ordered_polytomous', 'unordered_polytomous']:
        tmrel_cat = utility_data.get_tmrel_category(entity)
        tmrel_mask = data.parameter == tmrel_cat
        data.loc[tmrel_mask, vi_globals.DRAW_COLUMNS] = (data.loc[tmrel_mask, vi_globals.DRAW_COLUMNS]
                                                         .mask(np.isclose(data.loc[tmrel_mask, vi_globals.DRAW_COLUMNS],
                                                                          1.0), 1.0))

    data = validate_and_reshape_gbd_data(data, entity, key, location, gbd_round_id, age_group_ids)
    return data
