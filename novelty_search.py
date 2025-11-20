"""Novelty Search implementation for PyPongAI.

This module implements behavioral novelty tracking to encourage diverse AI strategies.
The behavioral characteristic (BC) used is the average Y-coordinate of ball-paddle contacts.
"""

import numpy as np


class NoveltyArchive:
    """Stores and analyzes behavioral characteristics of successful genomes.
    
    The archive maintains a collection of behavioral characteristics (BCs) from
    past genomes to calculate novelty scores. This encourages exploration of
    diverse strategies rather than converging to a single optimal approach.
    
    Attributes:
        archive: List of behavioral characteristics (average contact Y positions).
        max_size: Maximum number of BCs to store (FIFO when exceeded).
        k_nearest: Number of nearest neighbors to use for novelty calculation.
    """
    
    def __init__(self, max_size=500, k_nearest=15):
        """Initializes the novelty archive.
        
        Args:
            max_size: Maximum archive size. Oldest entries removed when exceeded.
            k_nearest: Number of nearest neighbors for novelty calculation.
        """
        self.archive = []
        self.max_size = max_size
        self.k_nearest = k_nearest
    
    def add_bc(self, bc_value):
        """Adds a behavioral characteristic to the archive.
        
        Args:
            bc_value: The BC value to add (average contact Y-coordinate).
        """
        self.archive.append(bc_value)
        
        # Maintain max size (FIFO)
        if len(self.archive) > self.max_size:
            self.archive.pop(0)
    
    def calculate_novelty(self, bc_value):
        """Calculates the novelty score for a given BC.
        
        Novelty is the average distance to the k-nearest neighbors in the archive.
        Higher novelty means the behavior is more different from past behaviors.
        
        Args:
            bc_value: The BC value to evaluate.
        
        Returns:
            float: Novelty score (average distance to k-nearest neighbors).
                Returns 0.0 if archive is too small.
        """
        if len(self.archive) < self.k_nearest:
            # Not enough archive data yet, return default novelty
            return 0.0
        
        # Calculate distances to all archive entries
        distances = [abs(bc_value - archive_bc) for archive_bc in self.archive]
        
        # Sort and get k-nearest distances
        distances.sort()
        k_nearest_distances = distances[:self.k_nearest]
        
        # Return average distance (novelty score)
        return np.mean(k_nearest_distances)
    
    def get_archive_size(self):
        """Returns the current size of the archive.
        
        Returns:
            int: Number of BCs currently stored.
        """
        return len(self.archive)


def calculate_bc_from_contacts(contact_metrics_list):
    """Calculates behavioral characteristic from contact data.
    
    The BC is defined as the average Y-coordinate of all ball-paddle contacts.
    This represents where the genome tends to make contact with the ball.
    
    Args:
        contact_metrics_list: List of dictionaries containing contact_y values.
    
    Returns:
        float: Average contact Y-coordinate, or None if no contacts occurred.
    """
    contact_y_values = []
    
    for metrics in contact_metrics_list:
        if "contact_y" in metrics:
            contact_y_values.append(metrics["contact_y"])
    
    if len(contact_y_values) == 0:
        return None  # No contacts, can't calculate BC
    
    return np.mean(contact_y_values)
