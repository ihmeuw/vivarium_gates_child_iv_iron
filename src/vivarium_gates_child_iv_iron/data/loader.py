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
import pickle
from typing import Tuple, Union

import numpy as np
import pandas as pd
from gbd_mapping import Cause, sequelae
from scipy.interpolate import RectBivariateSpline, griddata
from vivarium.framework.artifact import EntityKey
from vivarium_gbd_access import constants as gbd_constants
from vivarium_gbd_access import gbd
from vivarium_inputs import globals as vi_globals
from vivarium_inputs import interface
from vivarium_inputs import utilities as vi_utils
from vivarium_inputs import utility_data

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
        data_keys.DIARRHEA.CSMR: load_diarrhea_csmr,
        data_keys.DIARRHEA.RESTRICTIONS: load_metadata,
        data_keys.DIARRHEA.BIRTH_PREVALENCE: load_diarrhea_birth_prevalence,

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
        data_keys.LRI.CSMR: load_lri_csmr,
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

        data_keys.AFFECTED_UNMODELED_CAUSES.URI_CSMR: load_standard_data,
        data_keys.AFFECTED_UNMODELED_CAUSES.OTITIS_MEDIA_CSMR: load_standard_data,
        data_keys.AFFECTED_UNMODELED_CAUSES.MENINGITIS_CSMR: load_standard_data,
        data_keys.AFFECTED_UNMODELED_CAUSES.ENCEPHALITIS_CSMR: load_standard_data,
        data_keys.AFFECTED_UNMODELED_CAUSES.NEONATAL_PRETERM_BIRTH_CSMR: load_standard_data,
        data_keys.AFFECTED_UNMODELED_CAUSES.NEONATAL_ENCEPHALOPATHY_CSMR: load_standard_data,
        data_keys.AFFECTED_UNMODELED_CAUSES.NEONATAL_SEPSIS_CSMR: load_standard_data,
        data_keys.AFFECTED_UNMODELED_CAUSES.NEONATAL_JAUNDICE_CSMR: load_standard_data,
        data_keys.AFFECTED_UNMODELED_CAUSES.OTHER_NEONATAL_DISORDERS_CSMR: load_standard_data,
        data_keys.AFFECTED_UNMODELED_CAUSES.SIDS_CSMR: load_sids_csmr,
        data_keys.AFFECTED_UNMODELED_CAUSES.NEONATAL_LRI_CSMR: load_neonatal_lri_csmr,
        data_keys.AFFECTED_UNMODELED_CAUSES.NEONATAL_DIARRHEAL_DISEASES_CSMR: load_neonatal_diarrhea_csmr,

        data_keys.IFA_SUPPLEMENTATION.DISTRIBUTION: load_intervention_distribution,
        data_keys.IFA_SUPPLEMENTATION.CATEGORIES: load_intervention_categories,
        data_keys.IFA_SUPPLEMENTATION.EXPOSURE: load_dichotomous_treatment_exposure,
        data_keys.IFA_SUPPLEMENTATION.EXCESS_SHIFT: load_treatment_excess_shift,
        data_keys.IFA_SUPPLEMENTATION.RISK_SPECIFIC_SHIFT: load_risk_specific_shift,

        data_keys.MMN_SUPPLEMENTATION.DISTRIBUTION: load_intervention_distribution,
        data_keys.MMN_SUPPLEMENTATION.CATEGORIES: load_intervention_categories,
        data_keys.MMN_SUPPLEMENTATION.EXPOSURE: load_dichotomous_treatment_exposure,
        data_keys.MMN_SUPPLEMENTATION.EXCESS_SHIFT: load_treatment_excess_shift,
        data_keys.MMN_SUPPLEMENTATION.RISK_SPECIFIC_SHIFT: load_risk_specific_shift,

        data_keys.BEP_SUPPLEMENTATION.DISTRIBUTION: load_intervention_distribution,
        data_keys.BEP_SUPPLEMENTATION.CATEGORIES: load_intervention_categories,
        data_keys.BEP_SUPPLEMENTATION.EXPOSURE: load_dichotomous_treatment_exposure,
        data_keys.BEP_SUPPLEMENTATION.EXCESS_SHIFT: load_treatment_excess_shift,
        data_keys.BEP_SUPPLEMENTATION.RISK_SPECIFIC_SHIFT: load_risk_specific_shift,

        data_keys.IV_IRON.DISTRIBUTION: load_intervention_distribution,
        data_keys.IV_IRON.CATEGORIES: load_intervention_categories,
        data_keys.IV_IRON.EXPOSURE: load_dichotomous_treatment_exposure,
        data_keys.IV_IRON.EXCESS_SHIFT: load_treatment_excess_shift,
        data_keys.IV_IRON.RISK_SPECIFIC_SHIFT: load_risk_specific_shift,

        data_keys.MATERNAL_BMI_ANEMIA.DISTRIBUTION: load_maternal_bmi_anemia_distribution,
        data_keys.MATERNAL_BMI_ANEMIA.CATEGORIES: load_maternal_bmi_anemia_categories,
        data_keys.MATERNAL_BMI_ANEMIA.EXPOSURE: load_maternal_bmi_anemia_exposure,
        data_keys.MATERNAL_BMI_ANEMIA.EXCESS_SHIFT: load_maternal_bmi_anemia_excess_shift,
        data_keys.MATERNAL_BMI_ANEMIA.RISK_SPECIFIC_SHIFT: load_risk_specific_shift,
    }
    return mapping[lookup_key](lookup_key, location)


