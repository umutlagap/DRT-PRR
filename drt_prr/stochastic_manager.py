"""
Stochastic Decision Manager for the DRT-PRR model.

This module manages controlled stochasticity in agent decision-making,
ensuring a target cumulative deviation from deterministic outcomes.
"""

import numpy as np
import random
from . import config


class StochasticDecisionManager:
    """
    Manages stochastic elements in agent decision making with controlled cumulative impact.
    
    This class ensures that stochastic decisions across the simulation remain within
    a target cumulative rate (default 10%), providing reproducibility while allowing
    for realistic behavioral variation.
    
    Attributes:
        target_cumulative (float): Target maximum stochastic rate
        decisions_made (int): Total decisions tracked
        stochastic_decisions (int): Number of stochastic decisions made
        decision_weights (dict): Probability weights per decision type
        decision_stats (dict): Statistics for each decision type
    """
    
    def __init__(self, target_cumulative_stochasticity=None, random_seed=None):
        """
        Initialize the stochastic decision manager.
        
        Args:
            target_cumulative_stochasticity (float): Target stochastic rate (default from config)
            random_seed (int): Random seed for reproducibility (None for true randomness)
        """
        self.target_cumulative = target_cumulative_stochasticity or config.TARGET_STOCHASTICITY
        self.decisions_made = 0
        self.stochastic_decisions = 0
        
        # Set random seed
        if random_seed is not None:
            np.random.seed(random_seed)
            random.seed(random_seed)
        
        # Generate decision weights
        self.decision_weights = self._generate_decision_weights()
        
        # Initialize statistics tracking
        self.decision_stats = {
            decision_type: {'total': 0, 'stochastic': 0}
            for decision_type in self.decision_weights.keys()
        }
    
    def _generate_decision_weights(self):
        """
        Generate random weights for each decision type within specified ranges.
        
        Returns:
            dict: Decision type -> probability weight
        """
        weight_ranges = config.DECISION_WEIGHT_RANGES
        
        # Generate random weights within ranges
        random_weights = {}
        for decision_type, (min_val, max_val) in weight_ranges.items():
            random_weights[decision_type] = np.random.uniform(min_val, max_val)
        
        # Scale to ensure sum equals target cumulative
        total_weight = sum(random_weights.values())
        scale_factor = self.target_cumulative / total_weight
        
        return {
            decision_type: weight * scale_factor
            for decision_type, weight in random_weights.items()
        }
    
    def should_apply_stochasticity(self, decision_type):
        """
        Determine if stochasticity should be applied to a decision.
        
        Uses declining probability to maintain cumulative target rate.
        
        Args:
            decision_type (str): Type of decision being made
            
        Returns:
            bool: True if stochastic variation should be applied
        """
        if decision_type not in self.decision_weights:
            return False
        
        self.decisions_made += 1
        self.decision_stats[decision_type]['total'] += 1
        
        # Calculate current stochastic rate
        current_rate = self.stochastic_decisions / max(1, self.decisions_made)
        
        # Determine probability
        if current_rate >= self.target_cumulative:
            probability = 0
        else:
            remaining_budget = self.target_cumulative - current_rate
            base_prob = self.decision_weights[decision_type]
            probability = min(base_prob, remaining_budget * 3)
        
        apply_stochasticity = random.random() < probability
        
        if apply_stochasticity:
            self.stochastic_decisions += 1
            self.decision_stats[decision_type]['stochastic'] += 1
        
        return apply_stochasticity
    
    def get_statistics(self):
        """
        Get current stochasticity statistics.
        
        Returns:
            dict: Statistics including rate, counts, and per-type breakdown
        """
        if self.decisions_made == 0:
            return {
                "rate": 0,
                "total_decisions": 0,
                "stochastic_decisions": 0,
                "target": self.target_cumulative,
                "by_type": {}
            }
        
        by_type_stats = {}
        for decision_type, stats in self.decision_stats.items():
            if stats['total'] > 0:
                by_type_stats[decision_type] = {
                    'total': stats['total'],
                    'stochastic': stats['stochastic'],
                    'rate': stats['stochastic'] / stats['total']
                }
        
        return {
            "rate": self.stochastic_decisions / self.decisions_made,
            "total_decisions": self.decisions_made,
            "stochastic_decisions": self.stochastic_decisions,
            "target": self.target_cumulative,
            "by_type": by_type_stats
        }
    
    def reset(self):
        """Reset all statistics and counters."""
        self.decisions_made = 0
        self.stochastic_decisions = 0
        for stats in self.decision_stats.values():
            stats['total'] = 0
            stats['stochastic'] = 0
