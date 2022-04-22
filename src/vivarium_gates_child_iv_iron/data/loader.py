"""Loads, standardizes and validates input data for the simulation.

Abstract the extract and transform pieces of the artifact ETL.
The intent here is to provide a uniform interface around this portion
of artifact creation. The value of this interface shows up when more
complicated data needs are part of the project. See the BEP project
for an example.

`BEP <https://github.com/ihmeuw/vivarium_gates_bep/blob/master/src/vivarium_gates_bep/data/loader.py>`_

.. admonition::

   No logging is done here. Logging is done in vivarium inputs itself and forwarded.
"""
import pandas as pd
import numpy as np

from gbd_mapping import causes, covariates, risk_factors, sequelae
from vivarium.framework.artifact import EntityKey
from vivarium_gbd_access import constants as gbd_constants, gbd
from vivarium_inputs import globals as vi_globals, interface, utilities as vi_utils, utility_data
from vivarium_inputs.mapping_extension import alternative_risk_factors

from vivarium_gates_child_iv_iron.constants import data_keys, data_values, metadata, paths
from vivarium_gates_child_iv_iron.constants.metadata import ARTIFACT_INDEX_COLUMNS
from vivarium_gates_child_iv_iron.data import utilities

from vivarium_gates_child_iv_iron.utilities import get_random_variable_draws


def get_data(lookup_key: str, location: str) -> pd.DataFrame:
    """Retrieves data from an appropriate source.

    Parameters
    ----------
    lookup_key
        The key that will eventually get put in the artifact with
        the requested data.
    location
        The location to get data for.

    Returns
    -------
        The requested data.

    """
    mapping = {
        data_keys.POPULATION.LOCATION: load_population_location,
        data_keys.POPULATION.STRUCTURE: load_population_structure,
        data_keys.POPULATION.AGE_BINS: load_age_bins,
        data_keys.POPULATION.DEMOGRAPHY: load_demographic_dimensions,
        data_keys.POPULATION.TMRLE: load_theoretical_minimum_risk_life_expectancy,
        data_keys.POPULATION.ACMR: load_standard_data,
        data_keys.POPULATION.CRUDE_BIRTH_RATE: load_standard_data,

        data_keys.DIARRHEA.DURATION: load_duration,
        data_keys.DIARRHEA.PREVALENCE: load_prevalence_from_incidence_and_duration,
        data_keys.DIARRHEA.INCIDENCE_RATE: load_standard_data,
        data_keys.DIARRHEA.REMISSION_RATE: load_remission_rate_from_duration,
        data_keys.DIARRHEA.DISABILITY_WEIGHT: load_standard_data,
        data_keys.DIARRHEA.EMR: load_emr_from_csmr_and_prevalence,
        data_keys.DIARRHEA.CSMR: load_standard_data,
        data_keys.DIARRHEA.RESTRICTIONS: load_metadata,

        data_keys.MEASLES.PREVALENCE: load_standard_data,
        data_keys.MEASLES.INCIDENCE_RATE: load_standard_data,
        data_keys.MEASLES.DISABILITY_WEIGHT: load_standard_data,
        data_keys.MEASLES.EMR: load_standard_data,
        data_keys.MEASLES.CSMR: load_standard_data,
        data_keys.MEASLES.RESTRICTIONS: load_metadata,

        data_keys.LRI.DURATION: load_duration,
        data_keys.LRI.PREVALENCE: load_prevalence_from_incidence_and_duration,
        data_keys.LRI.INCIDENCE_RATE: load_standard_data,
        data_keys.LRI.REMISSION_RATE: load_remission_rate_from_duration,
        data_keys.LRI.DISABILITY_WEIGHT: load_standard_data,
        data_keys.LRI.EMR: load_emr_from_csmr_and_prevalence,
        data_keys.LRI.CSMR: load_standard_data,
        data_keys.LRI.RESTRICTIONS: load_metadata,

        data_keys.WASTING.DISTRIBUTION: load_metadata,
        data_keys.WASTING.ALT_DISTRIBUTION: load_metadata,
        data_keys.WASTING.CATEGORIES: load_metadata,
        data_keys.WASTING.EXPOSURE: load_standard_data,
        data_keys.WASTING.RELATIVE_RISK: load_standard_data,
        data_keys.WASTING.PAF: load_categorical_paf,

        data_keys.STUNTING.DISTRIBUTION: load_metadata,
        data_keys.STUNTING.ALT_DISTRIBUTION: load_metadata,
        data_keys.STUNTING.CATEGORIES: load_metadata,
        data_keys.STUNTING.EXPOSURE: load_standard_data,
        data_keys.STUNTING.RELATIVE_RISK: load_standard_data,
        data_keys.STUNTING.PAF: load_categorical_paf,

        data_keys.MODERATE_PEM.DISABILITY_WEIGHT: load_pem_disability_weight,
        data_keys.MODERATE_PEM.EMR: load_pem_emr,
        data_keys.MODERATE_PEM.CSMR: load_pem_csmr,
        data_keys.MODERATE_PEM.RESTRICTIONS: load_pem_restrictions,

        data_keys.SEVERE_PEM.DISABILITY_WEIGHT: load_pem_disability_weight,
        data_keys.SEVERE_PEM.EMR: load_pem_emr,
        data_keys.SEVERE_PEM.CSMR: load_pem_csmr,
        data_keys.SEVERE_PEM.RESTRICTIONS: load_pem_restrictions,

        data_keys.LBWSG.DISTRIBUTION: load_metadata,
        data_keys.LBWSG.CATEGORIES: load_metadata,
        data_keys.LBWSG.EXPOSURE: load_lbwsg_exposure,
        data_keys.LBWSG.RELATIVE_RISK: load_lbwsg_rr,
        data_keys.LBWSG.RELATIVE_RISK_INTERPOLATOR: load_lbwsg_interpolated_rr,
        data_keys.LBWSG.PAF: load_lbwsg_paf,
    }
    return mapping[lookup_key](lookup_key, location)