def load_population_location(key: str, location: str) -> str:
    if key != data_keys.POPULATION.LOCATION:
        raise ValueError(f"Unrecognized key {key}")

    return location


def load_population_structure(key: str, location: str) -> pd.DataFrame:
    if location == "LMICs":
        world_bank_1 = filter_population(
            interface.get_population_structure("World Bank Low Income")
        )
        world_bank_2 = filter_population(
            interface.get_population_structure("World Bank Lower Middle Income")
        )
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
    return all_age_bins[all_age_bins.age_start < 5].set_index(
        ["age_start", "age_end", "age_group_name"]
    )


def load_demographic_dimensions(key: str, location: str) -> pd.DataFrame:
    demographic_dimensions = interface.get_demographic_dimensions(location)
    is_under_five = demographic_dimensions.index.get_level_values("age_end") <= 5
    return demographic_dimensions[is_under_five]


def load_theoretical_minimum_risk_life_expectancy(key: str, location: str) -> pd.DataFrame:
    return interface.get_theoretical_minimum_risk_life_expectancy()


def load_standard_data(key: str, location: str) -> pd.DataFrame:
    key = EntityKey(key)
    entity = utilities.get_entity(key)
    return interface.get_measure(entity, key.measure, location).droplevel("location")


def load_metadata(key: str, location: str):
    key = EntityKey(key)
    entity = utilities.get_entity(key)
    entity_metadata = entity[key.measure]
    if hasattr(entity_metadata, "to_dict"):
        entity_metadata = entity_metadata.to_dict()
    return entity_metadata


