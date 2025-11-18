import neat
import inspect
from neat.config import DefaultClassConfig

print(f"NEAT Version: {neat.__version__}")
print(f"DefaultClassConfig spec: {inspect.getfullargspec(DefaultClassConfig.__init__)}")

import neat.stagnation
print(f"Source of stagnation.parse_config:\n{inspect.getsource(neat.stagnation.DefaultStagnation.parse_config)}")
