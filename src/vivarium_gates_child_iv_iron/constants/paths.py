from pathlib import Path

import vivarium_gates_child_iv_iron
from vivarium_gates_child_iv_iron.constants import metadata

BASE_DIR = Path(vivarium_gates_child_iv_iron.__file__).resolve().parent

ARTIFACT_ROOT = Path(f"/share/costeffectiveness/artifacts/{metadata.PROJECT_NAME}/")
MODEL_SPEC_DIR = BASE_DIR / 'model_specifications'
RESULTS_ROOT = Path(f'/share/costeffectiveness/results/{metadata.PROJECT_NAME}/')

TEMPORARY_PAF_DIR = Path('/share/costeffectiveness/auxiliary_data/GBD_2019/01_original_data/population_attributable_fraction/risk_factor/lbwsg/data/')