def load_population_location(key: str, location: str) -> str:
    if key != data_keys.POPULATION.LOCATION:
        raise ValueError(f'Unrecognized key {key}')

    return location


def load_population_structure(key: str, location: str) -> pd.DataFrame:
    if location == "LMICs":
        world_bank_1 = filter_population(
            interface.get_population_structure("World Bank Low Income"))
        world_bank_2 = filter_population(
            interface.get_population_structure("World Bank Lower Middle Income"))
        population_structure = pd.concat([world_bank_1, world_bank_2])
    else:
        population_structure = filter_population(interface.get_population_structure(location))
    return population_structure


def filter_population(unfiltered: pd.DataFrame) -> pd.DataFrame:
    unfiltered = unfiltered.reset_index()
    filtered_pop = unfiltered[(unfiltered.age_end <= 5)]
    filtered_pop = filtered_pop.set_index(ARTIFACT_INDEX_COLUMNS)

    return filtered_pop


def load_age_bins(key: str, location: str) -> pd.DataFrame:
    all_age_bins = interface.get_age_bins().reset_index()
    return all_age_bins[all_age_bins.age_start < 5].set_index(['age_start', 'age_end', 'age_group_name'])


def load_demographic_dimensions(key: str, location: str) -> pd.DataFrame:
    demographic_dimensions = interface.get_demographic_dimensions(location)
    is_under_five = demographic_dimensions.index.get_level_values('age_end') <= 5
    return demographic_dimensions[is_under_five]


def load_theoretical_minimum_risk_life_expectancy(key: str, location: str) -> pd.DataFrame:
    return interface.get_theoretical_minimum_risk_life_expectancy()


def load_standard_data(key: str, location: str) -> pd.DataFrame:
    key = EntityKey(key)
    entity = get_entity(key)
    return interface.get_measure(entity, key.measure, location).droplevel('location')


