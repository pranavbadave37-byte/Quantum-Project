"""Illustrative thermally-activated healing model (shared with the JS simulator).

h_eq(T)  : sigmoid capacity of the polymer to heal at temperature T (needs T > onset)
k(T)     : Arrhenius rate constant [1/min], referenced to 120 C
dh/dt    : k(T) * (h_eq(T) - h)   (healed bonds do not un-heal on cooling)
Educational toy model - not a validated polymer-chemistry model.
"""
import numpy as np

R = 8.314
T_REF = 393.15  # 120 C
K_REF = 0.12    # 1/min at 120 C
T_DEG = 190.0   # thermal degradation warning (C)


def h_eq(T, t_onset=60.0):
    return 1.0 / (1.0 + np.exp(-(np.asarray(T, float) - (t_onset + 25.0)) / 10.0))


def rate(T, ea_kj=80.0):
    Tk = np.asarray(T, float) + 273.15
    return K_REF * np.exp(ea_kj * 1000.0 / R * (1.0 / T_REF - 1.0 / Tk))


def healing_curve(T, minutes, t_onset=60.0, ea_kj=80.0, n=200):
    t = np.linspace(0, minutes, n)
    heq, k = float(h_eq(T, t_onset)), float(rate(T, ea_kj))
    return t, heq * (1.0 - np.exp(-k * t))


def time_to(T, target=0.9, t_onset=60.0, ea_kj=80.0):
    heq, k = float(h_eq(T, t_onset)), float(rate(T, ea_kj))
    if heq <= target:
        return float("inf")
    return float(-np.log(1 - target / heq) / k)
