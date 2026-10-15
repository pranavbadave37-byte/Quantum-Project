import numpy as np
import pandas as pd

CLASSES = ["Healthy", "Matrix Crack", "Delamination", "Fibre Break"]


def generate_cfrp_data(n=800, seed=42):
    rng = np.random.default_rng(seed)
    per = n // 4
    rows = []
    centers = {
        "Healthy": [25, 55, 2.0, 60, 1.0, 70],
        "Matrix Crack": [40, 105, 4.0, 115, 5.0, 150],
        "Delamination": [55, 150, 5.5, 155, 9.0, 240],
        "Fibre Break": [75, 205, 7.0, 210, 14.0, 360],
    }
    scales = [7, 18, 0.8, 20, 2.0, 35]
    for label in CLASSES:
        for _ in range(per):
            vals = np.array(centers[label]) + rng.normal(0, scales)
            vals = np.maximum(vals, 0)
            rows.append([*vals, label])
    return pd.DataFrame(rows, columns=["load", "initiation_frequency", "amplitude", "average_frequency", "resistance_change", "energy", "damage"])


def synthetic_signal(label="Healthy", n=256, seed=3):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, n)
    base = 2.5 * np.sin(2 * np.pi * 18 * t) + 1.1 * np.sin(2 * np.pi * 34 * t)
    extra = {
        "Healthy": 0.0,
        "Matrix Crack": 1.2 * np.sin(2 * np.pi * 58 * t),
        "Delamination": 1.8 * np.sin(2 * np.pi * 72 * t),
        "Fibre Break": 2.4 * np.sin(2 * np.pi * 91 * t),
    }[label]
    noise = rng.normal(0, 0.65, n)
    return t, base + extra + noise
