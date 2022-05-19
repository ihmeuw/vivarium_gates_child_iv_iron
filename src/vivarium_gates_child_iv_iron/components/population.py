"""
==========================
Module for Base Population
==========================

This module contains a component for creating a base population from line list data.

"""
import glob
from typing import Callable, Dict, List

import numpy as np
import pandas as pd
from vivarium.framework.engine import Builder
from vivarium.framework.event import Event
from vivarium.framework.population import SimulantData
from vivarium.framework.randomness import RandomnessStream

from vivarium_public_health import utilities
from vivarium_public_health.population.base_population import BasePopulation, generate_population
from vivarium_public_health.population.data_transformations import (
    assign_demographic_proportions,
    load_population_structure,
    rescale_binned_proportions,
    smooth_ages,
)


class PopulationLineList(BasePopulation):
    """
    Component to produce and age simulants based on line list data.
    """

    def __init__(self):
        super().__init__()

    def setup(self, builder: Builder) -> None:
        super().setup(builder)
        self.birth_records = self._get_birth_records()
        self.fertility_data_directory = builder.fertility.fertility_input_data_path

    @property
    def name(self) -> str:
        return "line_list_population"

    def on_initialize_simulants(self, pop_data: SimulantData) -> None:
        """
        Creates simulants based on their birth date from the line list data.  Their demographic characteristics are also
        determined by the input data.
        """

        # todo: check dtypes of data due to pd.read_hdf
        new_births_index = pop_data.new_births
        birth_records = self.birth_records
        birth_records["age_start"] = self.config.age_start
        birth_records["age_end"] = self.config.age_end
        new_births = birth_records.iloc[new_births_index]

        creation_time = new_births.birth_date
        #todo fix this >> age_start and how to get these since they arent in Simulant data
        age_params = {
            "age_start": new_births.age_start
            "age_end": new_births.age_end,
        }

        self.population_view.update(
            generate_population(
                simulant_ids=new_births_index,
                creation_time=pop_data.creation_time,
                step_size=pop_data.creation_window,  # Not sure what to do about this
                age_params=age_params,
                population_data=new_births,   # columns?
                randomness_streams=self.randomness,
                register_simulants=self.register_simulants,
            )
        )

    def _get_birth_records(self) -> pd.DataFrame:
        """
        Method to load existing fertility data to use as birth records.
        """
        fertility_data_dir = self.fertility_data_directory
        file_path = glob.glob(fertility_data_dir + 'south_asia*.hdf')[0]
        # todo: fix path names to incorporate what draw and seed to use
        birth_records = pd.read_hdf(file_path)

        return birth_records
