# Q-CFRP Guardian — Interactive 7-in-1 Dashboard

An upgraded Streamlit prototype for quantum-inspired / simulated-quantum CFRP structural-health monitoring.

## What was improved

- Polished dark glass-style dashboard UI
- Redesigned left navigation with active-page state
- Smooth page switching using Streamlit session state
- Live sliders and selectors throughout the application
- Graphs recalculate from slider values instead of being static
- Interactive command-center controls for load, frequency, amplitude, resistance, energy, temperature, sensor noise and healing effectiveness
- Interactive VQE-style material-energy landscape
- Quantum sensing shot control
- QFT/FFT signal controls for frequency, amplitude and noise
- Quantum-kernel SVM controls for test split, SVM C and sample size
- Damage prediction controls for horizon and damage growth
- QAOA-style healing optimizer with adjustable risk/cost/conflict weights
- Autonomous Detect → Decide → Heal → Verify simulation
- Responsive Plotly charts and metric cards

## New in this version: live animations

- **02 Structural Monitoring** - a CFRP panel is loaded, the damage grows, acoustic waves spread and each sensor lights up when the wave arrives. Sensor traces, detection threshold, damage-level meter and localisation marker. Responds to damage class, load and shots.
- **03 Signal Analysis** - a live scrolling waveform with a damage burst at 3.5 s, a live FFT spectrum and an adaptive-threshold detector that flags the damage frequency. Responds to the frequency / amplitude / noise sliders.
- **04 Damage Classification** - polymer-network breakage simulation (carbon fibres + polymer chains pulled until bonds snap) for all four damage classes, with live stress-strain and acoustic-emission graphs, plus new Plotly graphs (per-class accuracy, feature scatter with misclassified points, stress-strain signatures).
- **06 Healing Optimizer** - thermal self-healing simulator: raise the temperature (slider or Auto-heat) and the crack closes as reversible bonds reform; shows healing vs time, capacity vs temperature and a degradation warning above 190 C. Python-side healing curves use the same model (`src/healing_model.py`).

The animations live in `src/animations.py` (plain HTML5 canvas, no extra dependencies, work offline).

## Seven modules

1. Self-Healing CFRP & Material Chemistry — VQE-style material screening
2. Structural Health Monitoring — simulated quantum sensing
3. Damage Signal Analysis — QFT/FFT frequency-domain analysis
4. Damage Detection & Classification — fidelity quantum kernel + SVM
5. Damage Prediction — progression + illustrative relative RUL
6. Healing Strategy Optimization — QAOA-style discrete search
7. Autonomous Self-Healing — simulated closed-loop decision support

## Run locally

```bash
python -m venv .venv
```

Windows:

```bash
.venv\\Scripts\\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start:

```bash
streamlit run app.py
```

## Important scope

This is an educational software simulation. The quantum circuits/state operations are simulated with NumPy and the CFRP damage/healing values are illustrative. It does not physically repair CFRP, does not claim quantum advantage, and should not be used as a certified structural-life or repair system.
