import itertools

import pandas as pd

from vivarium_gates_child_iv_iron.constants import data_keys, models

#################################
# Results columns and variables #
#################################

TOTAL_YLDS_COLUMN = 'years_lived_with_disability'
TOTAL_YLLS_COLUMN = 'years_of_life_lost'

# Columns from parallel runs
INPUT_DRAW_COLUMN = 'input_draw'
RANDOM_SEED_COLUMN = 'random_seed'

OUTPUT_INPUT_DRAW_COLUMN = 'input_data.input_draw_number'
OUTPUT_RANDOM_SEED_COLUMN = 'randomness.random_seed'
OUTPUT_SCENARIO_COLUMN = 'intervention.scenario'

STANDARD_COLUMNS = {
    'total_ylls': TOTAL_YLLS_COLUMN,
    'total_ylds': TOTAL_YLDS_COLUMN,
}

THROWAWAY_COLUMNS = [f"{state}_event_count" for state in models.STATES]

DEATH_COLUMN_TEMPLATE = 'death_due_to_{CAUSE_OF_DEATH}_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}'
YLLS_COLUMN_TEMPLATE = 'ylls_due_to_{CAUSE_OF_DEATH}_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}'
YLDS_COLUMN_TEMPLATE = 'ylds_due_to_{CAUSE_OF_DISABILITY}_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}'
DIARRHEA_STATE_PERSON_TIME_COLUMN_TEMPLATE = (
    'diarrheal_diseases_{DIARRHEA_STATE}_person_time_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}'
)
LRI_STATE_PERSON_TIME_COLUMN_TEMPLATE = (
    'lower_respiratory_infections_{LRI_STATE}_person_time_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}'
)
MEASLES_STATE_PERSON_TIME_COLUMN_TEMPLATE = (
    'measles_{MEASLES_STATE}_person_time_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}'
)
MODERATE_PEM_STATE_PERSON_TIME_COLUMN_TEMPLATE = (
    'moderate_protein_energy_malnutrition_{MODERATE_PEM_STATE}_person_time_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}'
)
SEVERE_PEM_STATE_PERSON_TIME_COLUMN_TEMPLATE = (
    'severe_protein_energy_malnutrition_{SEVERE_PEM_STATE}_person_time_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}'
)
DIARRHEA_TRANSITION_COUNT_COLUMN_TEMPLATE = (
    'diarrheal_diseases_{DIARRHEA_TRANSITION}_event_count_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}'
)
LRI_TRANSITION_COUNT_COLUMN_TEMPLATE = (
    'lower_respiratory_infections_{LRI_TRANSITION}_event_count_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}'
)
MEASLES_TRANSITION_COUNT_COLUMN_TEMPLATE = (
    'measles_{MEASLES_TRANSITION}_event_count_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}'
)
MODERATE_PEM_TRANSITION_COUNT_COLUMN_TEMPLATE = (
    'moderate_protein_energy_malnutrition_{MODERATE_PEM_TRANSITION}_event_count_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}'
)
SEVERE_PEM_TRANSITION_COUNT_COLUMN_TEMPLATE = (
    'severe_protein_energy_malnutrition_{SEVERE_PEM_TRANSITION}_event_count_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}'
)
STUNTING_STATE_PERSON_TIME_COLUMN_TEMPLATE = (
    'child_stunting_{CGF_RISK_STATE_NUMERIC}_person_time_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}_maternal_supplementation_{SUPPLEMENTATION}_iv_iron_{IV_IRON}'
)
WASTING_STATE_PERSON_TIME_COLUMN_TEMPLATE = (
    'child_wasting_{CGF_RISK_STATE_NUMERIC}_person_time_year_{YEAR}_sex_{SEX}_age_{AGE_GROUP}_maternal_supplementation_{SUPPLEMENTATION}_iv_iron_{IV_IRON}'
)
LOW_BIRTH_WEIGHT_SHORT_GESTATION_SUB_RISK_SUM_COLUM_TEMPLATE = (
    '{LBWSG_SUB_RISK}_sum_year_{YEAR}_sex_{SEX}_maternal_supplementation_{SUPPLEMENTATION}_iv_iron_{IV_IRON}_bmi_anemia_{BMI_ANEMIA}'
)
LIVE_BIRTHS_COLUMN_TEMPLATE = (
    'live_births_year_{YEAR}_sex_{SEX}_maternal_supplementation_{SUPPLEMENTATION}_iv_iron_{IV_IRON}_bmi_anemia_{BMI_ANEMIA}'
)
LOW_WEIGHT_BIRTHS_COLUMN_TEMPLATE = (
    'low_weight_births_year_{YEAR}_sex_{SEX}_maternal_supplementation_{SUPPLEMENTATION}_iv_iron_{IV_IRON}_bmi_anemia_{BMI_ANEMIA}'
)


