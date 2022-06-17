"""
================
Fertility Models
================

Fertility module to create simulants from existing data

"""
from typing import Dict

import pandas as pd
from pathlib import Path

from vivarium.framework.event import Event
from vivarium_public_health import utilities

PREGNANCY_DURATION = pd.Timedelta(days=9 * utilities.DAYS_PER_MONTH)


class FertilityLineList:
    """
    This class will determine what simulants need to be added to the state table based on their birth data from existing
    line list data.  Simulants will be registered to the state table on the time steps in which their birth takes place.
    """

    configuration_defaults = {}

    def __repr__(self):
        return "FertilityLineList()"

    @property
    def name(self):
        return "line_list_fertility"

    def setup(self, builder):
        self.clock = builder.time.clock()
        self.randomness = builder.randomness
        self.simulant_creator = builder.population.get_simulant_creator()

        # Requirements for input data
        self.fertility_data_directory = builder.configuration.input_data.fertility_input_data_path
        self.draw = builder.configuration.input_data.input_draw_number
        self.seed = builder.configuration.randomness.random_seed
        self.scenario = builder.configuration.intervention.scenario
        self.birth_records = self._get_birth_records()

        builder.event.register_listener("time_step", self.on_time_step)

    def _get_birth_records(self) -> Dict[int, pd.DataFrame]:
        """
        Method to load existing fertility data to use as birth records.
        """
        fertility_data_dir = Path(self.fertility_data_directory)
        file_path = fertility_data_dir / f'scenario_{self.scenario}_draw_{self.draw}_seed_{self.seed}.hdf'
        raw_birth_data = pd.read_hdf(file_path)
        # raw_birth_data = raw_birth_data.sort_values("birth_date")
        birth_years = raw_birth_data["birth_date"].apply(lambda ts: ts.year)
        birth_records = {year: raw_birth_data[birth_years == year] for year in birth_years.unique()}

        return birth_records

    def on_time_step(self, event: Event) -> None:
        """Adds new simulants every time step determined by a simulant's birth date in the line list data.
        Parameters
        ----------
        event
            The event that triggered the function call.
        """
        birth_records = self.birth_records[event.time.year]
        born_previous_step_mask = (birth_records['birth_date'] < self.clock()) & (
            birth_records['birth_date'] > self.clock() - event.step_size)
        # born_previous_step = birth_records[born_previous_step_mask]
        born_previous_step = birth_records.head(2)
        simulants_to_add = len(born_previous_step)

        if simulants_to_add > 0:
            self.simulant_creator(
                simulants_to_add,
                population_configuration={
                    "age_start": 0,
                    "age_end": 0,
                    "sim_state": "time_step",
                    "new_births": born_previous_step
                },
            )