def load_metadata(key: str, location: str):
    key = EntityKey(key)
    entity = get_entity(key)
    entity_metadata = entity[key.measure]
    if hasattr(entity_metadata, 'to_dict'):
        entity_metadata = entity_metadata.to_dict()
    return entity_metadata


def load_categorical_paf(key: str, location: str) -> pd.DataFrame:
    try:
        risk = {
            data_keys.WASTING.PAF: data_keys.WASTING,
            data_keys.STUNTING.PAF: data_keys.STUNTING,
        }[key]
    except KeyError:
        raise ValueError(f'Unrecognized key {key}')

    distribution_type = get_data(risk.DISTRIBUTION, location)

    if distribution_type != 'dichotomous' and 'polytomous' not in distribution_type:
        raise NotImplementedError(
            f"Unrecognized distribution {distribution_type} for {risk.name}. Only dichotomous and "
            f"polytomous are recognized categorical distributions."
        )

    exp = get_data(risk.EXPOSURE, location)
    rr = get_data(risk.RELATIVE_RISK, location)

    # paf = (sum_categories(exp * rr) - 1) / sum_categories(exp * rr)
    sum_exp_x_rr = (
        (exp * rr)
        .groupby(list(set(rr.index.names) - {'parameter'})).sum()
        .reset_index()
        .set_index(rr.index.names[:-1])
    )
    paf = (sum_exp_x_rr - 1) / sum_exp_x_rr
    return paf


def _load_em_from_meid(location, meid, measure):
    location_id = utility_data.get_location_id(location)
    data = gbd.get_modelable_entity_draws(meid, location_id)
    data = data[data.measure_id == vi_globals.MEASURES[measure]]
    data = vi_utils.normalize(data, fill_value=0)
    data = data.filter(vi_globals.DEMOGRAPHIC_COLUMNS + vi_globals.DRAW_COLUMNS)
    data = vi_utils.reshape(data)
    data = vi_utils.scrub_gbd_conventions(data, location)
    data = vi_utils.split_interval(data, interval_column='age', split_column_prefix='age')
    data = vi_utils.split_interval(data, interval_column='year', split_column_prefix='year')
    return vi_utils.sort_hierarchical_data(data)


# TODO - add project-specific data functions here
def load_duration(key: str, location: str) -> pd.DataFrame:
    try:
        distribution = {
            data_keys.DIARRHEA.DURATION: data_values.DIARRHEA_DURATION,
            data_keys.LRI.DURATION: data_values.LRI_DURATION,
        }[key]
    except KeyError:
        raise ValueError(f'Unrecognized key {key}')

    demography = get_data(data_keys.POPULATION.DEMOGRAPHY, location)
    duration_draws = (
            get_random_variable_draws(len(metadata.ARTIFACT_COLUMNS), distribution)
            / metadata.YEAR_DURATION
    )

    enn_duration = pd.DataFrame(
        data_values.EARLY_NEONATAL_CAUSE_DURATION / metadata.YEAR_DURATION,
        columns=metadata.ARTIFACT_COLUMNS,
        index=demography.query('age_start == 0.0').index
    )

    all_other_duration = pd.DataFrame(
        [duration_draws], index=demography.query('age_start != 0.0').index
    )
    all_other_duration.columns = metadata.ARTIFACT_COLUMNS

    duration = pd.concat([enn_duration, all_other_duration]).sort_index()

    return duration.droplevel('location')


def load_prevalence_from_incidence_and_duration(key: str, location: str) -> pd.DataFrame:
    try:
        cause = {
            data_keys.DIARRHEA.PREVALENCE: data_keys.DIARRHEA,
            data_keys.LRI.PREVALENCE: data_keys.LRI,
        }[key]
    except KeyError:
        raise ValueError(f'Unrecognized key {key}')

    incidence_rate = get_data(cause.INCIDENCE_RATE, location)
    duration = get_data(cause.DURATION, location)
    prevalence = incidence_rate * duration
    # NAs introduced by restricted demography in duration
    return prevalence.fillna(0)


