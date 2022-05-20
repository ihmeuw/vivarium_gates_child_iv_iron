"""
==========================
Module for Base Population
==========================

This module contains a component for creating a base population from line list data.

"""
import glob

import pandas as pd

from vivarium.framework.engine import Builder
from vivarium.framework.population import SimulantData

from vivarium_public_health.population.base_population import BasePopulation

from vivarium_gates_child_iv_iron.constants.metadata import LOCATIONS


class PopulationLineList(BasePopulation):
    """
    Component to produce and age simulants based on line list data.
    """

    def setup(self, builder: Builder) -> None:
        super().setup(builder)
        self.location = self._get_location(builder)

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

        new_births = pop_data.user_data["new_births"]
        new_births["alive"] = "alive"
        new_births["location"] = self.location
        new_births["entrance_time"] = pop_data.creation_time
        new_births["exit_time"] = pd.NaT
        new_births["location"] = self.location

        self.population_view.update(new_births)

    def _get_location(self, builder: Builder) -> str:
        return builder.data.load("population.location")