COLUMN_TEMPLATES = {
    'deaths': DEATH_COLUMN_TEMPLATE,
    'ylls': YLLS_COLUMN_TEMPLATE,
    'ylds': YLDS_COLUMN_TEMPLATE,
    'diarrhea_state_person_time': DIARRHEA_STATE_PERSON_TIME_COLUMN_TEMPLATE,
    'measles_state_person_time': MEASLES_STATE_PERSON_TIME_COLUMN_TEMPLATE,
    'lri_state_person_time': LRI_STATE_PERSON_TIME_COLUMN_TEMPLATE,
    'moderate_pem_state_person_time': MODERATE_PEM_STATE_PERSON_TIME_COLUMN_TEMPLATE,
    'severe_pem_state_person_time': SEVERE_PEM_STATE_PERSON_TIME_COLUMN_TEMPLATE,
    'diarrhea_transition_count': DIARRHEA_TRANSITION_COUNT_COLUMN_TEMPLATE,
    'measles_transition_count': MEASLES_TRANSITION_COUNT_COLUMN_TEMPLATE,
    'lri_transition_count': LRI_TRANSITION_COUNT_COLUMN_TEMPLATE,
    'moderate_pem_transition_count': MODERATE_PEM_TRANSITION_COUNT_COLUMN_TEMPLATE,
    'severe_pem_transition_count': SEVERE_PEM_TRANSITION_COUNT_COLUMN_TEMPLATE,
    'stunting_state_person_time': STUNTING_STATE_PERSON_TIME_COLUMN_TEMPLATE,
    'wasting_state_person_time': WASTING_STATE_PERSON_TIME_COLUMN_TEMPLATE,
    'low_birth_weight_and_short_gestation_sum': LOW_BIRTH_WEIGHT_SHORT_GESTATION_SUB_RISK_SUM_COLUM_TEMPLATE,
    'live_births_count': LIVE_BIRTHS_COLUMN_TEMPLATE,
    'low_weight_births_count': LOW_WEIGHT_BIRTHS_COLUMN_TEMPLATE,
}

NON_COUNT_TEMPLATES = [
]

SEXES = ('male', 'female')
YEARS = tuple(range(2025, 2041))
AGE_GROUPS = (
    'early_neonatal',
    'late_neonatal',
    'post_neonatal',
    '1_to_4'
)
DICHOTOMOUS_RISK_STATES = ('cat2', 'cat1')
CAUSES_OF_DEATH = (
    'other_causes',
    models.DIARRHEA.STATE_NAME,
    models.MEASLES.STATE_NAME,
    models.LRI.STATE_NAME,
    models.MODERATE_PEM.STATE_NAME,
    models.SEVERE_PEM.STATE_NAME,
)
CAUSES_OF_DISABILITY = (
    models.DIARRHEA.STATE_NAME,
    models.MEASLES.STATE_NAME,
    models.LRI.STATE_NAME,
    models.MODERATE_PEM.STATE_NAME,
    models.SEVERE_PEM.STATE_NAME,
)
CGF_RISK_STATES = tuple([category.value for category in data_keys.CGFCategories])
TETRACHOTOMTOUS_RISK_STATES = ("cat1", "cat2", "cat3", "cat4")
LBWSG_SUB_RISKS = ("birth_weight", "gestational_age")
MATERNAL_SUPPLEMENTATION_TYPES = ("uncovered", "ifa", "mms", "bep")
DICHOTOMOUS_COVERAGE_STATES = ("uncovered", "covered")

