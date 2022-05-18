"""
================
Fertility Models
================

Fertility module to create simulants from existing data

"""
import numpy as np
import pandas as pd

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
            # todo: would this be a good place to flag whether we are using dummy data or real output data?
        }
    }

    def __repr__(self):
        return "FertilityFromOutputs()"

    @property
    def name(self):
        return "output_data_fertility"

    def setup(self, builder):
        self.clock = builder.time.clock()
        self.randomness = builder.randomness
        self.simulant_creator = builder.population.get_simulant_creator()

        builder.event.register_listener("time_step", self.on_time_step)

    def on_time_step(self, event):
        """Adds new simulants every time step determined by a simulant's birth date in the output data.
        Parameters
        ----------
        event
            The event that triggered the function call.
        """
        
        simulants_to_add = ()

        if simulants_to_add > 0:
            self.simulant_creator(
                simulants_to_add,
                population_configuration={
                    "age_start": 0,
                    "age_end": 0,
                    "sim_state": "time_step",
                },
            )

