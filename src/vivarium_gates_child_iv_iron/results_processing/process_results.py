from pathlib import Path
from typing import Dict, NamedTuple, List, Union

import pandas as pd
from loguru import logger
import yaml

from vivarium_gates_child_iv_iron.constants import results, scenarios


SCENARIO_COLUMN = 'scenario'
GROUPBY_COLUMNS = [
    results.INPUT_DRAW_COLUMN,
    SCENARIO_COLUMN
]
OUTPUT_COLUMN_SORT_ORDER = [
    'age_group',
    'sex',
    'year',
    'risk',
    'cause',
    'measure',
    'input_draw'
]
RENAME_COLUMNS = {
    'age_group': 'age',
    'cause_of_death': 'cause',
}


def make_measure_data(data: pd.DataFrame, disaggregate_seeds: bool):
    measure_data = MeasureData(
        ylls=get_by_cause_measure_data(data, 'ylls', disaggregate_seeds),
        ylds=get_by_cause_measure_data(data, 'ylds', disaggregate_seeds),
        deaths=get_by_cause_measure_data(data, 'deaths', disaggregate_seeds),
        diarrhea_state_person_time=get_state_person_time_measure_data(
            data, 'diarrhea_state_person_time', disaggregate_seeds
        ),
        lri_state_person_time=get_state_person_time_measure_data(
            data, 'lri_state_person_time', disaggregate_seeds
        ),
        measles_state_person_time=get_state_person_time_measure_data(
            data, 'measles_state_person_time', disaggregate_seeds
        ),
        moderate_pem_state_person_time=get_state_person_time_measure_data(
            data, 'moderate_pem_state_person_time', disaggregate_seeds
        ),
        severe_pem_state_person_time=get_state_person_time_measure_data(
            data, 'severe_pem_state_person_time', disaggregate_seeds
        ),
        diarrhea_transition_count=get_transition_count_measure_data(
            data, 'diarrhea_transition_count', disaggregate_seeds
        ),
        lri_transition_count=get_transition_count_measure_data(
            data, 'lri_transition_count', disaggregate_seeds
        ),
        measles_transition_count=get_transition_count_measure_data(
            data, 'measles_transition_count', disaggregate_seeds
        ),
        moderate_pem_transition_count=get_transition_count_measure_data(
            data, 'moderate_pem_transition_count', disaggregate_seeds
        ),
        severe_pem_transition_count=get_transition_count_measure_data(
            data, 'severe_pem_transition_count', disaggregate_seeds
        ),
        stunting_state_person_time=get_state_person_time_measure_data(
            data, 'stunting_state_person_time', disaggregate_seeds),
        wasting_state_person_time=get_state_person_time_measure_data(
            data, 'wasting_state_person_time', disaggregate_seeds
        ),
        low_birth_weight_and_short_gestation_sum=get_measure_data(
            data, 'low_birth_weight_and_short_gestation_sum', disaggregate_seeds
        ),
        live_births_count=get_measure_data(data, 'live_births_count', disaggregate_seeds),
        low_weight_births_count=get_measure_data(data, 'low_weight_births_count', disaggregate_seeds),
    )
    return measure_data


class MeasureData(NamedTuple):
    ylls: pd.DataFrame
    ylds: pd.DataFrame
    deaths: pd.DataFrame
    diarrhea_state_person_time: pd.DataFrame
    lri_state_person_time: pd.DataFrame
    measles_state_person_time: pd.DataFrame
    moderate_pem_state_person_time: pd.DataFrame
    severe_pem_state_person_time: pd.DataFrame
    diarrhea_transition_count: pd.DataFrame
    lri_transition_count: pd.DataFrame
    measles_transition_count: pd.DataFrame
    moderate_pem_transition_count: pd.DataFrame
    severe_pem_transition_count: pd.DataFrame
    stunting_state_person_time: pd.DataFrame
    wasting_state_person_time: pd.DataFrame
    low_birth_weight_and_short_gestation_sum: pd.DataFrame
    live_births_count: pd.DataFrame
    low_weight_births_count: pd.DataFrame

    def dump(self, output_dir: Path):
        for key, df in self._asdict().items():
            df.to_hdf(output_dir / f'{key}.hdf', key=key)
            df.to_csv(output_dir / f'{key}.csv')


def read_data(path: Path, single_run: bool) -> (pd.DataFrame, List[str]):
    data = pd.read_hdf(path)
    # noinspection PyUnresolvedReferences
    data = (
        data
        .drop(columns=data.columns.intersection(results.THROWAWAY_COLUMNS))
        .reset_index(drop=True)
        .rename(
            columns={
                results.OUTPUT_SCENARIO_COLUMN: SCENARIO_COLUMN,
                results.OUTPUT_INPUT_DRAW_COLUMN: results.INPUT_DRAW_COLUMN,
                results.OUTPUT_RANDOM_SEED_COLUMN: results.RANDOM_SEED_COLUMN,
            }
        )
    )
    if single_run:
        data[results.INPUT_DRAW_COLUMN] = 0
        data[results.RANDOM_SEED_COLUMN] = 0
        data[SCENARIO_COLUMN] = scenarios.INTERVENTION_SCENARIOS.BASELINE.name
        keyspace = {
            results.INPUT_DRAW_COLUMN: [0],
            results.RANDOM_SEED_COLUMN: [0],
            results.OUTPUT_SCENARIO_COLUMN: [scenarios.INTERVENTION_SCENARIOS.BASELINE.name]
        }
    else:
        data[results.INPUT_DRAW_COLUMN] = data[results.INPUT_DRAW_COLUMN].astype(int)
        data[results.RANDOM_SEED_COLUMN] = data[results.RANDOM_SEED_COLUMN].astype(int)
        with (path.parent / 'keyspace.yaml').open() as f:
            keyspace = yaml.full_load(f)
    return data, keyspace


