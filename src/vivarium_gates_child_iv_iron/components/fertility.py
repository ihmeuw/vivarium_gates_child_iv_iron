"""
================
Fertility Models
================

Fertility module to create simulants from existing data

"""
import numpy as np
import glob
import pandas as pd
from pathlib import Path

from vivarium_public_health import utilities
from vivarium_public_health.population.data_transformations import (
    get_live_births_per_year,
)

PREGNANCY_DURATION = pd.Timedelta(days=9 * utilities.DAYS_PER_MONTH)


class FertilityLineList:
    """
    This class will determine what simulants need to be added to the state table based on their birth data from existing
    line list data.  Simulants will be registered to the state table on the time steps in which their birth takes place.
    """

    configuration_defaults = {
        "fertility": {
            "fertility_input_data_path": ""
        }
    }

    def __repr__(self):
        return "FertilityLineList()"

    @property
    def name(self):
        return "line_list_fertility"

    def setup(self, builder):
        self.clock = builder.time.clock()
        self.birth_records = self._get_birth_records()
        self.fertility_data_directory = builder.fertility.fertility_input_data_path
        self.randomness = builder.randomness
        self.simulant_creator = builder.population.get_simulant_creator()

        builder.event.register_listener("time_step", self.on_time_step)

    def _get_birth_records(self) -> pd.DataFrame:
        """
        Method to load existing fertility data to use as birth records.
        """
        fertility_data_dir = self.fertility_data_directory
        file_path = glob.glob(fertility_data_dir + 'south_asia*.hdf')[0]
        # todo: fix path names to incorporate what draw and seed to use
        birth_records = pd.read_hdf(file_path)

        return birth_records

    def on_time_step(self, event):
        """Adds new simulants every time step determined by a simulant's birth date in the line list data.
        Parameters
        ----------
        event
            The event that triggered the function call.
        """
        birth_records = self.birth_records
        # todo: make sure this is behaving as expected - simulants born during previous time step i.e. they are now new births for current step
        born_previous_step_mask = (birth_records['birth_date'] < self.clock()) & (
            birth_records['birth_date'] > self.clock() - event.step_size)
        born_previous_step = birth_records[born_previous_step_mask]
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