def load_categorical_paf(key: str, location: str) -> pd.DataFrame:
    try:
        risk = {
            data_keys.WASTING.PAF: data_keys.WASTING,
            data_keys.STUNTING.PAF: data_keys.STUNTING,
        }[key]
    except KeyError:
        raise ValueError(f"Unrecognized key {key}")

    distribution_type = get_data(risk.DISTRIBUTION, location)

    if distribution_type != "dichotomous" and "polytomous" not in distribution_type:
        raise NotImplementedError(
            f"Unrecognized distribution {distribution_type} for {risk.name}. Only dichotomous and "
            f"polytomous are recognized categorical distributions."
        )

    exp = get_data(risk.EXPOSURE, location)
    rr = get_data(risk.RELATIVE_RISK, location)

    # paf = (sum_categories(exp * rr) - 1) / sum_categories(exp * rr)
    sum_exp_x_rr = (
        (exp * rr)
        .groupby(list(set(rr.index.names) - {"parameter"}))
        .sum()
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
    data = vi_utils.split_interval(data, interval_column="age", split_column_prefix="age")
    data = vi_utils.split_interval(data, interval_column="year", split_column_prefix="year")
    return vi_utils.sort_hierarchical_data(data)


# TODO - add project-specific data functions here
def load_duration(key: str, location: str) -> pd.DataFrame:
    try:
        distribution = {
            data_keys.DIARRHEA.DURATION: data_values.DIARRHEA_DURATION,
            data_keys.LRI.DURATION: data_values.LRI_DURATION,
        }[key]
    except KeyError:
        raise ValueError(f"Unrecognized key {key}")

    demography = get_data(data_keys.POPULATION.DEMOGRAPHY, location)
    duration_draws = (
        get_random_variable_draws(metadata.ARTIFACT_COLUMNS, *distribution)
        / metadata.YEAR_DURATION
    )

    duration = pd.DataFrame(
        [duration_draws], columns=metadata.ARTIFACT_COLUMNS, index=demography.index
    )

    return duration.droplevel("location")


def load_prevalence_from_incidence_and_duration(key: str, location: str) -> pd.DataFrame:
    try:
        cause = {
            data_keys.DIARRHEA.PREVALENCE: data_keys.DIARRHEA,
            data_keys.LRI.PREVALENCE: data_keys.LRI,
        }[key]
    except KeyError:
        raise ValueError(f"Unrecognized key {key}")

    incidence_rate = get_data(cause.INCIDENCE_RATE, location)
    duration = get_data(cause.DURATION, location)
    prevalence = incidence_rate * duration

    # get enn prevalence
    birth_prevalence = data_values.BIRTH_PREVALENCE_OF_ZERO
    enn_prevalence = prevalence.query("age_start == 0")
    enn_prevalence = (birth_prevalence + enn_prevalence) / 2
    all_other_prevalence = prevalence.query("age_start != 0.0")

    prevalence = pd.concat([enn_prevalence, all_other_prevalence]).sort_index()

    # If cause is diarrhea, set early and late neonatal groups prevalence to that of post-neonatal age group
    if key == data_keys.DIARRHEA.PREVALENCE:
        prevalence = utilities.scrub_neonatal_age_groups(prevalence)
    return prevalence


def load_remission_rate_from_duration(key: str, location: str) -> pd.DataFrame:
    try:
        cause = {
            data_keys.DIARRHEA.REMISSION_RATE: data_keys.DIARRHEA,
            data_keys.LRI.REMISSION_RATE: data_keys.LRI,
        }[key]
    except KeyError:
        raise ValueError(f"Unrecognized key {key}")
    step_size = 4 / 365  # years
    duration = get_data(cause.DURATION, location)
    remission_rate = (-1 / step_size) * np.log(1 - step_size / duration)

    if key == data_keys.DIARRHEA.REMISSION_RATE:
        remission_rate.loc[remission_rate.index.get_level_values('age_start') < metadata.NEONATAL_END_AGE, :] = 0
    return remission_rate


def load_emr_from_csmr_and_prevalence(key: str, location: str) -> pd.DataFrame:
    try:
        cause = {
            data_keys.DIARRHEA.EMR: data_keys.DIARRHEA,
            data_keys.LRI.EMR: data_keys.LRI,
        }[key]
    except KeyError:
        raise ValueError(f"Unrecognized key {key}")

    csmr = get_data(cause.CSMR, location)
    prevalence = get_data(cause.PREVALENCE, location)
    data = (csmr / prevalence).fillna(0)
    data = data.replace([np.inf, -np.inf], 0)

    if key == data_keys.DIARRHEA.EMR:
        data.loc[data.index.get_level_values('age_start') < metadata.NEONATAL_END_AGE, :] = 0
    return data


def load_pem_disability_weight(key: str, location: str) -> pd.DataFrame:
    try:
        pem_sequelae = {
            data_keys.MODERATE_PEM.DISABILITY_WEIGHT: [
                sequelae.moderate_wasting_with_edema,
                sequelae.moderate_wasting_without_edema,
            ],
            data_keys.SEVERE_PEM.DISABILITY_WEIGHT: [
                sequelae.severe_wasting_with_edema,
                sequelae.severe_wasting_without_edema,
            ],
        }[key]
    except KeyError:
        raise ValueError(f"Unrecognized key {key}")

    prevalence_disability_weight = []
    state_prevalence = []
    for s in pem_sequelae:
        sequela_prevalence = interface.get_measure(s, "prevalence", location)
        sequela_disability_weight = interface.get_measure(s, "disability_weight", location)

        prevalence_disability_weight += [sequela_prevalence * sequela_disability_weight]
        state_prevalence += [sequela_prevalence]

    disability_weight = (
        (sum(prevalence_disability_weight) / sum(state_prevalence))
        .fillna(0)
        .droplevel("location")
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
        raise ValueError(f"Unrecognized key {key}")

    entity = utilities.get_entity(data_keys.LBWSG.EXPOSURE)
    data = utilities.load_lbwsg_exposure(location)
    # This category was a mistake in GBD 2019, so drop.
    extra_residual_category = vi_globals.EXTRA_RESIDUAL_CATEGORY[entity.name]
    data = data.loc[data['parameter'] != extra_residual_category]
    idx_cols = ['location_id', 'age_group_id', 'year_id', 'sex_id', 'parameter']
    data = data.set_index(idx_cols)[vi_globals.DRAW_COLUMNS]

    # Sometimes there are data values on the order of 10e-300 that cause
    # floating point headaches, so clip everything to reasonable values
    data = data.clip(lower=vi_globals.MINIMUM_EXPOSURE_VALUE)

    # normalize so all categories sum to 1
    total_exposure = data.groupby(['location_id', 'age_group_id', 'sex_id']).transform('sum')
    data = (data / total_exposure).reset_index()
    data = reshape_to_vivarium_format(data, location)
    return data


def load_lbwsg_rr(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.LBWSG.RELATIVE_RISK:
        raise ValueError(f"Unrecognized key {key}")

    key = EntityKey(key)
    entity = utilities.get_entity(key)
    data = utilities.get_data(
        key,
        entity,
        location,
        gbd_constants.SOURCES.RR,
        "rei_id",
        metadata.AGE_GROUP.GBD_2019_LBWSG_RELATIVE_RISK,
        metadata.GBD_2019_ROUND_ID,
        "step4",
    )
    data = data[data["year_id"] == 2019].drop(columns="year_id")
    data = utilities.process_relative_risk(
        data,
        key,
        entity,
        location,
        metadata.GBD_2019_ROUND_ID,
        metadata.AGE_GROUP.GBD_2019,
        whitelist_sids=True,
    )
    data = data.query("year_start == 2019").droplevel(["affected_entity", "affected_measure"])
    data = data[~data.index.duplicated()]
    return data


def load_lbwsg_interpolated_rr(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.LBWSG.RELATIVE_RISK_INTERPOLATOR:
        raise ValueError(f"Unrecognized key {key}")

    rr = get_data(data_keys.LBWSG.RELATIVE_RISK, location).reset_index()
    rr["parameter"] = pd.Categorical(rr["parameter"], [f"cat{i}" for i in range(1000)])
    rr = (
        rr.sort_values("parameter")
        .set_index(metadata.ARTIFACT_INDEX_COLUMNS + ["parameter"])
        .stack()
        .unstack("parameter")
        .apply(np.log)
    )

    # get category midpoints
    def get_category_midpoints(lbwsg_type: str) -> pd.Series:
        categories = get_data(f"risk_factor.{data_keys.LBWSG.name}.categories", location)
        return utilities.get_intervals_from_categories(lbwsg_type, categories).apply(
            lambda x: x.mid
        )

    gestational_age_midpoints = get_category_midpoints("short_gestation")
    birth_weight_midpoints = get_category_midpoints("low_birth_weight")

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
            method="nearest",
            rescale=True,
        )
        # return a RectBivariateSpline object from the extrapolated values on grid
        return RectBivariateSpline(
            gestational_age_grid, birth_weight_grid, log_rr_grid_nearest, kx=1, ky=1
        )

    log_rr_interpolator = (
        rr.apply(make_interpolator, axis="columns")
        .apply(lambda x: pickle.dumps(x).hex())
        .unstack()
    )
    return log_rr_interpolator


def load_lbwsg_paf(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.LBWSG.PAF:
        raise ValueError(f"Unrecognized key {key}")

    location_mapper = {"Sub-Saharan Africa": "sub-saharan_africa",
                        "South Asia": "south_asia",
                       "LMICs": "lmics",
                       "Ethiopia": "ethiopia",
                       "Nigeria": "nigeria",
                       "India": "india"}

    output_dir = paths.TEMPORARY_PAF_DIR / location_mapper[location]
    paf_files = output_dir.glob("*.hdf")
    paf_data = pd.concat([pd.read_hdf(paf_file) for paf_file in paf_files]).sort_values(
        metadata.ARTIFACT_INDEX_COLUMNS + ["draw"]
    )

    paf_data["draw"] = paf_data["draw"].apply(lambda draw: f"draw_{draw}")

    paf_data = paf_data.set_index(metadata.ARTIFACT_INDEX_COLUMNS + ["draw"]).unstack()

    paf_data.columns = paf_data.columns.droplevel(0)
    paf_data.columns.name = None

    full_index = (
        get_data(data_keys.LBWSG.RELATIVE_RISK, location)
        .index.droplevel("parameter")
        .drop_duplicates()
    )

    paf_data = paf_data.reindex(full_index).fillna(0.0)
    return paf_data


def load_sids_csmr(key: str, location: str) -> pd.DataFrame:
    if key == data_keys.AFFECTED_UNMODELED_CAUSES.SIDS_CSMR:
        key = EntityKey(key)
        entity: Cause = utilities.get_entity(key)

        # get around the validation rejecting yll only causes
        entity.restrictions.yll_only = False
        entity.restrictions.yld_age_group_id_start = min(metadata.AGE_GROUP.GBD_2019_SIDS)
        entity.restrictions.yld_age_group_id_end = max(metadata.AGE_GROUP.GBD_2019_SIDS)

        data = interface.get_measure(entity, key.measure, location).droplevel("location")
        return data
    else:
        raise ValueError(f"Unrecognized key {key}")


def load_intervention_distribution(key: str, location: str) -> str:
    try:
        return {
            data_keys.IFA_SUPPLEMENTATION.DISTRIBUTION: data_values.MATERNAL_CHARACTERISTICS.DISTRIBUTION,
            data_keys.MMN_SUPPLEMENTATION.DISTRIBUTION: data_values.MATERNAL_CHARACTERISTICS.DISTRIBUTION,
            data_keys.BEP_SUPPLEMENTATION.DISTRIBUTION: data_values.MATERNAL_CHARACTERISTICS.DISTRIBUTION,
            data_keys.IV_IRON.DISTRIBUTION: data_values.MATERNAL_CHARACTERISTICS.DISTRIBUTION,
        }[key]
    except KeyError:
        raise ValueError(f'Unrecognized key {key}')


def load_intervention_categories(key: str, location: str) -> str:
    try:
        return {
            data_keys.IFA_SUPPLEMENTATION.CATEGORIES: data_values.MATERNAL_CHARACTERISTICS.CATEGORIES,
            data_keys.MMN_SUPPLEMENTATION.CATEGORIES: data_values.MATERNAL_CHARACTERISTICS.CATEGORIES,
            data_keys.BEP_SUPPLEMENTATION.CATEGORIES: data_values.MATERNAL_CHARACTERISTICS.CATEGORIES,
            data_keys.IV_IRON.CATEGORIES: data_values.MATERNAL_CHARACTERISTICS.CATEGORIES,
        }[key]
    except KeyError:
        raise ValueError(f'Unrecognized key {key}')


def load_dichotomous_treatment_exposure(key: str, location: str, **kwargs) -> pd.DataFrame:
    try:
        distribution_data = {
            data_keys.IFA_SUPPLEMENTATION.EXPOSURE:
                load_baseline_ifa_supplementation_coverage(location),
            data_keys.MMN_SUPPLEMENTATION.EXPOSURE:
                data_values.MATERNAL_CHARACTERISTICS.BASELINE_MMN_COVERAGE,
            data_keys.BEP_SUPPLEMENTATION.EXPOSURE:
                data_values.MATERNAL_CHARACTERISTICS.BASELINE_BEP_COVERAGE,
            data_keys.IV_IRON.EXPOSURE:
                data_values.MATERNAL_CHARACTERISTICS.BASELINE_IV_IRON_COVERAGE,
        }[key]
    except KeyError:
        raise ValueError(f'Unrecognized key {key}')
    return load_dichotomous_exposure(location, distribution_data, is_risk=False, **kwargs)


def load_treatment_excess_shift(key: str, location: str) -> pd.DataFrame:
    try:
        distribution_data = {
            data_keys.IFA_SUPPLEMENTATION.EXCESS_SHIFT:
                data_values.MATERNAL_CHARACTERISTICS.IFA_BIRTH_WEIGHT_SHIFT,
            data_keys.MMN_SUPPLEMENTATION.EXCESS_SHIFT:
                data_values.MATERNAL_CHARACTERISTICS.MMN_BIRTH_WEIGHT_SHIFT,
            data_keys.BEP_SUPPLEMENTATION.EXCESS_SHIFT:
                data_values.MATERNAL_CHARACTERISTICS.BEP_BIRTH_WEIGHT_SHIFT,
            data_keys.IV_IRON.EXCESS_SHIFT:
                data_values.MATERNAL_CHARACTERISTICS.IV_IRON_BIRTH_WEIGHT_SHIFT,
        }[key]
    except KeyError:
        raise ValueError(f'Unrecognized key {key}')
    return load_dichotomous_excess_shift(location, distribution_data, is_risk=False)


def load_dichotomous_exposure(
        location: str,
        distribution_data: Union[float, pd.DataFrame],
        is_risk: bool,
) -> pd.DataFrame:
    index = get_data(data_keys.POPULATION.DEMOGRAPHY, location).index
    if type(distribution_data) == float:
        base_exposure = pd.Series(distribution_data, index=index)
        exposed = (
            pd.DataFrame({f'draw_{i}': base_exposure for i in range(1000)})
            .droplevel('location')
        )
    else:
        exposed = distribution_data

    unexposed = 1 - exposed
    exposed['parameter'] = 'cat1' if is_risk else 'cat2'
    unexposed['parameter'] = 'cat2' if is_risk else 'cat1'

    exposure = (
        pd.concat([exposed, unexposed])
        .set_index('parameter', append=True)
        .sort_index()
    )
    return exposure


def load_dichotomous_excess_shift(
        location: str, distribution_data: Tuple, is_risk: bool
) -> pd.DataFrame:
    index = get_data(data_keys.POPULATION.DEMOGRAPHY, location).index
    shift = get_random_variable_draws(metadata.ARTIFACT_COLUMNS, *distribution_data)

    exposed = pd.DataFrame([shift], index=index)
    exposed['parameter'] = 'cat1' if is_risk else 'cat2'
    unexposed = pd.DataFrame([pd.Series(0.0, index=metadata.ARTIFACT_COLUMNS)], index=index)
    unexposed['parameter'] = 'cat2' if is_risk else 'cat1'

    excess_shift = pd.concat([exposed, unexposed])
    excess_shift['affected_entity'] = data_keys.LBWSG.BIRTH_WEIGHT_EXPOSURE.name
    excess_shift['affected_measure'] = data_keys.LBWSG.BIRTH_WEIGHT_EXPOSURE.measure

    excess_shift = (
        excess_shift
        .set_index(['affected_entity', 'affected_measure', 'parameter'], append=True)
        .sort_index()
    )
    return excess_shift


def load_risk_specific_shift(key: str, location: str) -> pd.DataFrame:
    try:
        key_group: data_keys.__AdditiveRisk = {
            data_keys.IFA_SUPPLEMENTATION.RISK_SPECIFIC_SHIFT: data_keys.IFA_SUPPLEMENTATION,
            data_keys.MMN_SUPPLEMENTATION.RISK_SPECIFIC_SHIFT: data_keys.MMN_SUPPLEMENTATION,
            data_keys.BEP_SUPPLEMENTATION.RISK_SPECIFIC_SHIFT: data_keys.BEP_SUPPLEMENTATION,
            data_keys.IV_IRON.RISK_SPECIFIC_SHIFT: data_keys.IV_IRON,
            data_keys.MATERNAL_BMI_ANEMIA.RISK_SPECIFIC_SHIFT: data_keys.MATERNAL_BMI_ANEMIA,
        }[key]
    except KeyError:
        raise ValueError(f'Unrecognized key {key}')

    # p_exposed * exposed_shift
    exposure = (
        get_data(key_group.EXPOSURE, location)
    )
    excess_shift = (
        get_data(key_group.EXCESS_SHIFT, location)
    )

    risk_specific_shift = (
        (exposure * excess_shift)
        .groupby(metadata.ARTIFACT_INDEX_COLUMNS + ['affected_entity', 'affected_measure'])
        .sum()
    )
    return risk_specific_shift


def load_baseline_ifa_supplementation_coverage(location: str) -> pd.DataFrame:

    index = get_data(data_keys.POPULATION.DEMOGRAPHY, location).index
    location_id = utility_data.get_location_id(location)
    intervention_scenarios = pd.read_csv(paths.MATERNAL_INTERVENTION_COVERAGE_CSV)

    df = intervention_scenarios.drop(
        columns=['Unnamed: 0', 'scale_up', 'oral_iron_scenario', 'antenatal_iv_iron_scenario',
                 'postpartum_iv_iron_scenario', 'antenatal_and_postpartum_iv_iron_scenario']
    )
    df = df.query('intervention == "ifa" & baseline_scenario == 1')
    df = df.set_index(['location_id', 'year', 'draw']).loc[location_id].drop(
        columns=['intervention', 'baseline_scenario'])
    df = df.value.unstack()
    df.columns.name = None
    df = df.reset_index().drop(columns=['year'])
    df = df.iloc[[0]]

    exposure = pd.DataFrame(data=np.repeat(df.values, len(index), axis=0), columns=df.columns,
                            index=index).droplevel("location")
    return exposure


def load_maternal_bmi_anemia_distribution(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.MATERNAL_BMI_ANEMIA.DISTRIBUTION:
        raise ValueError(f"Unrecognized key {key}")
    return 'ordered_polytomous'


def load_maternal_bmi_anemia_categories(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.MATERNAL_BMI_ANEMIA.CATEGORIES:
        raise ValueError(f"Unrecognized key {key}")
    return {
        "cat4": "Pre-pregnancy/first trimester BMI exposure >= 18.5 and Early pregnancy "
                "“untreated” hemoglobin exposure >= 10g/dL",
        "cat3": "Pre-pregnancy/first trimester BMI exposure < 18.5 and Early pregnancy "
                "“untreated” hemoglobin exposure >= 10g/dL",
        "cat2": "Pre-pregnancy/first trimester BMI exposure >= 18.5 and Early pregnancy "
                "“untreated” hemoglobin exposure < 10g/dL",
        "cat1": "Pre-pregnancy/first trimester BMI exposure < 18.5 and Early pregnancy "
                "“untreated” hemoglobin exposure < 10g/dL",
    }


def load_maternal_bmi_anemia_exposure(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.MATERNAL_BMI_ANEMIA.EXPOSURE:
        raise ValueError(f"Unrecognized key {key}")

    location_id = utility_data.get_location_id(location)
    index = get_data(data_keys.POPULATION.DEMOGRAPHY, location).index.droplevel('location')

    def _read_hgb_data(filename: str) -> pd.Series:
        raw_data = pd.read_csv(paths.RAW_DATA_DIR / filename)
        data = (
            raw_data.loc[raw_data['location_id'] == location_id, ['draw', 'value']]
            .set_index('draw')
            .squeeze()
        )
        data.index.name = None
        return data

    p_low_hgb = _read_hgb_data("pregnant_proportion_with_hgb_below_100.csv")
    p_low_bmi_given_low_hgb = _read_hgb_data(
        "prevalence_of_low_bmi_given_hemoglobin_below_10_age_weighted.csv"
    )
    p_low_bmi_given_high_hgb = _read_hgb_data(
        "prevalence_of_low_bmi_given_hemoglobin_above_10_age_weighted.csv"
    )

    cat4_exposure = pd.DataFrame([(1 - p_low_hgb) * (1 - p_low_bmi_given_high_hgb)], index=index)
    cat4_exposure['parameter'] = 'cat4'

    cat3_exposure = pd.DataFrame([(1 - p_low_hgb) * p_low_bmi_given_high_hgb], index=index)
    cat3_exposure['parameter'] = 'cat3'

    cat2_exposure = pd.DataFrame([p_low_hgb * (1 - p_low_bmi_given_low_hgb)], index=index)
    cat2_exposure['parameter'] = 'cat2'

    cat1_exposure = pd.DataFrame([p_low_hgb * p_low_bmi_given_low_hgb], index=index)
    cat1_exposure['parameter'] = 'cat1'

    exposure = pd.concat([cat4_exposure, cat3_exposure, cat2_exposure, cat1_exposure])

    exposure = (
        exposure
        .set_index(['parameter'], append=True)
        .sort_index()
    )

    return exposure


def load_maternal_bmi_anemia_excess_shift(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.MATERNAL_BMI_ANEMIA.EXCESS_SHIFT:
        raise ValueError(f"Unrecognized key {key}")

    index = get_data(data_keys.POPULATION.DEMOGRAPHY, location).index.droplevel('location')
    cat3_draws = get_random_variable_draws(
        metadata.ARTIFACT_COLUMNS,
        *data_values.MATERNAL_CHARACTERISTICS.BMI_ANEMIA_CAT3_BIRTH_WEIGHT_SHIFT
    )
    cat2_draws = get_random_variable_draws(
        metadata.ARTIFACT_COLUMNS,
        *data_values.MATERNAL_CHARACTERISTICS.BMI_ANEMIA_CAT2_BIRTH_WEIGHT_SHIFT
    )
    cat1_draws = get_random_variable_draws(
        metadata.ARTIFACT_COLUMNS,
        *data_values.MATERNAL_CHARACTERISTICS.BMI_ANEMIA_CAT1_BIRTH_WEIGHT_SHIFT
    )

    cat4_shift = pd.DataFrame(0.0, columns=metadata.ARTIFACT_COLUMNS, index=index)
    cat4_shift['parameter'] = 'cat4'
    
    cat3_shift = pd.DataFrame([cat3_draws], index=index)
    cat3_shift['parameter'] = 'cat3'
    
    cat2_shift = pd.DataFrame([cat2_draws], index=index)
    cat2_shift['parameter'] = 'cat2'
    
    cat1_shift = pd.DataFrame([cat1_draws], index=index)
    cat1_shift['parameter'] = 'cat1'

    excess_shift = pd.concat([cat4_shift, cat3_shift, cat2_shift, cat1_shift])
    excess_shift['affected_entity'] = data_keys.LBWSG.BIRTH_WEIGHT_EXPOSURE.name
    excess_shift['affected_measure'] = data_keys.LBWSG.BIRTH_WEIGHT_EXPOSURE.measure

    excess_shift = (
        excess_shift
        .set_index(['affected_entity', 'affected_measure', 'parameter'], append=True)
        .sort_index()
    )
    return excess_shift


def load_neonatal_lri_csmr(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.AFFECTED_UNMODELED_CAUSES.NEONATAL_LRI_CSMR:
        raise ValueError(f"Unrecognized key {key}")

    data = load_standard_data(data_keys.LRI.CSMR, location)
    data.loc[data.index.get_level_values('age_start') >= metadata.NEONATAL_END_AGE, :] = 0
    return data


def load_lri_csmr(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.LRI.CSMR:
        raise ValueError(f"Unrecognized key {key}")

    data = load_standard_data(data_keys.LRI.CSMR, location)
    data.loc[data.index.get_level_values('age_start') < metadata.NEONATAL_END_AGE, :] = 0
    return data


def load_diarrhea_csmr(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.DIARRHEA.CSMR:
        raise ValueError(f"Unrecognized key {key}")

    data = load_standard_data(data_keys.DIARRHEA.CSMR, location)
    data.loc[data.index.get_level_values('age_start') < metadata.NEONATAL_END_AGE, :] = 0
    return data


def load_neonatal_diarrhea_csmr(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.AFFECTED_UNMODELED_CAUSES.NEONATAL_DIARRHEAL_DISEASES_CSMR:
        raise ValueError(f"Unrecognized key {key}")

    data = load_standard_data(data_keys.DIARRHEA.CSMR, location)
    data.loc[data.index.get_level_values('age_start') >= metadata.NEONATAL_END_AGE, :] = 0
    return data


def load_diarrhea_birth_prevalence(key: str, location: str) -> pd.DataFrame:
    if key != data_keys.DIARRHEA.BIRTH_PREVALENCE:
        raise ValueError(f"Unrecognized key {key}")

    prevalence = get_data(data_keys.DIARRHEA.PREVALENCE, location)
    post_neonatal = prevalence.loc[
        (prevalence.index.get_level_values("age_start") >= metadata.NEONATAL_END_AGE)
        & (prevalence.index.get_level_values("age_start") < 1)
        ]
    data = post_neonatal.droplevel(['age_start', 'age_end'])

    return data


def reshape_to_vivarium_format(df, location):
    df = vi_utils.reshape(df, value_cols=vi_globals.DRAW_COLUMNS)
    df = vi_utils.scrub_gbd_conventions(df, location)
    df = vi_utils.split_interval(df, interval_column='age', split_column_prefix='age')
    df = vi_utils.split_interval(df, interval_column='year', split_column_prefix='year')
    df = vi_utils.sort_hierarchical_data(df)
    df.index = df.index.droplevel("location")
    return df
