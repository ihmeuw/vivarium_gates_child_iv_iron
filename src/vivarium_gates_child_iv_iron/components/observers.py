import pandas as pd

from vivarium.framework.engine import Builder
from vivarium_public_health.metrics.stratification import (
    ResultsStratifier as ResultsStratifier_,
    Source,
    SourceType,
)

from vivarium_gates_child_iv_iron.constants import data_keys


class ResultsStratifier(ResultsStratifier_):
    """Centralized component for handling results stratification.
    This should be used as a sub-component for observers.  The observers
    can then ask this component for population subgroups and labels during
    results production and have this component manage adjustments to the
    final column labels for the subgroups.
    """

    def register_stratifications(self, builder: Builder) -> None:
        """Register each desired stratification with calls to _setup_stratification"""
        super().register_stratifications(builder)

        self.setup_stratification(
            builder,
            name="wasting_state",
            sources=[Source(f'{data_keys.WASTING.name}.exposure', SourceType.PIPELINE)],
            categories={category.value for category in data_keys.CGFCategories},
            mapper=self.child_growth_risk_factor_stratification_mapper,
        )

        self.setup_stratification(
            builder,
            name="stunting_state",
            sources=[Source(f'{data_keys.STUNTING.name}.exposure', SourceType.PIPELINE)],
            categories={category.value for category in data_keys.CGFCategories},
            mapper=self.child_growth_risk_factor_stratification_mapper,
        )

    ###########################
    # Stratifications Details #
    ###########################

    # noinspection PyMethodMayBeStatic
    def child_growth_risk_factor_stratification_mapper(self, row: pd.Series) -> str:
    # applicable to stunting and wasting
        return {
            "cat4": data_keys.CGFCategories.UNEXPOSED.value,
            "cat3": data_keys.CGFCategories.MILD.value,
            "cat2": data_keys.CGFCategories.MODERATE.value,
            "cat1": data_keys.CGFCategories.SEVERE.value,
        }[row.squeeze()]