def load_remission_rate_from_duration(key: str, location: str) -> pd.DataFrame:
    try:
        cause = {
            data_keys.DIARRHEA.REMISSION_RATE: data_keys.DIARRHEA,
            data_keys.LRI.REMISSION_RATE: data_keys.LRI,
        }[key]
    except KeyError:
        raise ValueError(f'Unrecognized key {key}')
    duration = get_data(cause.DURATION, location)
    remission_rate = 1 / duration
    return remission_rate


def load_emr_from_csmr_and_prevalence(key: str, location: str) -> pd.DataFrame:
    try:
        cause = {
            data_keys.DIARRHEA.EMR: data_keys.DIARRHEA,
            data_keys.LRI.EMR: data_keys.LRI,
        }[key]
    except KeyError:
        raise ValueError(f'Unrecognized key {key}')

    csmr = get_data(cause.CSMR, location)
    prevalence = get_data(cause.PREVALENCE, location)
    data = (csmr / prevalence).fillna(0)
    data = data.replace([np.inf, -np.inf], 0)
    return data


def get_entity(key: str):
    # Map of entity types to their gbd mappings.
    type_map = {
        'cause': causes,
        'covariate': covariates,
        'risk_factor': risk_factors,
        'alternative_risk_factor': alternative_risk_factors
    }
    key = EntityKey(key)
    return type_map[key.type][key.name]


def load_pem_disability_weight(key: str, location: str) -> pd.DataFrame:
    try:
        pem_sequelae = {
            data_keys.MODERATE_PEM.DISABILITY_WEIGHT: [sequelae.moderate_wasting_with_edema,
                                               sequelae.moderate_wasting_without_edema],
            data_keys.SEVERE_PEM.DISABILITY_WEIGHT: [sequelae.severe_wasting_with_edema,
                                               sequelae.severe_wasting_without_edema],
        }[key]
    except KeyError:
        raise ValueError(f'Unrecognized key {key}')

    prevalence_disability_weight = []
    state_prevalence = []
    for s in pem_sequelae:
        sequela_prevalence = interface.get_measure(s, 'prevalence', location)
        sequela_disability_weight = interface.get_measure(s, 'disability_weight', location)

        prevalence_disability_weight += [sequela_prevalence * sequela_disability_weight]
        state_prevalence += [sequela_prevalence]

    disability_weight = (
        (sum(prevalence_disability_weight) / sum(state_prevalence))
        .fillna(0)
        .droplevel('location')
    )
    return disability_weight


def load_pem_emr(key: str, location: str) -> pd.DataFrame:
    emr = load_standard_data(data_keys.PEM.EMR, location)
    return emr


def load_pem_csmr(key: str, location: str) -> pd.DataFrame:
    csmr = load_standard_data(data_keys.PEM.CSMR, location)
    return csmr


def load_pem_restrictions(key: str, location: str) -> pd.DataFrame:
    metadata = load_metadata(data_keys.PEM.RESTRICTIONS, location)
    return metadata


