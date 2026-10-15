import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent / "src"))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC

from data import CLASSES, generate_cfrp_data, synthetic_signal
from animations import breakage_html, healing_html, sensing_html, signal_html
from healing_model import h_eq, healing_curve, rate, time_to
from quantum_core import (
    fidelity,
    fidelity_kernel,
    quantum_sensing_score,
    quantum_state,
    qaoa_healing_options,
    signal_damage_score,
    run_vqe,
    vqe_material_score,
)

st.set_page_config(
    page_title="Q-CFRP Guardian",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Theme / UI
# -----------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #070b14;
  --panel: rgba(16, 24, 42, .82);
  --panel-2: rgba(21, 31, 53, .9);
  --line: rgba(148, 163, 184, .16);
  --text: #f4f7fb;
  --muted: #8fa0b8;
  --cyan: #39d9d1;
  --purple: #9b7cff;
  --blue: #5ca7ff;
  --green: #5ee7a5;
  --orange: #ffb86b;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp {
  background:
    radial-gradient(circle at 8% 0%, rgba(57,217,209,.13), transparent 28%),
    radial-gradient(circle at 92% 10%, rgba(155,124,255,.14), transparent 30%),
    linear-gradient(180deg, #080d18 0%, #060a12 100%);
  color: var(--text);
}
.block-container { max-width: 1500px; padding: 1.25rem 2rem 3rem; }

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0b1220 0%, #090f1b 100%);
  border-right: 1px solid rgba(148,163,184,.12);
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }

.brand {
  padding: 14px 14px 18px;
  margin-bottom: 12px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: linear-gradient(145deg, rgba(57,217,209,.10), rgba(155,124,255,.09));
}
.brand-icon { font-size: 28px; }
.brand-title { font-size: 18px; font-weight: 800; margin-top: 5px; }
.brand-sub { font-size: 11px; color: var(--muted); line-height: 1.45; margin-top: 4px; }

.sidebar-section {
  color: #6f819b; font-size: 10px; font-weight: 800; letter-spacing: 1.3px;
  text-transform: uppercase; margin: 18px 4px 7px;
}

.hero {
  padding: 28px 30px;
  border: 1px solid rgba(148,163,184,.18);
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(57,217,209,.11), rgba(155,124,255,.12) 55%, rgba(92,167,255,.07));
  box-shadow: 0 24px 70px rgba(0,0,0,.25);
  margin-bottom: 18px;
}
.hero h1 { margin: 0; font-size: 2.65rem; letter-spacing: -1.5px; }
.hero p { color: var(--muted); margin: 8px 0 0; max-width: 850px; line-height: 1.55; }
.pill {
  display: inline-block; padding: 5px 10px; border-radius: 999px; margin-bottom: 9px;
  background: rgba(57,217,209,.10); color: var(--cyan); border: 1px solid rgba(57,217,209,.26);
  font-size: 10px; font-weight: 800; letter-spacing: 1px;
}

.section-title { font-size: 20px; font-weight: 800; margin: 22px 0 10px; }
.section-sub { color: var(--muted); font-size: 13px; margin-bottom: 14px; }

.card {
  background: var(--panel); border: 1px solid var(--line); border-radius: 18px;
  padding: 17px; min-height: 110px; box-shadow: 0 12px 30px rgba(0,0,0,.12);
}
.card:hover { border-color: rgba(57,217,209,.28); }
.card-kicker { color: var(--cyan); font-size: 10px; font-weight: 800; letter-spacing: 1px; }
.card-title { font-weight: 700; margin-top: 7px; font-size: 14px; }
.card-desc { color: var(--muted); font-size: 11px; line-height: 1.45; margin-top: 6px; }

