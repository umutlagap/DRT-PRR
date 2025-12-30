"""
Analysis utilities for DRT-PRR simulation results.

This module provides functions for aggregating and analyzing
results from multiple simulation runs.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path


def aggregate_satisfaction_across_runs(output_dir, num_runs=10):
    """
    Aggregate satisfaction data across multiple simulation runs.
    
    Args:
        output_dir (str): Base directory containing run folders
        num_runs (int): Number of runs to process
        
    Returns:
        pd.DataFrame: Aggregated satisfaction statistics
    """
    all_run_data = {}
    
    for run_num in range(1, num_runs + 1):
        run_dir = Path(output_dir) / f"run_{run_num:02d}"
        steps_dir = run_dir / "output_steps"
        
        if not steps_dir.exists():
            print(f"Warning: {steps_dir} not found, skipping run {run_num}")
            continue
        
        # Find all agent files
        agent_files = sorted(steps_dir.glob("agents_*.csv"))
        
        run_satisfaction = {}
        for agent_file in agent_files:
            # Extract month from filename
            month = agent_file.stem.replace("agents_", "")
            
            df = pd.read_csv(agent_file)
            if 'Satisfaction' in df.columns:
                run_satisfaction[month] = df['Satisfaction'].mean()
        
        all_run_data[f"run_{run_num:02d}"] = run_satisfaction
    
    # Create summary DataFrame
    df_summary = pd.DataFrame(all_run_data)
    df_summary.index.name = 'Month'
    
    # Calculate statistics
    df_summary['Mean'] = df_summary.mean(axis=1)
    df_summary['Std'] = df_summary.std(axis=1)
    df_summary['Min'] = df_summary.min(axis=1)
    df_summary['Max'] = df_summary.max(axis=1)
    df_summary['Range'] = df_summary['Max'] - df_summary['Min']
    
    return df_summary


def calculate_recovery_metrics(df_longitudinal):
    """
    Calculate key recovery metrics from longitudinal data.
    
    Args:
        df_longitudinal (pd.DataFrame): Longitudinal simulation data
        
    Returns:
        dict: Recovery metrics
    """
    metrics = {}
    
    # Final status distribution
    final_step = df_longitudinal['Step'].max()
    final_data = df_longitudinal[df_longitudinal['Step'] == final_step]
    
    status_dist = final_data['Relocation_Status'].value_counts(normalize=True)
    metrics['final_status_distribution'] = status_dist.to_dict()
    
    # Return rate
    returned = final_data[final_data['Relocation_Status'] == 'return_back']
    metrics['return_rate'] = len(returned) / len(final_data)
    
    # Left city rate
    left = final_data[final_data['Relocation_Status'] == 'left_city']
    metrics['left_city_rate'] = len(left) / len(final_data)
    
    # Mean satisfaction over time
    sat_by_step = df_longitudinal.groupby('Step')['Satisfaction'].mean()
    metrics['satisfaction_trajectory'] = sat_by_step.to_dict()
    
    # Time to 50% satisfaction recovery
    initial_sat = sat_by_step.iloc[0] if len(sat_by_step) > 0 else 0
    final_sat = sat_by_step.iloc[-1] if len(sat_by_step) > 0 else 0
    target_sat = initial_sat + (final_sat - initial_sat) * 0.5
    
    for step, sat in sat_by_step.items():
        if sat >= target_sat:
            metrics['months_to_50pct_recovery'] = step
            break
    
    return metrics


def compare_scenarios(scenario_results):
    """
    Compare results across different policy scenarios.
    
    Args:
        scenario_results (dict): Dictionary mapping scenario name to results DataFrame
        
    Returns:
        pd.DataFrame: Comparison table
    """
    comparison_data = []
    
    for scenario_name, df in scenario_results.items():
        final_step = df['Step'].max()
        final_data = df[df['Step'] == final_step]
        
        total = len(final_data)
        
        row = {
            'Scenario': scenario_name,
            'Return_Rate': len(final_data[final_data['Relocation_Status'] == 'return_back']) / total,
            'Left_City_Rate': len(final_data[final_data['Relocation_Status'] == 'left_city']) / total,
            'In_Shelter_Rate': len(final_data[final_data['Relocation_Status'] == 'shelter']) / total,
            'Final_Mean_Satisfaction': final_data['Satisfaction'].mean(),
            'Final_Satisfaction_Std': final_data['Satisfaction'].std()
        }
        
        comparison_data.append(row)
    
    return pd.DataFrame(comparison_data)


def analyze_equity(df_longitudinal, group_column='Land_Use'):
    """
    Analyze recovery equity across different groups.
    
    Args:
        df_longitudinal (pd.DataFrame): Longitudinal data
        group_column (str): Column to group by (e.g., 'Land_Use', 'Income')
        
    Returns:
        pd.DataFrame: Equity analysis results
    """
    final_step = df_longitudinal['Step'].max()
    final_data = df_longitudinal[df_longitudinal['Step'] == final_step]
    
    equity_stats = final_data.groupby(group_column).agg({
        'Satisfaction': ['mean', 'std', 'min', 'max'],
        'H_ID': 'count'
    }).round(3)
    
    equity_stats.columns = ['Mean_Satisfaction', 'Std_Satisfaction', 
                           'Min_Satisfaction', 'Max_Satisfaction', 'Count']
    
    # Calculate return rates by group
    return_rates = final_data.groupby(group_column).apply(
        lambda x: (x['Relocation_Status'] == 'return_back').sum() / len(x)
    )
    equity_stats['Return_Rate'] = return_rates
    
    return equity_stats


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze DRT-PRR simulation results")
    parser.add_argument("--output-dir", type=str, required=True,
                        help="Directory containing simulation outputs")
    parser.add_argument("--num-runs", type=int, default=10,
                        help="Number of runs to aggregate")
    
    args = parser.parse_args()
    
    # Run aggregation
    df_summary = aggregate_satisfaction_across_runs(args.output_dir, args.num_runs)
    
    # Save results
    output_path = Path(args.output_dir) / "satisfaction_summary.xlsx"
    df_summary.to_excel(output_path)
    print(f"Saved aggregated results to: {output_path}")