def load_lbwsg_exposure(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.LBWSG.EXPOSURE:
        raise ValueError(f'Unrecognized key {key}')

    key = EntityKey(key)
    entity = get_entity(key)
    data = utilities.get_data(key, entity, location, gbd_constants.SOURCES.EXPOSURE, 'rei_id',
                              metadata.AGE_GROUP.GBD_2019_LBWSG_EXPOSURE, metadata.GBD_2019_ROUND_ID, 'step4')
    data = data[data['year_id'] == 2019].drop(columns='year_id')
    data = utilities.process_exposure(data, key, entity, location, metadata.GBD_2019_ROUND_ID,
                                      metadata.AGE_GROUP.GBD_2019_LBWSG_EXPOSURE | metadata.AGE_GROUP.GBD_2020)
    data = data[data.index.get_level_values('year_start') == 2019]
    return data


def load_lbwsg_rr(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.LBWSG.RELATIVE_RISK:
        raise ValueError(f'Unrecognized key {key}')

    key = EntityKey(key)
    entity = get_entity(key)
    data = utilities.get_data(key, entity, location, gbd_constants.SOURCES.RR, 'rei_id',
                              metadata.AGE_GROUP.GBD_2019_LBWSG_RELATIVE_RISK, metadata.GBD_2019_ROUND_ID, 'step4')
    data = data[data['year_id'] == 2019].drop(columns='year_id')
    data = utilities.process_relative_risk(data, key, entity, location, metadata.GBD_2019_ROUND_ID,
                                           metadata.AGE_GROUP.GBD_2020, whitelist_sids=True)
    data = (
        data.query('year_start == 2019')
        .droplevel(['affected_entity', 'affected_measure'])
    )
    data = data[~data.index.duplicated()]
    return data


def load_lbwsg_interpolated_rr(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.LBWSG.RELATIVE_RISK_INTERPOLATOR:
        raise ValueError(f'Unrecognized key {key}')

    rr = get_data(data_keys.LBWSG.RELATIVE_RISK, location).reset_index()
    rr['parameter'] = pd.Categorical(rr['parameter'], [f'cat{i}' for i in range(1000)])
    rr = (
        rr.sort_values('parameter')
        .set_index(metadata.ARTIFACT_INDEX_COLUMNS + ['parameter'])
        .stack()
        .unstack('parameter')
        .apply(np.log)
    )

    # get category midpoints
    def get_category_midpoints(lbwsg_type: Type[LBWSGSubRisk]) -> pd.Series:
        categories = get_data(f'risk_factor.{data_keys.LBWSG.name}.categories', location)
        return lbwsg_type.get_intervals_from_categories(categories).apply(lambda x: x.mid)

    gestational_age_midpoints = get_category_midpoints(ShortGestation)
    birth_weight_midpoints = get_category_midpoints(LowBirthWeight)

    # build grid of gestational age and birth weight
    def get_grid(midpoints: pd.Series, endpoints: Tuple[float, float]) -> np.array:
        grid = np.append(np.unique(midpoints), endpoints)
        grid.sort()
        return grid

    gestational_age_grid = get_grid(gestational_age_midpoints, (0.0, 42.0))
    birth_weight_grid = get_grid(birth_weight_midpoints, (0.0, 4500.0))

    def make_interpolator(log_rr_for_age_sex_draw: pd.Series) -> RectBivariateSpline:
        # Use scipy.interpolate.griddata to extrapolate to grid using nearest neighbor interpolation
        log_rr_grid_nearest = griddata(
            (gestational_age_midpoints, birth_weight_midpoints),
            log_rr_for_age_sex_draw,
            (gestational_age_grid[:, None], birth_weight_grid[None, :]),
            method='nearest',
            rescale=True
        )
        # return a RectBivariateSpline object from the extrapolated values on grid
        return RectBivariateSpline(gestational_age_grid, birth_weight_grid, log_rr_grid_nearest, kx=1, ky=1)

    log_rr_interpolator = (
        rr.apply(make_interpolator, axis='columns')
        .apply(lambda x: pickle.dumps(x).hex())
        .unstack()
    )
    return log_rr_interpolator


def load_lbwsg_paf(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.LBWSG.PAF:
        raise ValueError(f'Unrecognized key {key}')

    paf_files = paths.TEMPORARY_PAF_DIR.glob('*.hdf')
    paf_data = (
        pd.concat([pd.read_hdf(paf_file) for paf_file in paf_files])
        .sort_values(metadata.ARTIFACT_INDEX_COLUMNS + ['draw'])
    )

    paf_data['draw'] = paf_data['draw'].apply(lambda draw: f'draw_{draw}')

    paf_data = (
        paf_data.set_index(metadata.ARTIFACT_INDEX_COLUMNS + ['draw'])
        .unstack()
    )

    paf_data.columns = paf_data.columns.droplevel(0)
    paf_data.columns.name = None

    full_index = (
        get_data(data_keys.LBWSG.RELATIVE_RISK, location).index
        .droplevel('parameter')
        .drop_duplicates()
    )

    paf_data = (
        paf_data.reindex(full_index)
        .fillna(0.0)
    )
    return paf_data