TEMPLATE_FIELD_MAP = {
    'YEAR': YEARS,
    'SEX': SEXES,
    'AGE_GROUP': AGE_GROUPS,
    'CAUSE_OF_DEATH': CAUSES_OF_DEATH,
    'CAUSE_OF_DISABILITY': CAUSES_OF_DISABILITY,
    'DIARRHEA_STATE': models.DIARRHEA.STATES,
    'LRI_STATE': models.LRI.STATES,
    'MEASLES_STATE': models.MEASLES.STATES,
    'MODERATE_PEM_STATE': models.MODERATE_PEM.STATES,
    'SEVERE_PEM_STATE': models.SEVERE_PEM.STATES,
    'DIARRHEA_TRANSITION': models.DIARRHEA.TRANSITIONS,
    'LRI_TRANSITION': models.LRI.TRANSITIONS,
    'MEASLES_TRANSITION': models.MEASLES.TRANSITIONS,
    'MODERATE_PEM_TRANSITION': models.MODERATE_PEM.TRANSITIONS,
    'SEVERE_PEM_TRANSITION': models.SEVERE_PEM.TRANSITIONS,
    'CGF_RISK_STATE': CGF_RISK_STATES,
    "CGF_RISK_STATE_NUMERIC": TETRACHOTOMTOUS_RISK_STATES,
    "LBWSG_SUB_RISK": LBWSG_SUB_RISKS,
    "SUPPLEMENTATION": MATERNAL_SUPPLEMENTATION_TYPES,
    "IV_IRON": DICHOTOMOUS_COVERAGE_STATES,
    "BMI_ANEMIA": TETRACHOTOMTOUS_RISK_STATES,
}


# noinspection PyPep8Naming
def RESULT_COLUMNS(kind='all'):
    if kind not in COLUMN_TEMPLATES and kind != 'all':
        raise ValueError(f'Unknown result column type {kind}')
    columns = []
    if kind == 'all':
        for k in COLUMN_TEMPLATES:
            columns += RESULT_COLUMNS(k)
        columns = list(STANDARD_COLUMNS.values()) + columns
    else:
        template = COLUMN_TEMPLATES[kind]
        filtered_field_map = {field: values
                              for field, values in TEMPLATE_FIELD_MAP.items() if
                              f'{{{field}}}' in template}
        fields, value_groups = filtered_field_map.keys(), itertools.product(
            *filtered_field_map.values())
        for value_group in value_groups:
            columns.append(
                template.format(**{field: value for field, value in zip(fields, value_group)}))
    return columns


# noinspection PyPep8Naming
def RESULTS_MAP(kind):
    if kind not in COLUMN_TEMPLATES:
        raise ValueError(f'Unknown result column type {kind}')
    columns = []
    template = COLUMN_TEMPLATES[kind]
    filtered_field_map = {field: values
                          for field, values in TEMPLATE_FIELD_MAP.items() if
                          f'{{{field}}}' in template}
    fields, value_groups = list(filtered_field_map.keys()), list(
        itertools.product(*filtered_field_map.values()))
    for value_group in value_groups:
        columns.append(
            template.format(**{field: value for field, value in zip(fields, value_group)}))
    df = pd.DataFrame(value_groups, columns=map(lambda x: x.lower(), fields))
    df['key'] = columns
    df['measure'] = kind  # per researcher feedback, this column is useful, even when it's identical for all rows
    return df.set_index('key').sort_index()
