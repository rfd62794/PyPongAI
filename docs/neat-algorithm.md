# NEAT Algorithm

Understanding NeuroEvolution of Augmenting Topologies in PyPongAI.

## What is NEAT?

**NEAT (NeuroEvolution of Augmenting Topologies)** is a genetic algorithm that evolves both the weights **and structure** of neural networks. Unlike traditional neural networks with fixed architectures, NEAT starts with minimal networks and gradually adds complexity.

### Key Advantages

1. **Topology Evolution**: Networks grow from simple to complex
2. **No Manual Architecture Design**: Structure emerges automatically
3. **Competitive with Backpropagation**: Works well for reinforcement learning
4. **Innovation Protection**: New structures get time to optimize before competing

## How NEAT Works

### 1. Initialization

Start with a minimal network:
- **Inputs (8)**: Game state information
- **Outputs (3)**: Action decisions (UP, DOWN, STAY)
- **Hidden Nodes (1)**: Initial starting point
- **Connections**: Fully connected input-to-output

```
Input Layer (8)  →  Hidden (1)  →  Output Layer (3)
  paddle_y            [node]          UP
  ball_x                              DOWN
  ball_y                              STAY
  ball_vel_x
  ball_vel_y
  relative_y
  incoming
  opponent_y
```

### 2. Evaluation (Fitness)

Each genome (network) plays Pong and receives a fitness score:

**Basic Fitness:**
```python
fitness = 0
fitness += 0.1 * frames_survived
fitness += 10 * points_scored
fitness -= 5 * points_lost
fitness += 1 * paddle_hits
```

**Competitive Fitness (ELO):**
```python
fitness = elo_rating + (0.1 * novelty_score)
```

### 3. Selection

- Top 20% of genomes survive (elitism)
- Survivors produce offspring
- Worst performers are eliminated

### 4. Reproduction

#### Mutation (Common)
Random changes to existing genomes:

**Weight Mutation** (80% chance):
```python
weight += random.gauss(0, mutation_power)
weight = clamp(weight, -30, 30)
```

**Add Connection** (50% chance):
```python
# Connect two previously unconnected nodes
add_edge(node_a, node_b, random_weight())
```

**Add Node** (20% chance):
```python
# Split existing connection
old_connection = node_a → node_b
new_connection = node_a → new_node → node_b
```

**Remove Connection** (50% chance):
```python
# Delete random connection
remove_edge(node_a, node_b)
```

#### Crossover (Rare)
Combine two parent networks:
```python
child = align_and_merge(parent1, parent2)
# Matching genes: randomly chosen from either parent
# Disjoint genes: inherited from fitter parent
```

### 5. Speciation

Networks are grouped into species based on similarity:

```python
def distance(genome1, genome2):
    # Count mismatched connections
    disjoint = count_disjoint_genes(genome1, genome2)
    # Compare matching connection weights
    weight_diff = avg_weight_difference(genome1, genome2)
    
    return (disjoint * c1) + (weight_diff * c2)

if distance(genome, species_rep) < threshold:
    add_to_species(genome, species)
```

**Why Speciation?**
- Protects innovation: New structures compete within species first
- Maintains diversity: Prevents single strategy domination
- Enables exploration: Different species explore different strategies

## PyPongAI Configuration

### Network Architecture (`neat_config.txt`)

```ini
[DefaultGenome]
# Start simple, evolve complexity
num_hidden = 1
num_inputs = 8
num_outputs = 3

# Enable recurrent connections (memory)
feed_forward = False

# Activation functions
activation_options = sigmoid tanh relu

# Mutation rates (per genome per generation)
weight_mutate_rate = 0.8      # 80% chance to mutate weights
bias_mutate_rate = 0.7        # 70% chance to mutate biases
conn_add_prob = 0.5           # 50% chance to add connection
conn_delete_prob = 0.5        # 50% chance to delete connection
node_add_prob = 0.2           # 20% chance to add node
node_delete_prob = 0.2        # 20% chance to delete node
```

### Population Settings

```ini
[NEAT]
pop_size = 50                 # 50 competing genomes
fitness_criterion = max       # Maximize fitness
reset_on_extinction = False   # Don't restart if all species die

[DefaultStagnation]
max_stagnation = 20           # Remove species after 20 gens without improvement
species_elitism = 2           # Keep top 2 genomes per species
```

## Evolution Timeline

### Generation 0-10: Bootstrap Phase
- Networks learn basic paddle control
- Connections strengthen or weaken
- Poor performers eliminated
- Fitness: ~100-500

