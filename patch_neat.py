import neat.stagnation
from neat.config import ConfigParameter, DefaultClassConfig

def patched_parse_config(cls, param_dict):
    return DefaultClassConfig(param_dict,
                              [ConfigParameter('species_fitness_func', str, 'mean'),
                               ConfigParameter('max_stagnation', int, 15),
                               ConfigParameter('species_elitism', int, 0),
                               ConfigParameter('min_species_size', int, 1)],
                              'DefaultStagnation')

neat.stagnation.DefaultStagnation.parse_config = classmethod(patched_parse_config)
print("Applied monkeypatch to neat.stagnation.DefaultStagnation.parse_config")
