"""
==========================
Module for Base Population
==========================

This module contains a component for creating a base population from line list data.

"""
import glob
import subprocess
from subprocess import Popen

import pandas as pd

from vivarium.framework.engine import Builder
from vivarium.framework.population import SimulantData
from vivarium.framework.time import get_time_stamp

from vivarium_public_health.population.base_population import BasePopulation


class PopulationLineList(BasePopulation):
    """
    Component to produce and age simulants based on line list data.
    """

    def setup(self, builder: Builder) -> None:
        super().setup(builder)
        self.start_time = get_time_stamp(builder.configuration.time.start)
        self.location = self._get_location(builder)
        subprocess.Popen(args='echo This is a test', shell=True)

    @property
    def name(self) -> str:
        return "line_list_population"

    def __repr__(self) -> str:
        return "PopulationLineList()"

    def on_initialize_simulants(self, pop_data: SimulantData) -> None:
        """
        Creates simulants based on their birth date from the line list data.  Their demographic characteristics are also
        determined by the input data.
        """
        columns = ["age", "sex", "alive", "location", "entrance_time", "exit_time"]
        new_simulants = pd.DataFrame(columns=columns, index=pop_data.index)

        if pop_data.creation_time >= self.start_time:
            new_births = pop_data.user_data["new_births"]
            new_births.index = pop_data.index

            # Create columns for state table
            new_simulants["age"] = 0.0
            new_simulants["sex"] = new_births["sex"]
            new_simulants["alive"] = "alive"
            new_simulants["location"] = self.location
            new_simulants["entrance_time"] = pop_data.creation_time
            new_simulants["exit_time"] = pd.NaT

        self.population_view.update(new_simulants)

    def _get_location(self, builder: Builder) -> str:
        return builder.data.load("population.location")
