"""
Visualization utilities for DRT-PRR simulation results.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_satisfaction_trajectory(df_summary, output_path=None, title="Mean Satisfaction Over Time"):
    """
    Plot satisfaction trajectory with confidence bands.
    
    Args:
        df_summary (pd.DataFrame): Summary with Mean, Min, Max columns
        output_path (str, optional): Path to save figure
        title (str): Plot title
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = range(len(df_summary))
    
    # Plot mean line
    ax.plot(x, df_summary['Mean'], 'b-', linewidth=2, label='Mean')
    
    # Plot min-max range
    ax.fill_between(x, df_summary['Min'], df_summary['Max'],
                    alpha=0.3, color='blue', label='Min-Max Range')
    
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Mean Satisfaction', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Set x-axis labels
    if len(df_summary) <= 24:
        ax.set_xticks(x)
        ax.set_xticklabels(df_summary.index, rotation=45, ha='right')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved figure to: {output_path}")
    
    return fig, ax


def plot_status_distribution(status_counts, output_path=None, title="Final Relocation Status Distribution"):
    """
    Plot bar chart of status distribution.
    
    Args:
        status_counts (dict): Status -> count mapping
        output_path (str, optional): Path to save figure
        title (str): Plot title
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    statuses = list(status_counts.keys())
    counts = list(status_counts.values())
    total = sum(counts)
    percentages = [c/total*100 for c in counts]
    
    bars = ax.bar(statuses, percentages, color='steelblue', edgecolor='black')
    
    # Add value labels
    for bar, pct in zip(bars, percentages):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{pct:.1f}%', ha='center', va='bottom', fontsize=10)
    
    ax.set_xlabel('Relocation Status', fontsize=12)
    ax.set_ylabel('Percentage (%)', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.set_xticklabels(statuses, rotation=45, ha='right')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved figure to: {output_path}")
    
    return fig, ax


def plot_scenario_comparison(comparison_df, metric='Return_Rate', output_path=None):
    """
    Plot comparison of scenarios.
    
    Args:
        comparison_df (pd.DataFrame): Scenario comparison data
        metric (str): Column to compare
        output_path (str, optional): Path to save figure
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    
    scenarios = comparison_df['Scenario']
    values = comparison_df[metric]
    
    colors = plt.cm.viridis(np.linspace(0.2, 0.8, len(scenarios)))
    bars = ax.bar(scenarios, values, color=colors, edgecolor='black')
    
    # Add value labels
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{val:.1%}', ha='center', va='bottom', fontsize=10)
    
    ax.set_xlabel('Scenario', fontsize=12)
    ax.set_ylabel(metric.replace('_', ' '), fontsize=12)
    ax.set_title(f'Scenario Comparison: {metric.replace("_", " ")}', fontsize=14)
    ax.set_xticklabels(scenarios, rotation=45, ha='right')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved figure to: {output_path}")
    
    return fig, ax


def plot_multi_series(data_dict, labels=None, colors=None, output_path=None,
                     title="Multi-Series Comparison", xlabel="Step", ylabel="Value"):
    """
    Plot multiple satisfaction series with shaded ranges.
    
    Args:
        data_dict (dict): Series name -> DataFrame with Mean, Min, Max columns
        labels (list, optional): Custom labels
        colors (list, optional): Custom colors
        output_path (str, optional): Path to save figure
        title (str): Plot title
        xlabel (str): X-axis label
        ylabel (str): Y-axis label
    """
    fig, ax = plt.subplots(figsize=(14, 7))
    
    if colors is None:
        colors = ['#2E86AB', '#E8A838', '#28A745', '#DC3545', '#6F42C1']
    
    for i, (name, df) in enumerate(data_dict.items()):
        color = colors[i % len(colors)]
        label = labels[i] if labels else name
        
        x = range(len(df))
        
        # Plot mean line
        ax.plot(x, df['Mean'], color=color, linewidth=2, label=label)
        
        # Plot min-max range
        ax.fill_between(x, df['Min'], df['Max'], alpha=0.2, color=color)
    
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.savefig(output_path.replace('.png', '.pdf'), bbox_inches='tight')
        print(f"Saved figure to: {output_path}")
    
    return fig, ax


if __name__ == "__main__":
    # Example usage
    print("Visualization utilities for DRT-PRR")
    print("Import and use functions: plot_satisfaction_trajectory, plot_status_distribution, etc.")
