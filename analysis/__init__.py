"""
Analysis utilities for DRT-PRR simulation results.
"""

from .analyze_results import (
    aggregate_satisfaction_across_runs,
    calculate_recovery_metrics,
    compare_scenarios,
    analyze_equity
)

from .visualize import (
    plot_satisfaction_trajectory,
    plot_status_distribution,
    plot_scenario_comparison,
    plot_multi_series
)

__all__ = [
    'aggregate_satisfaction_across_runs',
    'calculate_recovery_metrics',
    'compare_scenarios',
    'analyze_equity',
    'plot_satisfaction_trajectory',
    'plot_status_distribution',
    'plot_scenario_comparison',
    'plot_multi_series'
]
