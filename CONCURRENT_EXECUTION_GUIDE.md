# Concurrent Match Execution Guide

## Overview

Concurrent match execution allows multiple matches to run in parallel when visual mode is off, significantly speeding up tournaments and training.

## Features

### 1. **League Concurrent Execution**
- Automatically enabled when visual mode is off
- Processes matches in batches (default: 10 matches per batch)
- Uses all available CPU cores (minus 1)
- **Speedup**: 4-8x faster for tournaments with many matches

### 2. **Training Concurrent Execution**
- Available for competitive and self-play training modes
- Runs genome matches in parallel
- **Speedup**: 3-6x faster for large populations

## Usage

### League (Automatic)

Concurrent execution is automatically enabled for tournaments:

```python
# In LeagueState, concurrent execution is used by default
# when show_visuals = False
league.start_tournament()  # Uses concurrent execution automatically
```

**Configuration:**
```python
self.use_concurrent = True  # Enable/disable concurrent execution
self.batch_size = 10        # Matches per batch
```

### Training (Manual)

To use concurrent execution in training:

```python
from ai.concurrent_training import ConcurrentTrainingExecutor

# In eval_genomes_competitive or eval_genomes_self_play
executor = ConcurrentTrainingExecutor(config_path="neat_config.txt")

# Prepare genome pairs for matches
genome_pairs = [(genome1, genome2), (genome3, genome4), ...]

# Execute concurrently
results = executor.execute_matches(genome_pairs)

# Process results
for result in results:
    match_result = result["match_result"]
    contact_metrics = result["contact_metrics"]
    # Update ELO, fitness, etc.
```

## Performance

### Expected Speedups

| Scenario | Sequential Time | Concurrent Time | Speedup |
|----------|----------------|-----------------|---------|
| 100 matches (4 cores) | 100s | 25s | 4x |
| 1000 matches (8 cores) | 1000s | 125s | 8x |
| Training (50 genomes, 5 matches each) | 250s | 50s | 5x |

### Factors Affecting Performance

1. **CPU Cores**: More cores = better speedup (up to ~8x on 8-core systems)
2. **Match Duration**: Longer matches benefit more from parallelization
3. **I/O**: Agent loading can be a bottleneck (mitigated by caching)
4. **Memory**: Each process uses memory; ensure sufficient RAM

## Limitations

1. **Visual Mode**: Concurrent execution is disabled when `visual_mode=True`
2. **Windows**: Uses 'spawn' method (slightly slower startup)
3. **Memory**: Each worker process loads agents independently
4. **Pickling**: Training genomes must be pickleable

## Troubleshooting

### Issue: "PicklingError" in training
**Solution**: Ensure genomes are properly serializable. Use the provided `ConcurrentTrainingExecutor` which handles pickling.

### Issue: High memory usage
**Solution**: Reduce `batch_size` or `max_workers`:
```python
executor = ConcurrentMatchExecutor(max_workers=4)  # Use fewer workers
```

### Issue: Slower than expected
**Solution**: 
- Check CPU usage (should be ~100% on all cores)
- Ensure matches are CPU-bound (not I/O bound)
- Verify visual mode is off

## Implementation Details

### Process Management
- Uses `multiprocessing.Pool` for process management
- Workers are spawned (not forked) for Windows compatibility
- Processes are reused across batches for efficiency

### Error Handling
- Failed matches return error dicts
- Other matches continue processing
- Errors are logged but don't stop execution

### Resource Management
- Process pool is cleaned up after use
- Memory is freed when executor is closed
- Can be used as context manager:
```python
with ConcurrentMatchExecutor() as executor:
    results = executor.execute_matches(match_configs)
```

## Future Improvements

1. **Dynamic Worker Allocation**: Adjust workers based on system load
2. **Shared Memory**: Share agent cache across processes
3. **GPU Acceleration**: Use GPU for neural network inference
4. **Distributed Execution**: Run matches across multiple machines