.control-box {
  padding: 15px 17px; border-radius: 18px; border: 1px solid var(--line);
  background: rgba(10,16,28,.75); margin-bottom: 14px;
}
.control-label { font-size: 11px; color: #9aabc0; text-transform: uppercase; letter-spacing: .8px; font-weight: 700; }

.status {
  padding: 10px 13px; border-radius: 12px; background: rgba(94,231,165,.08);
  border: 1px solid rgba(94,231,165,.22); color: #b8f6d4; font-size: 12px;
}
.warning {
  padding: 10px 13px; border-radius: 12px; background: rgba(255,184,107,.08);
  border: 1px solid rgba(255,184,107,.22); color: #ffd7aa; font-size: 12px;
}

[data-testid="stMetric"] {
  background: rgba(16,24,42,.72); border: 1px solid var(--line); padding: 12px 14px; border-radius: 15px;
}
[data-testid="stMetricLabel"] { color: var(--muted); }

div[data-testid="stButton"] button {
  border-radius: 11px; border: 1px solid rgba(57,217,209,.24);
  background: rgba(57,217,209,.08); color: #eafcfb; font-weight: 600;
}
div[data-testid="stButton"] button:hover { border-color: var(--cyan); color: white; }

hr { border-color: rgba(148,163,184,.10); }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
@st.cache_data

def get_data(seed=42, n=800):
    return generate_cfrp_data(n=n, seed=seed)


def dark_fig(fig, height=390):
    fig.update_layout(
        template="plotly_dark",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=55, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor="#111a2b"),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,.10)", zeroline=False)
    return fig


def metric_row(items):
    cols = st.columns(len(items))
    for col, (label, value, delta) in zip(cols, items):
        col.metric(label, value, delta)


def feature_row(load, freq, amp, resistance, energy, temp=25, noise=0.65):
    return np.array([load, freq, amp, freq, resistance, energy], dtype=float)


def nav_button(label, page):
    active = st.session_state.get("page", "Overview") == page
    if st.sidebar.button(("●  " if active else "○  ") + label, key="nav_" + page):
        st.session_state.page = page
        st.rerun()


# -----------------------------------------------------------------------------
# State
# -----------------------------------------------------------------------------
df = get_data()
features = ["load", "initiation_frequency", "amplitude", "average_frequency", "resistance_change", "energy"]
if "page" not in st.session_state:
    st.session_state.page = "Overview"

# -----------------------------------------------------------------------------
# Sidebar navigation
# -----------------------------------------------------------------------------
st.sidebar.markdown(
    """
<div class="brand">
  <div class="brand-icon">⚛️</div>
  <div class="brand-title">Q-CFRP Guardian</div>
  <div class="brand-sub">Interactive quantum-classical CFRP monitoring lab</div>
</div>
<div class="sidebar-section">Navigation</div>
""",
    unsafe_allow_html=True,
)

pages = [
    ("Overview", "Command Center"),
    ("Material Chemistry", "01 · VQE Material Screen"),
    ("Quantum Sensing", "02 · Structural Monitoring"),
    ("Signal Analysis", "03 · QFT Signal Analysis"),
    ("Quantum ML", "04 · Damage Classification"),
    ("Prediction", "05 · Damage Forecast"),
    ("Healing Optimizer", "06 · QAOA Strategy"),
    ("Autonomous Loop", "07 · Detect → Heal → Verify"),
]
for page, label in pages:
    nav_button(label, page)

st.sidebar.markdown('<div class="sidebar-section">Simulation</div>', unsafe_allow_html=True)
st.sidebar.caption("All controls below are live. Move a slider and the charts/metrics recalculate instantly.")
seed = st.sidebar.slider("Simulation seed", 1, 99, 42)
st.sidebar.markdown('<div class="sidebar-section">System</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="status">● Simulation engine online</div>', unsafe_allow_html=True)
st.sidebar.caption("Software simulation only • no physical actuator")

df = get_data(seed=seed)

# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------
st.markdown(
    """
<div class="hero">
  <div class="pill">7-IN-1 QUANTUM-CLASSICAL ENGINEERING LAB</div>
  <h1>⚛️ Q-CFRP Guardian</h1>
  <p>Interactive CFRP structural-health monitoring, damage intelligence, healing strategy optimization and autonomous decision-support prototype.</p>
</div>
""",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Overview
# -----------------------------------------------------------------------------
if st.session_state.page == "Overview":
    st.markdown('<div class="section-title">Live Command Center</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Use the control panel to create a simulated operating condition. Every downstream visualization responds to the values.</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**Live operating condition**")
        c1, c2, c3, c4 = st.columns(4)
        load = c1.slider("Applied load", 0.0, 100.0, 55.0, 1.0, key="ov_load")
        frequency = c2.slider("Acoustic / sensor frequency", 20.0, 250.0, 135.0, 1.0, key="ov_freq")
        amplitude = c3.slider("Signal amplitude", 0.0, 10.0, 5.0, .1, key="ov_amp")
        resistance = c4.slider("Resistance change", 0.0, 20.0, 8.0, .1, key="ov_res")
        c5, c6, c7, c8 = st.columns(4)
        energy = c5.slider("Acoustic energy", 0.0, 500.0, 230.0, 5.0, key="ov_energy")
        temperature = c6.slider("Temperature", -20, 120, 35, 1, key="ov_temp")
        sensor_noise = c7.slider("Sensor noise", 0.0, 1.5, .45, .05, key="ov_noise")
        healing = c8.slider("Healing effectiveness", 0, 100, 70, 1, key="ov_heal")

    x = feature_row(load, frequency, amplitude, resistance, energy, temperature, sensor_noise)
    state = quantum_state(x)
    anomaly, counts, probs = quantum_sensing_score(x, shots=512, seed=seed)
    damage_index = float(np.clip(.20*load/100 + .22*frequency/250 + .16*amplitude/10 + .20*resistance/20 + .22*energy/500, 0, 1))
    post_heal = max(0.0, damage_index * (1 - healing/100))
    health = 1 - post_heal

    metric_row([
        ("Damage index", f"{damage_index:.2f}", "live"),
        ("Post-healing index", f"{post_heal:.2f}", f"-{(damage_index-post_heal)*100:.0f}%"),
        ("Structural health", f"{health*100:.0f}%", None),
        ("Quantum anomaly", f"{anomaly:.2f}", None),
    ])

    left, right = st.columns([1.35, 1])
    with left:
        t = np.linspace(0, 1, 260)
        rng = np.random.default_rng(seed)
        live_signal = amplitude * np.sin(2*np.pi*(frequency/5)*t) + rng.normal(0, sensor_noise, len(t))
        fig = go.Figure(go.Scatter(x=t, y=live_signal, mode="lines", name="Sensor signal"))
        fig.update_layout(title="Live simulated sensor signal", xaxis_title="Time", yaxis_title="Amplitude")
        st.plotly_chart(dark_fig(fig, 390), use_container_width=True)
    with right:
        fig = go.Figure(go.Bar(x=["00", "01", "10", "11"], y=probs, name="Probability"))
        fig.update_layout(title="Quantum measurement distribution", yaxis_title="Probability")
        st.plotly_chart(dark_fig(fig, 390), use_container_width=True)

    st.markdown('<div class="section-title">Seven-layer pipeline</div>', unsafe_allow_html=True)
    cards = [
        ("01", "Material Chemistry", "VQE-style material-energy screening"),
        ("02", "Quantum Sensing", "Measurement + anomaly score"),
        ("03", "Signal Analysis", "Frequency-domain damage signature"),
        ("04", "Quantum ML", "Fidelity-kernel SVM classifier"),
        ("05", "Prediction", "Damage progression + RUL"),
        ("06", "Healing Optimizer", "QAOA-style action search"),
        ("07", "Autonomous Loop", "Detect → decide → heal → verify"),
    ]
    cols = st.columns(7)
    for col, (num, title, desc) in zip(cols, cards):
        col.markdown(f'<div class="card"><div class="card-kicker">{num}</div><div class="card-title">{title}</div><div class="card-desc">{desc}</div></div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1 VQE
# -----------------------------------------------------------------------------
elif st.session_state.page == "Material Chemistry":
    st.markdown('<div class="section-title">01 · Self-Healing CFRP & Material Chemistry</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Tune the toy material landscape. The lower-energy region is treated as the better candidate in this educational simulation.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    theta_bias = c1.slider("θ search bias", 0.0, 6.28, 3.14, .05)
    phi_bias = c2.slider("φ search bias", 0.0, 6.28, 3.14, .05)
    coupling = c3.slider("Coupling strength", 0.0, 1.0, .35, .01)
    grid = np.linspace(0, 2*np.pi, 90)
    vals = np.array([[-0.9*np.cos(t) - .55*np.cos(p) + coupling*np.cos(t-p) for p in grid] for t in grid])
    idx = np.unravel_index(np.argmin(np.abs(vals - (vals.mean() + .2*(np.cos(theta_bias)+np.sin(phi_bias))))), vals.shape)
    best_energy, best_t, best_p = run_vqe(steps=70)
    metric_row([
        ("Global toy minimum", f"{best_energy:.3f}", None),
        ("Selected θ", f"{grid[idx[0]]:.2f}", None),
        ("Selected φ", f"{grid[idx[1]]:.2f}", None),
    ])
    fig = go.Figure(go.Heatmap(z=vals, x=grid, y=grid, colorscale="Viridis"))
    fig.add_trace(go.Scatter(x=[grid[idx[1]]], y=[grid[idx[0]]], mode="markers", marker=dict(size=12, color="white", symbol="x"), name="Selected point"))
    fig.update_layout(title="Interactive toy variational energy landscape", xaxis_title="φ", yaxis_title="θ")
    st.plotly_chart(dark_fig(fig, 540), use_container_width=True)
    st.markdown('<div class="warning">Concept only: this is not a validated molecular Hamiltonian or a physical self-healing CFRP chemistry model.</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2 Sensing
# -----------------------------------------------------------------------------
elif st.session_state.page == "Quantum Sensing":
    st.markdown('<div class="section-title">02 · Structural Health Monitoring</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Adjust sensor conditions and observe how the simulated quantum measurement distribution changes.</div>', unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        condition = c1.selectbox("Baseline damage class", CLASSES, index=1)
        load = c2.slider("Load factor", 0, 100, 50, key="sense_load")
        shots = c3.slider("Measurement shots", 64, 2048, 512, 64)
    row = df[df.damage == condition].iloc[0].copy()
    row["load"] = load
    score, counts, probs = quantum_sensing_score(row[features].to_numpy(float), shots=shots, seed=seed)
    metric_row([
        ("Anomaly score", f"{score:.3f}", None),
        ("Shots", str(shots), None),
        ("State |00⟩ probability", f"{probs[0]:.3f}", None),
    ])
    st.markdown('<div class="section-title">Watch the damage get sensed</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Load builds up, the damage grows, acoustic waves spread out and each sensor lights up when the wave reaches it. Change the damage class, load or shots above to see a different outcome.</div>', unsafe_allow_html=True)
    components.html(sensing_html(condition, load, shots), height=500)
    fig = go.Figure(go.Bar(x=["00", "01", "10", "11"], y=probs, text=np.round(probs, 3), textposition="auto"))
    fig.update_layout(title=f"Measurement distribution · {condition}", yaxis_title="Probability")
    st.plotly_chart(dark_fig(fig, 450), use_container_width=True)

# -----------------------------------------------------------------------------
# 3 Signal / QFT
# -----------------------------------------------------------------------------
elif st.session_state.page == "Signal Analysis":
    st.markdown('<div class="section-title">03 · Damage Signal Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Change frequency, amplitude and noise to see the time-domain waveform and frequency-domain signature update together.</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    base_freq = c1.slider("Base frequency", 8, 40, 18, 1)
    damage_freq = c2.slider("Damage frequency", 35, 120, 72, 1)
    signal_amp = c3.slider("Damage amplitude", 0.0, 5.0, 1.8, .1)
    noise = c4.slider("Noise level", 0.0, 2.0, .65, .05)
    n = 512
    t = np.linspace(0, 1, n)
    rng = np.random.default_rng(seed)
    signal = 2.5*np.sin(2*np.pi*base_freq*t) + 1.1*np.sin(2*np.pi*(base_freq+16)*t) + signal_amp*np.sin(2*np.pi*damage_freq*t) + rng.normal(0, noise, n)
    score, spectrum = signal_damage_score(signal)
    metric_row([("Signal damage score", f"{score:.3f}", None), ("Dominant damage freq", f"{damage_freq} Hz", None), ("Noise", f"{noise:.2f}", None)])
    st.markdown('<div class="section-title">Watch the signal get detected</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">A healthy vibration signal streams in. At 3.5 s a damage burst appears; the live spectrum shows the new peak and the detector flags it once it crosses the adaptive threshold.</div>', unsafe_allow_html=True)
    components.html(signal_html(base_freq, damage_freq, signal_amp, noise), height=500)
    a, b = st.columns(2)
    with a:
        fig = go.Figure(go.Scatter(x=t, y=signal, mode="lines"))
        fig.update_layout(title="Live noisy CFRP sensor waveform", xaxis_title="Time", yaxis_title="Amplitude")
        st.plotly_chart(dark_fig(fig, 440), use_container_width=True)
    with b:
        freqs = np.fft.rfftfreq(n, d=1/n)
        mag = np.abs(np.fft.rfft(signal)) / np.sqrt(n)
        fig = go.Figure(go.Scatter(x=freqs, y=mag, mode="lines", fill="tozeroy"))
        fig.update_layout(title="QFT / FFT frequency-domain view", xaxis_title="Frequency (Hz)", yaxis_title="Magnitude")
        st.plotly_chart(dark_fig(fig, 440), use_container_width=True)
    st.markdown('<div class="status">Tip: increase damage amplitude or move the damage frequency away from the healthy peaks to make the spectral signature more obvious.</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4 Quantum ML
# -----------------------------------------------------------------------------
elif st.session_state.page == "Quantum ML":
    st.markdown('<div class="section-title">04 · Damage Detection & Classification</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Tune the training/test split and feature scaling. The fidelity kernel and SVM are recomputed when the controls change.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    test_size = c1.slider("Test set", .15, .40, .25, .05)
    C = c2.slider("SVM C", .1, 5.0, 1.0, .1)
    sample_limit = c3.slider("Samples per class", 50, 200, 120, 10)
    work = df.groupby("damage", group_keys=False).head(sample_limit).copy()
    X = work[features].to_numpy(float)
    y = work.damage.to_numpy()
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size, random_state=seed, stratify=y)
    Ktr = fidelity_kernel(Xtr)
    Kte = fidelity_kernel(Xte, Xtr)
    clf = SVC(kernel="precomputed", probability=True, C=C, random_state=seed).fit(Ktr, ytr)
    pred = clf.predict(Kte)
    acc = accuracy_score(yte, pred)
    cm = confusion_matrix(yte, pred, labels=CLASSES)
    metric_row([("Fidelity-kernel accuracy", f"{acc*100:.1f}%", None), ("Training samples", str(len(ytr)), None), ("Test samples", str(len(yte)), None)])
    st.markdown('<div class="section-title">Polymer breakage simulation</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">A lattice of carbon fibres (cyan) and polymer chains (purple) is pulled until bonds snap. Each damage class breaks differently - this is the physical origin of the sensor features the classifier learns from. Switch class with the buttons inside the widget.</div>', unsafe_allow_html=True)
    start_cls = st.selectbox("Initial damage mode", CLASSES, index=3, key="break_cls")
    components.html(breakage_html(start_cls), height=510)

    g1, g2 = st.columns(2)
    with g1:
        fig = go.Figure(go.Heatmap(z=cm, x=CLASSES, y=CLASSES, colorscale="Viridis", text=cm, texttemplate="%{text}"))
        fig.update_layout(title="Live quantum-kernel SVM confusion matrix", xaxis_title="Predicted", yaxis_title="Actual")
        st.plotly_chart(dark_fig(fig, 420), use_container_width=True)
    with g2:
        per_class = [float((pred[yte == c] == c).mean()) if (yte == c).any() else 0.0 for c in CLASSES]
        fig = go.Figure(go.Bar(x=CLASSES, y=per_class, text=[f"{v*100:.0f}%" for v in per_class], textposition="auto", marker_color=["#5ee7a5", "#5ca7ff", "#9b7cff", "#ff6b6b"]))
        fig.update_layout(title="Per-class detection accuracy", yaxis_title="Recall", yaxis_range=[0, 1.05])
        st.plotly_chart(dark_fig(fig, 420), use_container_width=True)

    g3, g4 = st.columns(2)
    with g3:
        ok = pred == yte
        fig = go.Figure()
        palette = {"Healthy": "#5ee7a5", "Matrix Crack": "#5ca7ff", "Delamination": "#9b7cff", "Fibre Break": "#ff6b6b"}
        for c in CLASSES:
            m = (yte == c) & ok
            fig.add_trace(go.Scatter(x=Xte[m, 5], y=Xte[m, 4], mode="markers", name=c, marker=dict(color=palette[c], size=8, opacity=.8)))
        if (~ok).any():
            fig.add_trace(go.Scatter(x=Xte[~ok, 5], y=Xte[~ok, 4], mode="markers", name="Misclassified", marker=dict(color="white", size=11, symbol="x", line=dict(width=2))))
        fig.update_layout(title="Test samples: acoustic energy vs resistance change", xaxis_title="Acoustic energy", yaxis_title="Resistance change")
        st.plotly_chart(dark_fig(fig, 420), use_container_width=True)
    with g4:
        eps = np.linspace(0, 8, 160)
        def curve(c):
            if c == "Healthy":
                return np.minimum(eps, 5) * 20
            if c == "Matrix Crack":
                return np.where(eps < 2.4, eps * 28, 67 + (eps - 2.4) * 6)
            if c == "Delamination":
                return np.where(eps < 3.2, eps * 22, np.where(eps < 4.2, 70 - (eps - 3.2) * 28, 42 + (eps - 4.2) * 3))
            return np.where(eps < 6.0, eps * 17, np.maximum(8, 102 - (eps - 6.0) * 260))
        fig = go.Figure()
        for c in CLASSES:
            fig.add_trace(go.Scatter(x=eps, y=curve(c), mode="lines", name=c, line=dict(color=palette[c], width=3)))
        fig.update_layout(title="Idealised stress-strain signature per damage class", xaxis_title="Strain (%)", yaxis_title="Stress (a.u.)")
        st.plotly_chart(dark_fig(fig, 420), use_container_width=True)

# -----------------------------------------------------------------------------
# 5 Prediction
# -----------------------------------------------------------------------------
elif st.session_state.page == "Prediction":
    st.markdown('<div class="section-title">05 · Damage Prediction & Remaining Life</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Adjust the monitoring horizon and growth rate. The forecast curve updates instantly.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    condition = c1.selectbox("Current condition", CLASSES, index=1)
    horizon = c2.slider("Forecast steps", 1, 24, 8)
    growth = c3.slider("Damage growth / step", .01, .12, .035, .005)
    X = df[features].to_numpy(float)
    severity = df.damage.map({"Healthy": .05, "Matrix Crack": .30, "Delamination": .65, "Fibre Break": .95}).to_numpy()
    model = RandomForestRegressor(n_estimators=120, random_state=seed).fit(X, severity)
    row = df[df.damage == condition].iloc[0]
    current = float(model.predict([row[features].to_numpy(float)])[0])
    x = np.arange(horizon + 1)
    future = np.clip(current + growth*x + .01*(x**1.35), 0, 1)
    rul = int(max(1, round((1-future[-1])*100)))
    metric_row([("Current damage", f"{current:.2f}", None), ("Projected damage", f"{future[-1]:.2f}", None), ("Relative RUL", f"{rul}%", None)])
    fig = go.Figure(go.Scatter(x=x, y=future, mode="lines+markers", name="Projected"))
    fig.add_hline(y=.7, line_dash="dash", annotation_text="Inspection threshold")
    fig.update_layout(title="Interactive damage progression forecast", xaxis_title="Future monitoring step", yaxis_title="Damage index", yaxis_range=[0, 1])
    st.plotly_chart(dark_fig(fig, 450), use_container_width=True)
    st.markdown('<div class="warning">RUL is an illustrative software estimate. It is not a certified structural-life prediction.</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6 QAOA
# -----------------------------------------------------------------------------
elif st.session_state.page == "Healing Optimizer":
    st.markdown('<div class="section-title">06 · Healing Strategy Optimization</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Change the importance of risk reduction, treatment cost and compatibility. The recommended action set changes with the sliders.</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Thermal self-healing simulator</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Drag the temperature slider inside the simulator (or press Auto-heat). Below the activation temperature the polymer chains are frozen; as the temperature rises, the chains move, reversible bonds reform across the crack and the damage closes. Too hot and the polymer degrades.</div>', unsafe_allow_html=True)
    h1, h2, h3 = st.columns(3)
    t_onset = h1.slider("Healing activation temperature (°C)", 40, 120, 60, 5)
    ea_kj = h2.slider("Activation energy (kJ/mol)", 40, 140, 80, 5)
    t_hold = h3.slider("Reference hold temperature (°C)", 40, 180, 120, 5)
    components.html(healing_html(t_onset, ea_kj, 25), height=510)
    t90 = time_to(t_hold, .9, t_onset, ea_kj)
    metric_row([
        ("Healing capacity at hold T", f"{float(h_eq(t_hold, t_onset))*100:.0f}%", None),
        ("Rate constant", f"{float(rate(t_hold, ea_kj)):.3f} /min", None),
        ("Time to 90% healed", "not reachable" if not np.isfinite(t90) else f"{t90:.0f} min", None),
    ])
    fig = go.Figure()
    for tt in [60, 80, 100, 120, 150, 180]:
        tx, hy = healing_curve(tt, 60, t_onset, ea_kj)
        fig.add_trace(go.Scatter(x=tx, y=hy * 100, mode="lines", name=f"{tt} °C", line=dict(width=3)))
    fig.update_layout(title="Healing vs time at different temperatures", xaxis_title="Time (min)", yaxis_title="Healed (%)", yaxis_range=[0, 100])
    st.plotly_chart(dark_fig(fig, 380), use_container_width=True)
    st.markdown('<div class="warning">Illustrative toy kinetics (sigmoid capacity + Arrhenius rate). Not a validated polymer-chemistry model.</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">QAOA-style healing strategy</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    risk_weight = c1.slider("Risk reduction weight", .5, 3.0, 1.4, .1)
    cost_weight = c2.slider("Treatment cost weight", .1, 2.0, 1.0, .1)
    conflict_weight = c3.slider("Action conflict penalty", 0.0, 1.5, .35, .05)
    actions = [("Resin infusion", 0.85, 0.70), ("Patch reinforcement", .65, .55), ("Heat-cure cycle", .45, .40)]
    rows = []
    for mask in range(8):
        selected = [actions[i] for i in range(3) if mask & (1 << i)]
        risk = sum(a[1] for a in selected)
        cost = sum(a[2] for a in selected)
        conflict = conflict_weight if (mask & 1) and (mask & 4) else 0
        objective = risk_weight*risk - cost_weight*cost - conflict
        rows.append((mask, selected, objective, risk, cost))
    rows.sort(key=lambda r: r[2], reverse=True)
    best = rows[0]
    metric_row([("Best objective", f"{best[2]:.3f}", None), ("Risk reduction", f"{best[3]:.2f}", None), ("Treatment cost", f"{best[4]:.2f}", None)])
    table = pd.DataFrame([
        {"State": format(mask, "03b"), "Actions": ", ".join(a[0] for a in selected) or "Monitor", "Risk reduction": round(risk, 2), "Cost": round(cost, 2), "Objective": round(obj, 3)}
        for mask, selected, obj, risk, cost in rows
    ])
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.success("Recommended strategy: " + (", ".join(a[0] for a in best[1]) or "Continue monitoring"))

# -----------------------------------------------------------------------------
# 7 Autonomous
# -----------------------------------------------------------------------------
else:
    st.markdown('<div class="section-title">07 · Autonomous Self-Healing Loop</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">This page connects sensing, classification, signal analysis, optimization and verification into one simulated control loop.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    condition = c1.selectbox("Incoming condition", CLASSES, index=2)
    load = c2.slider("Incoming load", 0, 100, 65)
    healing_eff = c3.slider("Healing effectiveness", 0, 100, 70)
    row = df[df.damage == condition].iloc[0].copy()
    row["load"] = load
    x = row[features].to_numpy(float)
    state = quantum_state(x)
    prototypes = {label: quantum_state(df[df.damage == label][features].mean().to_numpy(float)) for label in CLASSES}
    scores = {label: fidelity(state, s) for label, s in prototypes.items()}
    detected = max(scores, key=scores.get)
    confidence = scores[detected]
    sig_t, sig = synthetic_signal(condition, seed=seed)
    signal_score, _ = signal_damage_score(sig)
    actions = qaoa_healing_options()
    action = ", ".join(a[0] for a in actions[0][1]) if detected != "Healthy" else "Continue monitoring"
    verified = (confidence > .70 and signal_score >= .10) if detected != "Healthy" else confidence > .70
    initial_damage = float(np.clip(.18*load/100 + .30*(1-confidence) + .35*signal_score + .17*(1 if detected != "Healthy" else 0), 0, 1))
    final_damage = max(0, initial_damage*(1-healing_eff/100))
    steps = ["Sensor", "Detect", "Decide", "Heal", "Verify"]
    vals = [0.15 + .65*confidence, confidence, max(confidence, .75), max(confidence, .75), 1-final_damage]
    fig = go.Figure(go.Bar(x=steps, y=vals, text=[f"{v:.2f}" for v in vals], textposition="auto"))
    fig.update_layout(title="Closed-loop confidence / health trace", yaxis_title="Normalized score", yaxis_range=[0, 1])
    metric_row([("Detected class", detected, None), ("Quantum confidence", f"{confidence:.2f}", None), ("Signal score", f"{signal_score:.2f}", None), ("Verification", "PASS" if verified else "REVIEW", None)])
    st.plotly_chart(dark_fig(fig, 410), use_container_width=True)
    a, b = st.columns(2)
    with a:
        st.markdown('<div class="status">DETECT → DECIDE → HEAL → VERIFY</div>', unsafe_allow_html=True)
        st.write(f"**Recommended action:** {action}")
    with b:
        st.metric("Simulated post-healing damage", f"{final_damage:.2f}", f"-{(initial_damage-final_damage)*100:.0f}%")
    st.caption("Autonomous actuation is represented only as a software decision. Real CFRP systems require certified sensing, safety interlocks and validated repair processes.")

# Footer
st.markdown("---")
st.caption("Q-CFRP Guardian • educational quantum-inspired CFRP prototype • NumPy simulation • no claim of quantum advantage or physical self-healing")
