# PyPongAI: Neuroevolution Research Platform

## The Concept
Evolution discovered how to play Pong—without hand-coded rules.

### What It Does
Watch as a neural network evolves from random button-pressing to perfect ball-tracking, all through competitive selection and behavioral diversity.

---

## The Story: Three Key Insights

### 1. The Gap Between Random & Trained
- **Generation 0**: 0% win rate, random paddle movement.
- **Generation 50**: 98% win rate, perfect predictive tracking.
*Leverage the Comparison View in-app to see this evolution side-by-side.*

### 2. Dual Architecture: Speed vs Interpretability
- **Headless Simulator**: Optimized for 500x faster-than-real-time training.
- **Visual Pong**: Proof it actually works via high-fidelity verification and human matches.

### 3. Novelty Search: Evolution's Creativity Engine
- **Pure ELO**: All agents often converge to a single "safe" strategy.
- **ELO + Novelty**: Population maintains diversity, enabling agents to discover non-obvious, superior solutions by rewarding unique behaviors.

---

## Technical Highlights

### NEAT (NeuroEvolution of Augmenting Topologies)
PyPongAI uses NEAT to evolve both the weights and the topology of neural networks, starting from minimal complexity and complexifying only as needed to achieve higher fitness.

### RNNs for Temporal Memory
The inclusion of Recurrent Neural Networks (RNNs) allows agents to maintain a "memory" of ball velocity and previous states, which is critical for trajectory prediction.

### ELO-Based Competitive Training
Agents are ranked using a standard ELO system, ensuring that fitness isn't just a static score but a reflection of the agent's performance relative to the evolving population.

### League System & Gamification
Models are automatically categorized into ELO-based tiers (Bronze, Silver, Gold, Platinum), providing a clear progression path for the neuroevolution process.

---

## Quick Start

### Installation
```bash
git clone https://github.com/rfd62794/PyPongAI.git
cd PyPongAI
pip install pygame neat-python numpy
```

### Training (Research Mode)
```bash
python train.py --mode research --generations 50 --visual
```

### Playing Against a Trained AI
```bash
python play.py --model data/models/best_genome.pkl
```

### Comparing Gen 0 vs Gen 50
1. Run training to generate recordings.
2. Launch the app: `python main.py`
3. Navigate to **Analytics** -> **Compare**.

---

## Architecture

[Consult docs/architecture.md for a deep dive into the system components.]

---

## For Devlog Content Creators

### Recommended Shots
1. **Gen 0 Gameplay**: Random AI failing hilariously.
2. **Gen 30 Gameplay**: The AI starts to "get it."
3. **Gen 50 Gameplay**: Professional-level tracking.
4. **Training Logs**: Use the research mode output (ELO + Novelty metrics) to show real-time "learning."
5. **Comparison View**: Side-by-side Gen 0 vs Gen 50 playback.
6. **AI vs Human**: Proof of concept match.

---

## Research Value

This platform demonstrates:
- ✅ **Neuroevolution Fundamentals**: Implementation of NEAT in a dynamic environment.
- ✅ **Advanced RL Techniques**: RNNs, Novelty Search, and Curriculum Learning.
- ✅ **Production-Grade System Design**: High-performance dual-architecture simulator.

---

## Documentation

- **SDD** (docs/architecture.md): System design and component breakdown.
- **Devlog Guide** (DEVLOG_NARRATIVE.md): Full narrative arc for video content.
- **Training Guide** (docs/training-guide.md): How to run and configure experiments.

---

## License
MIT (Commercial use permitted; attribution required)

## Author
Robert (rfd62794)
