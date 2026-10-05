"""Operational gate around the unchanged frozen dataset loader."""
from tools.reservation_gate import archive_path

def load_dataset(path):
    archive_path(path, purpose='evaluation')
    from src.evaluation.snapshot import load_dataset as frozen_load
    return frozen_load(path)
