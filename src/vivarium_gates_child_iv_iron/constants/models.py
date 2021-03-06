from typing import List, Tuple

from vivarium_gates_child_iv_iron.constants import data_keys


class TransitionString(str):

    def __new__(cls, value):
        # noinspection PyArgumentList
        obj = str.__new__(cls, value.lower())
        obj.from_state, obj.to_state = value.split('_TO_')
        return obj


# noinspection PyPep8Naming
class __SISModel:
    def __init__(self, model_name: str):
        self.MODEL_NAME = model_name
        self.SUSCEPTIBLE_STATE_NAME: str = f'susceptible_to_{self.MODEL_NAME}'
        self.STATE_NAME: str = self.MODEL_NAME
        self.STATES: Tuple[str, ...] = (self.SUSCEPTIBLE_STATE_NAME, self.STATE_NAME)
        self.TRANSITIONS: Tuple[TransitionString, ...] = (
            TransitionString(f'{self.SUSCEPTIBLE_STATE_NAME}_TO_{self.STATE_NAME}'),
            TransitionString(f'{self.STATE_NAME}_TO_{self.SUSCEPTIBLE_STATE_NAME}'),
        )

###########################
# Disease Model variables #
###########################

DIARRHEA = __SISModel(data_keys.DIARRHEA.name)
LRI = __SISModel(data_keys.LRI.name)
MEASLES = __SISModel(data_keys.MEASLES.name)
MODERATE_PEM = __SISModel(data_keys.MODERATE_PEM.name)
SEVERE_PEM = __SISModel(data_keys.SEVERE_PEM.name)

CAUSE_MODELS: List[__SISModel] = [
    DIARRHEA,
    LRI,
    MEASLES,
    MODERATE_PEM,
    SEVERE_PEM
]

STATES = tuple(state for model in CAUSE_MODELS for state in model.STATES)
TRANSITIONS = tuple(state for model in CAUSE_MODELS for state in model.TRANSITIONS)
