import numpy as np


def normalize_features(x):
    x = np.asarray(x, dtype=float)
    lo = np.array([0.0, 20.0, 0.0, 20.0, 0.0, 0.0])
    hi = np.array([100.0, 250.0, 10.0, 250.0, 20.0, 500.0])
    return np.clip((x - lo) / (hi - lo), 0, 1)


def ry(theta):
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return np.array([[c, -s], [s, c]], dtype=complex)


def rz(theta):
    return np.array([[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]], dtype=complex)


def kron(a, b):
    return np.kron(a, b)


def quantum_state(features):
    """Encode 6 normalized CFRP features into a simulated 2-qubit state."""
    z = normalize_features(features)
    q0 = ry(np.pi * z[0]) @ rz(np.pi * z[1]) @ np.array([1, 0], dtype=complex)
    q1 = ry(np.pi * z[2]) @ rz(np.pi * z[3]) @ np.array([1, 0], dtype=complex)
    state = kron(q0, q1)
    # Feature-dependent phase coupling, kept normalized.
    phase = np.exp(1j * np.pi * (z[4] - z[5]))
    state = state * phase
    return state / np.linalg.norm(state)


def fidelity(a, b):
    a, b = np.asarray(a), np.asarray(b)
    return float(np.abs(np.vdot(a, b)) ** 2)


def fidelity_kernel(X, Y=None):
    if Y is None:
        Y = X
    A = np.array([quantum_state(x) for x in X])
    B = np.array([quantum_state(y) for y in Y])
    return np.abs(A.conj() @ B.T) ** 2


def z_expectations(state):
    probs = np.abs(state) ** 2
    z0 = probs[0] + probs[1] - probs[2] - probs[3]
    z1 = probs[0] - probs[1] + probs[2] - probs[3]
    return float(z0), float(z1)


def quantum_sensing_score(features, shots=512, seed=7):
    rng = np.random.default_rng(seed)
    state = quantum_state(features)
    p = np.abs(state) ** 2
    counts = rng.multinomial(shots, p)
    measured = counts / shots
    z0 = measured[0] + measured[1] - measured[2] - measured[3]
    z1 = measured[0] - measured[1] + measured[2] - measured[3]
    # A normalized anomaly score for the dashboard.
    score = float(np.clip(1 - (abs(z0) + abs(z1)) / 2, 0, 1))
    return score, counts, measured


def qft_amplitudes(signal):
    signal = np.asarray(signal, dtype=complex)
    n = len(signal)
    return np.fft.fft(signal) / np.sqrt(n)


def signal_damage_score(signal):
    spectrum = np.abs(qft_amplitudes(signal))
    half = spectrum[: len(spectrum) // 2]
    if half.max() == 0:
        return 0.0, half
    peak_ratio = float(np.max(half[2:]) / (np.mean(half) + 1e-9))
    return float(np.clip((peak_ratio - 1) / 5, 0, 1)), half


def vqe_material_score(params):
    """Tiny VQE-style variational search over a 2-qubit toy Hamiltonian.
    Lower energy is treated as a better candidate in this educational material screen.
    """
    theta, phi = params
    # A toy expectation landscape, not a physical CFRP chemistry Hamiltonian.
    energy = -0.9 * np.cos(theta) - 0.55 * np.cos(phi) + 0.35 * np.cos(theta - phi)
    return float(energy)


def run_vqe(steps=80):
    theta = np.linspace(0, 2 * np.pi, steps)
    phi = np.linspace(0, 2 * np.pi, steps)
    best = (999, 0, 0)
    for t in theta:
        for p in phi:
            e = vqe_material_score((t, p))
            if e < best[0]:
                best = (e, t, p)
    return best


def qaoa_healing_options():
    """Brute-force simulator for a small QAOA-style binary healing selection.
    We evaluate a cost function over the 3-bit action space to keep the demo transparent.
    """
    actions = [
        ("Resin infusion", 1, 0.85, 0.70),
        ("Patch reinforcement", 0, 0.65, 0.55),
        ("Heat-cure cycle", 0, 0.45, 0.40),
    ]
    rows = []
    for mask in range(8):
        selected = [actions[i] for i in range(3) if mask & (1 << i)]
        risk_reduction = sum(a[2] for a in selected)
        cost = sum(a[3] for a in selected)
        conflict = 0.35 if (mask & 1) and (mask & 4) else 0
        objective = 1.4 * risk_reduction - cost - conflict
        rows.append((mask, selected, objective))
    rows.sort(key=lambda r: r[2], reverse=True)
    return rows
