"""
====================================
Low Birth Weight and Short Gestation
====================================

This is a module to subclass the LBWSG component in Vivrium Public Health to use its functionality but to do so on
simulants who are initialized from line list data.

"""
import pandas as pd

from vivarium.framework.engine import Builder
from vivarium.framework.population import SimulantData
from vivarium.framework.time import get_time_stamp
from vivarium_public_health.risks.implementations.low_birth_weight_and_short_gestation import LBWSGRisk


class LBWSGLineList(LBWSGRisk):
    """
    Component to initialize low birthweight and short gestation data for simulants based on existing line list data.
    """
    def __init__(self):
        super().__init__()

    @property
    def name(self)-> str:
        return "line_list_low_birth_weight_and_short_gestation"

    def __repr__(self):
        return "LBWSGLineList()"

    # noinspection PyAttributeOutsideInit
    def setup(self, builder: Builder):
        super().setup(builder)
        self.start_time = get_time_stamp(builder.configuration.time.start)

    def on_initialize_simulants(self, pop_data: SimulantData) -> None:

        columns = ["birth_weight_exposure", "gestational_age_exposure"]
        new_simulants = pd.DataFrame(columns=columns)

        if pop_data.creation_time >= self.start_time:
            new_births = pop_data.user_data["new_births"]
            new_births = new_births.reindex(index=pop_data.index)

            # Create columns for state table
            new_simulants = new_simulants.reindex(index=pop_data.index)
            new_simulants["birth_weight_exposure"] = new_births["birth_weight"]
            new_simulants["gestational_age_exposure"] = new_births["gestational_age"]

        self.population_view.update(new_simulants)