def filter_out_incomplete(data: pd.DataFrame, keyspace: Dict[str, Union[str, int]]) -> pd.DataFrame:
    output = []
    for draw in keyspace[results.INPUT_DRAW_COLUMN]:
        # For each draw, gather all random seeds completed for all scenarios.
        random_seeds = set(keyspace[results.RANDOM_SEED_COLUMN])
        draw_data = data.loc[data[results.INPUT_DRAW_COLUMN] == draw]
        for scenario in keyspace[results.OUTPUT_SCENARIO_COLUMN]:
            seeds_in_data = draw_data.loc[
                data[SCENARIO_COLUMN] == scenario, results.RANDOM_SEED_COLUMN
            ].unique()
            random_seeds = random_seeds.intersection(seeds_in_data)
        draw_data = draw_data.loc[draw_data[results.RANDOM_SEED_COLUMN].isin(random_seeds)]
        output.append(draw_data)
    return pd.concat(output, ignore_index=True).reset_index(drop=True)


def aggregate_over_seed(data: pd.DataFrame) -> pd.DataFrame:
    non_count_columns = []
    for non_count_template in results.NON_COUNT_TEMPLATES:
        non_count_columns += results.RESULT_COLUMNS(non_count_template)
    count_columns = [c for c in data.columns if c not in non_count_columns + GROUPBY_COLUMNS]

    # non_count_data = data[non_count_columns + GROUPBY_COLUMNS].groupby(GROUPBY_COLUMNS).mean()
    count_data = data[count_columns + GROUPBY_COLUMNS].groupby(GROUPBY_COLUMNS).sum()
    return pd.concat([
        count_data,
        # non_count_data
    ], axis=1).reset_index()


def pivot_data(data: pd.DataFrame, disaggregate_seeds: bool) -> pd.DataFrame:
    if disaggregate_seeds:
        groupby_cols = GROUPBY_COLUMNS + [results.RANDOM_SEED_COLUMN]
    else:
        groupby_cols = GROUPBY_COLUMNS
    return (
        data
        .set_index(groupby_cols)
        .stack()
        .reset_index()
        .rename(columns={f'level_{len(groupby_cols)}': 'key', 0: 'value'})
    )


def sort_data(data: pd.DataFrame, disaggregate_seeds: bool) -> pd.DataFrame:
    if disaggregate_seeds:
        output_cols_sort_order = OUTPUT_COLUMN_SORT_ORDER + [results.RANDOM_SEED_COLUMN]
    else:
        output_cols_sort_order = OUTPUT_COLUMN_SORT_ORDER
    sort_order = [c for c in output_cols_sort_order if c in data.columns]
    other_cols = [c for c in data.columns if c not in sort_order and c != 'value']
    data = data[sort_order + other_cols + ['value']].sort_values(sort_order)
    return data.reset_index(drop=True)


def apply_results_map(data: pd.DataFrame, kind: str) -> pd.DataFrame:
    logger.info(f"Mapping {kind} data to stratifications.")
    map_df = results.RESULTS_MAP(kind)
    data = data.set_index('key')
    data = data.join(map_df).reset_index(drop=True)
    data = data.rename(columns=RENAME_COLUMNS)
    logger.info(f"Mapping {kind} complete.")
    return data


def get_population_data(data: pd.DataFrame, disaggregate_seeds: bool) -> pd.DataFrame:
    if disaggregate_seeds:
        groupby_cols = GROUPBY_COLUMNS + [results.RANDOM_SEED_COLUMN]
    else:
        groupby_cols = GROUPBY_COLUMNS

    total_pop = pivot_data(data[[results.TOTAL_POPULATION_COLUMN]
                                + results.RESULT_COLUMNS('population')
                                + groupby_cols], disaggregate_seeds)
    total_pop = total_pop.rename(columns={'key': 'measure'})
    return sort_data(total_pop, disaggregate_seeds)


def get_measure_data(data: pd.DataFrame, measure: str, disaggregate_seeds: bool) -> pd.DataFrame:
    if disaggregate_seeds:
        data = pivot_data(
            data[results.RESULT_COLUMNS(measure) + GROUPBY_COLUMNS + [results.RANDOM_SEED_COLUMN]],
            disaggregate_seeds
        )
    else:
        data = pivot_data(data[results.RESULT_COLUMNS(measure) + GROUPBY_COLUMNS], disaggregate_seeds)
    data = apply_results_map(data, measure)
    return sort_data(data, disaggregate_seeds)


def get_by_cause_measure_data(data: pd.DataFrame, measure: str, disaggregate_seeds: bool) -> pd.DataFrame:
    data = get_measure_data(data, measure, disaggregate_seeds)
    return sort_data(data, disaggregate_seeds)


def get_state_person_time_measure_data(data: pd.DataFrame, measure: str, disaggregate_seeds: bool) -> pd.DataFrame:
    data = get_measure_data(data, measure, disaggregate_seeds)
    return sort_data(data, disaggregate_seeds)


def get_transition_count_measure_data(data: pd.DataFrame, measure: str, disaggregate_seeds: bool) -> pd.DataFrame:
    # Oops, edge case.
    data = data.drop(columns=[c for c in data.columns if 'event_count' in c and str(results.YEARS[-1]+1) in c])
    data = get_measure_data(data, measure, disaggregate_seeds)
    return sort_data(data, disaggregate_seeds)
