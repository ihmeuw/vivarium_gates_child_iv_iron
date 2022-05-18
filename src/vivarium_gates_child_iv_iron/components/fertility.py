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


class FertilityFromOutputs:
    """
    This class will determine what simulants need to be added to the state table based on their birth data from existing
    output data.  Simulants will be registered to the state table on the time steps in which their birth takes place.
    """

    configuration_defaults = {
        "fertility": {
            "fertility_input_data_path": ""
        }
    }

    columns_created = ["age", "sex", "alive", "entrance_time", "exit_time"] # not sure if we need location?
    def __repr__(self):
        return "FertilityFromOutputs()"

    @property
    def name(self):
        return "output_data_fertility"

    def setup(self, builder):
        self.clock = builder.time.clock()
        self.fertility_data_directory = builder.fertility.fertility_input_data_path
        self.randomness = builder.randomness
        self.simulant_creator = builder.population.get_simulant_creator()

        builder.population.initializes_simulants(
            self.on_initialize_simulants, creates_columns=self.columns_created
        )
        builder.event.register_listener("time_step", self.on_time_step)

    def on_initialize_simulants(self) -> None:
        """
        Method to load existing fertility data to use as birth records.
        """
#        fertility_data_dir = self.fertility_data_directory
        fertility_data_dir = "/home/albrja/scratch/data/iv_iron_child/"
        file_path = glob.glob(fertility_data_dir + 'south_asia*.hdf')[0]
        # todo: fix path names to incorporate what draw and seed to use
        self.birth_records = pd.read_hdf(file_path)

    def on_time_step(self, event):
        """Adds new simulants every time step determined by a simulant's birth date in the output data.
        Parameters
        ----------
        event
            The event that triggered the function call.
        """
        birth_records = self.birth_records
        born_previous_step_idx = (birth_records['birth_date'] < self.clock()) & (
            birth_records['birth_date'] > self.clock() - event.step_size)
        simulants_to_add = birth_records[born_previous_step_idx]

        # todo: update pop config with new columns
        if len(simulants_to_add) > 0:
            self.simulant_creator(
                simulants_to_add,
                population_configuration={
                    "age_start": 0,
                    "age_end": 0,
                    "sim_state": "time_step",
                },
            )

