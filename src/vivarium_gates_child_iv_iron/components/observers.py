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


class BirthObserver:

    configuration_defaults = {
        "observers": {
            "birth": {
                "exclude": [],
                "include": [],
            }
        }
    }

    metrics_pipeline_name = "metrics"

    # todo name columns
    birth_weight_column_name = ''
    gestational_age_column_name = ''

    def __repr__(self):
        return "BirthObserver()"

    ##############
    # Properties #
    ##############

    @property
    def name(self):
        return "birth_observer"

    #################
    # Setup methods #
    #################

    # noinspection PyAttributeOutsideInit
    def setup(self, builder: Builder) -> None:
        self.config = self._get_stratification_configuration(builder)
        self.stratifier = self._get_stratifier(builder)
        self.population_view = self._get_population_view(builder)

        self.counts = Counter()

        self._register_collect_metrics_listener(builder)
        self._register_metrics_modifier(builder)

    # noinspection PyMethodMayBeStatic
    def _get_stratification_configuration(self, builder: Builder) -> ConfigTree:
        return builder.configuration.observers.birth

    # noinspection PyMethodMayBeStatic
    def _get_stratifier(self, builder: Builder) -> ResultsStratifier:
        return builder.components.get_component(ResultsStratifier.name)


    def _get_population_view(self, builder: Builder) -> PopulationView:
        # todo get with correct columns

    def _register_collect_metrics_listener(self, builder: Builder) -> None:
        builder.event.register_listener("time_step", self.on_collect_metrics)

    def _register_metrics_modifier(self, builder: Builder) -> None:
        builder.value.register_value_modifier(
            self.metrics_pipeline_name,
            modifier=self.metrics,
            requires_columns=["age", "exit_time", "alive"],
        )

    ########################
    # Event-driven methods #
    ########################

    def on_collect_metrics(self, event: Event) -> None:
        pop = self.population_view.get(event.index)
        # todo make sure this works with initial initialization
        pop_born = pop[pop["entrance_time"] == event.time]

        groups = self.stratifier.group(
            pop_born.index, self.config.include, self.config.exclude
        )
        for label, group_mask in groups:
            pop_born_in_group = pop_born[group_mask]
            low_birth_weight_mask = pop_born_in_group[self.birth_weight_column_name] < birth_weight_limit
            new_observations = {
                f"live_births_{label}": pop_born_in_group.index.size,
                f"birth_weight_sum_{label}": pop_born_in_group[self.birth_weight_column_name].sum(),
                f"gestational_age_sum_{label}":
                    pop_born_in_group[self.gestational_age_column_name].sum(),
                f'low_weight_births_{label}': low_birth_weight_mask.sum()
            }
            self.counts.update(new_observations)

    ##################################
    # Pipeline sources and modifiers #
    ##################################

    def metrics(self, index: pd.Index, metrics: Dict) -> Dict:
        metrics.update(self.counts)

        return metrics