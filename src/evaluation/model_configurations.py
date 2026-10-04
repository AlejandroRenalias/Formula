"""Explicit evaluation profiles; a recorded freeze chooses only the default profile."""
import json
from pathlib import Path

# wear, joint regression, offsets, estimate trend, extrapolate trend
PROFILES={
    'pit':(False,False,False,False,False),
    'wear':(True,False,False,False,False),
    'trend':(True,True,False,True,True),
    'offsets':(True,True,True,True,True),
    'ablation_a':(True,True,True,True,False),
    'ablation_b':(True,True,True,False,False),
}
FREEZE_PATH=Path(__file__).resolve().parents[2]/'data/evaluation/frozen_model.json'


def resolve_configuration(configuration=None):
    if configuration is None:
        configuration=json.loads(FREEZE_PATH.read_text())['configuration'] if FREEZE_PATH.exists() else 'offsets'
    if configuration not in PROFILES:raise ValueError(f'Unknown evaluation configuration: {configuration}')
    return configuration,PROFILES[configuration]


def frozen_uncertainty_multipliers():
    """Only the default frozen evaluation profile applies development calibration.

    Explicit historical profiles keep unit multipliers for reproducibility.
    """
    return (json.loads(FREEZE_PATH.read_text()).get('pace_uncertainty_multipliers', {})
            if FREEZE_PATH.exists() else {})
