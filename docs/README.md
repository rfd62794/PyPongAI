# PyPongAI Documentation

Welcome to the comprehensive documentation for **PyPongAI**, an advanced neuroevolution research platform for training AI agents to play Pong using NEAT (NeuroEvolution of Augmenting Topologies).

## 📚 Documentation Structure

### Getting Started
- **[Quick Start Guide](quick-start.md)** - Get up and running in 5 minutes
- **[Installation](installation.md)** - Detailed installation instructions and requirements
- **[Configuration](configuration.md)** - Understanding and customizing settings

### Core Concepts
- **[Architecture Overview](architecture.md)** - High-level system design and components
- **[NEAT Algorithm](neat-algorithm.md)** - Understanding neuroevolution and NEAT
- **[Training Pipeline](training-pipeline.md)** - How AI agents are trained
- **[State Management](state-management.md)** - UI state system architecture

### Training & Evaluation
- **[Training Guide](training-guide.md)** - Complete training workflow
- **[Competitive Training](competitive-training.md)** - ELO-based matchmaking system
- **[Novelty Search](novelty-search.md)** - Behavioral diversity and exploration
- **[Curriculum Learning](curriculum-learning.md)** - Progressive difficulty training

### Features
- **[Match Recording](match-recording.md)** - Recording and replaying matches
- **[Analytics System](analytics.md)** - Performance metrics and visualization
- **[League System](league-system.md)** - Tournament and tier management
- **[Human vs AI](human-play.md)** - Playing against trained agents

### API Reference
- **[AI Module](api/ai-module.md)** - Core training functions
- **[Game Engine](api/game-engine.md)** - Visual game implementation
- **[Game Simulator](api/game-simulator.md)** - Headless training simulator
- **[Configuration API](api/config.md)** - Configuration constants

### Advanced Topics
- **[RNN Implementation](advanced/rnn.md)** - Recurrent networks for temporal reasoning
- **[ELO System](advanced/elo.md)** - Rating calculation and matchmaking
- **[Performance Optimization](advanced/performance.md)** - Training speed optimization
- **[Extending the System](advanced/extending.md)** - Adding new features

### Reference
- **[File Structure](reference/file-structure.md)** - Project organization
- **[Data Formats](reference/data-formats.md)** - JSON schemas and data structures
- **[Testing Guide](reference/testing.md)** - Running and writing tests
- **[Troubleshooting](reference/troubleshooting.md)** - Common issues and solutions

## 🎯 Project Overview

PyPongAI is a production-ready research platform that combines:
- **Recurrent Neural Networks** for temporal memory
- **ELO-based competitive training** for stable skill assessment
- **Novelty search** for behavioral diversity
- **Curriculum learning** for progressive difficulty
- **Comprehensive analytics** for research insights

## 🚀 Quick Navigation

**New to the project?** Start with the [Quick Start Guide](quick-start.md)

**Want to train your first AI?** See the [Training Guide](training-guide.md)

**Interested in the algorithms?** Check out [NEAT Algorithm](neat-algorithm.md) and [Novelty Search](novelty-search.md)

**Need API details?** Browse the [API Reference](api/) section

**Having issues?** Check [Troubleshooting](reference/troubleshooting.md)

## 📊 Project Status

**Production Ready** - Successfully trained for 50+ generations
- Best fitness achieved: 1876
- Stable evolution with 2 species
- ~1 second per generation training speed
- 41 unit tests covering core functionality

## 🤝 Contributing

See the root repository for contribution guidelines. All documentation follows Markdown best practices and should be clear, concise, and example-driven.

## 📝 Legacy Documentation

The following legacy documents are preserved for reference:
- [System Analysis](system_analysis.md) - Historical system analysis
- [Training (Legacy)](training.md) - Original training documentation

For current documentation, refer to the structured guides above.