### Generation 10-25: Structure Emerges
- Hidden nodes added
- Recurrent connections form
- Species diversify
- Fitness: ~500-1000

### Generation 25-50: Strategy Development
- Complex behaviors emerge
- Networks anticipate ball trajectory
- Competitive strategies evolve
- Fitness: ~1000-1500

### Generation 50+: Refinement
- Fine-tuning of weights
- Stability vs exploration balance
- Occasional breakthroughs
- Fitness: ~1500-2000+

## Recurrent Networks (RNNs)

PyPongAI uses **recurrent connections** for temporal memory:

```python
# Standard feedforward
output = activate(input)

# Recurrent network
output = activate(input + previous_state)
network_state = update_state(output)
```

**Benefits:**
- Remember ball trajectory
- Predict future positions
- Learn temporal patterns
- More human-like anticipation

**Implementation:**
```python
net = neat.nn.RecurrentNetwork.create(genome, config)
net.reset()  # Clear memory at game start

for frame in game:
    output = net.activate(inputs)  # State automatically maintained
```

## Novelty Search Integration

NEAT alone can converge to local optima. **Novelty search** encourages exploration:

### Behavioral Characteristic (BC)
```python
# Average Y-coordinate of paddle-ball contacts
bc = mean([contact.y for contact in match_contacts])
```

### Novelty Score
```python
# Distance to k-nearest neighbors in archive
novelty = mean([distance(bc, neighbor) for neighbor in k_nearest])
```

### Combined Fitness
```python
final_fitness = elo_rating + (0.1 * novelty_score)
```

**Effect:**
- Rewards unique strategies
- Prevents premature convergence
- Maintains population diversity
- Discovers unexpected solutions

## Genetic Encoding

NEAT uses **innovation numbers** to track gene history:

```python
Genome {
    nodes: {
        0: InputNode(y=0),
        1: InputNode(y=1),
        ...
        8: OutputNode(action=UP),
        9: OutputNode(action=DOWN),
        10: OutputNode(action=STAY),
        11: HiddenNode(activation=tanh),
        ...
    },
    connections: {
        (0, 11): Connection(weight=0.5, enabled=True, innovation=1),
        (1, 11): Connection(weight=-0.3, enabled=True, innovation=2),
        (11, 8): Connection(weight=1.2, enabled=True, innovation=15),
        ...
    }
}
```

Innovation numbers enable:
- Accurate crossover (align matching genes)
- Speciation distance calculation
- Historical tracking

## Performance Optimization

### Parallel Evaluation
```python
# Evaluate multiple genomes simultaneously
with ProcessPoolExecutor() as executor:
    futures = [executor.submit(evaluate, g) for g in genomes]
    results = [f.result() for f in futures]
```

### Headless Simulation
```python
# 10-100x faster than visual mode
game = GameSimulator()  # No Pygame overhead
while not done:
    state = game.update(left_move, right_move)
```

### Early Termination
```python
# Stop poor performers early
if fitness < threshold and frames > min_frames:
    terminate_evaluation()
```

## Common Questions

### Q: Why does fitness sometimes decrease?

**A:** NEAT uses elitism (top genomes always survive), but the *average* population fitness can decrease as new mutations are explored. This is healthy exploration.

### Q: How long does training take?

**A:** ~1 second per generation on modern hardware. 50 generations = ~1 minute. 100 generations = ~2 minutes.

### Q: Can I use backpropagation instead?

**A:** NEAT is preferred for reinforcement learning where:
- No labeled training data exists
- Architecture is unknown
- Exploration is needed

### Q: What if all species go extinct?

**A:** Set `reset_on_extinction = True` to restart with a new population. Or lower `max_stagnation` to give species more time.

### Q: How do I prevent overfitting?

**A:** Use competitive training, Hall of Fame, and validation against rule-based AI. These provide diverse opponents.

## Further Reading

- [NEAT Paper (Stanley & Miikkulainen, 2002)](http://nn.cs.utexas.edu/downloads/papers/stanley.ec02.pdf)
- [NEAT-Python Documentation](https://neat-python.readthedocs.io/)
- [Recurrent Networks in NEAT](https://citeseerx.ist.psu.edu/document?repid=rep1&type=pdf&doi=8c5d1e8a0cc8c05ffc0c5f46c3c0f5a3fcf2c5e8)
- [PyPongAI Training Guide](training-guide.md)
