"""
Example script for running the DRT-PRR simulation.

This script demonstrates how to:
1. Load data
2. Initialize the model
3. Run the simulation
4. Export results
"""

import pandas as pd
import time
import os

from drt_prr import DTRecoveryModel, load_data, config


def run_simulation(data_dir, output_dir="output"):
    """
    Run a single simulation.
    
    Args:
        data_dir (str): Directory containing input data files
        output_dir (str): Directory for output files
    """
    print("=" * 60)
    print("DRT-PRR: Digital Risk Twin Post-Disaster Recovery Model")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    print("\n[1/4] Loading data...")
    data = load_data(
        households_path=os.path.join(data_dir, "households.xlsx"),
        recovery_path=os.path.join(data_dir, "recovery_monitoring.xlsx"),
        shelters_path=os.path.join(data_dir, "shelters.xlsx"),
        schools_path=os.path.join(data_dir, "schools.xlsx"),
        hospitals_path=os.path.join(data_dir, "hospitals.xlsx"),
        new_buildings_path=os.path.join(data_dir, "new_buildings.xlsx"),
        new_jobs_path=os.path.join(data_dir, "new_jobs.xlsx"),
        new_buildings_recovery_path=os.path.join(data_dir, "new_buildings_recovery.xlsx")
    )
    
    # Initialize model
    print("\n[2/4] Initializing model...")
    start_time = time.time()
    
    model = DTRecoveryModel(
        df_households=data['households'],
        df_recovery=data['recovery'],
        month_cols=data['month_cols'],
        df_shelters=data['shelters'],
        df_schools=data['schools'],
        df_hospitals=data['hospitals'],
        df_new_buildings=data.get('new_buildings'),
        df_new_jobs=data.get('new_jobs'),
        df_new_buildings_recovery=data.get('new_buildings_recovery')
    )
    
    init_time = time.time() - start_time
    print(f"  Initialization completed in {init_time:.2f} seconds")
    
    # Run simulation
    print("\n[3/4] Running simulation...")
    sim_start = time.time()
    
    for i, month in enumerate(data['month_cols']):
        step_start = time.time()
        model.advance(month)
        step_time = time.time() - step_start
        
        # Progress update
        if (i + 1) % 10 == 0 or i == 0 or i == len(data['month_cols']) - 1:
            stats = model.get_summary_statistics()
            print(f"  Step {i+1}/{len(data['month_cols'])} ({month}): "
                  f"{step_time:.2f}s - "
                  f"Shelter: {stats['shelter_occupancy']}, "
                  f"Left city: {stats['left_city_stats']['total_departures']}")
    
    sim_time = time.time() - sim_start
    print(f"  Simulation completed in {sim_time:.2f} seconds")
    
    # Export results
    print("\n[4/4] Exporting results...")
    
    # Longitudinal data
    df_longitudinal = model.export_collected_longitudinal_data()
    if df_longitudinal is not None:
        csv_path = os.path.join(output_dir, "longitudinal_data.csv")
        xlsx_path = os.path.join(output_dir, "longitudinal_data.xlsx")
        df_longitudinal.to_csv(csv_path, index=False)
        df_longitudinal.to_excel(xlsx_path, index=False)
        print(f"  Saved longitudinal data: {len(df_longitudinal)} records")
    
    # Final summary
    stats = model.get_summary_statistics()
    summary_path = os.path.join(output_dir, "simulation_summary.txt")
    with open(summary_path, 'w') as f:
        f.write("DRT-PRR Simulation Summary\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Total agents: {stats['total_agents']}\n")
        f.write(f"Simulation steps: {stats['current_step']}\n")
        f.write(f"Final month: {stats['current_month']}\n\n")
        f.write("Final Status Distribution:\n")
        for status, count in sorted(stats['status_distribution'].items()):
            pct = count / stats['total_agents'] * 100
            f.write(f"  {status}: {count} ({pct:.1f}%)\n")
        f.write(f"\nLeft City Statistics:\n")
        f.write(f"  Total departures: {stats['left_city_stats']['total_departures']}\n")
        f.write(f"  Total returns: {stats['left_city_stats']['total_returns']}\n")
        f.write(f"\nStochasticity:\n")
        stoch = stats['stochasticity']
        f.write(f"  Rate: {stoch['rate']:.2%} (target: {stoch['target']:.1%})\n")
        f.write(f"  Total decisions: {stoch['total_decisions']}\n")
        f.write(f"  Stochastic decisions: {stoch['stochastic_decisions']}\n")
    
    print(f"  Saved summary to: {summary_path}")
    
    # Print final summary
    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60)
    print(f"Total time: {time.time() - start_time:.1f} seconds")
    print(f"\nFinal Status Distribution:")
    for status, count in sorted(stats['status_distribution'].items()):
        pct = count / stats['total_agents'] * 100
        print(f"  {status}: {count} ({pct:.1f}%)")
    
    return model, df_longitudinal


def run_multi_simulation(data_dir, output_dir="output_runs", num_runs=10, base_seed=42):
    """
    Run multiple stochastic simulations.
    
    Args:
        data_dir (str): Directory containing input data files
        output_dir (str): Base directory for output files
        num_runs (int): Number of simulation runs
        base_seed (int): Base random seed (incremented for each run)
        
    Returns:
        pd.DataFrame: Summary statistics across all runs
    """
    import numpy as np
    import gc
    
    print("=" * 60)
    print(f"MULTI-RUN SIMULATION: {num_runs} STOCHASTIC RUNS")
    print("=" * 60)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data once
    print("\nLoading data (shared across all runs)...")
    data = load_data(
        households_path=os.path.join(data_dir, "households.xlsx"),
        recovery_path=os.path.join(data_dir, "recovery_monitoring.xlsx"),
        shelters_path=os.path.join(data_dir, "shelters.xlsx"),
        schools_path=os.path.join(data_dir, "schools.xlsx"),
        hospitals_path=os.path.join(data_dir, "hospitals.xlsx")
    )
    
    all_runs_summary = []
    
    for run_num in range(1, num_runs + 1):
        print(f"\n{'='*40}")
        print(f"RUN {run_num}/{num_runs}")
        print(f"{'='*40}")
        
        run_seed = base_seed + run_num
        np.random.seed(run_seed)
        
        # Create run output directory
        run_output_dir = os.path.join(output_dir, f"run_{run_num:02d}")
        os.makedirs(run_output_dir, exist_ok=True)
        
        # Initialize model
        model = DTRecoveryModel(
            df_households=data['households'],
            df_recovery=data['recovery'],
            month_cols=data['month_cols'],
            df_shelters=data['shelters'],
            df_schools=data['schools'],
            df_hospitals=data['hospitals']
        )
        
        # Run simulation
        for month in data['month_cols']:
            model.advance(month)
        
        # Collect summary
        stats = model.get_summary_statistics()
        run_summary = {
            'run': run_num,
            'seed': run_seed,
            'total_agents': stats['total_agents'],
            'stochastic_rate': stats['stochasticity']['rate']
        }
        
        for status, count in stats['status_distribution'].items():
            run_summary[f'final_{status}'] = count
        
        run_summary['departures'] = stats['left_city_stats']['total_departures']
        run_summary['returns'] = stats['left_city_stats']['total_returns']
        
        all_runs_summary.append(run_summary)
        
        # Save run data
        df_longitudinal = model.export_collected_longitudinal_data()
        if df_longitudinal is not None:
            df_longitudinal.to_csv(
                os.path.join(run_output_dir, f"longitudinal_run_{run_num:02d}.csv"),
                index=False
            )
        
        # Cleanup
        del model
        gc.collect()
        
        print(f"  Completed run {run_num}")
    
    # Save combined summary
    df_summary = pd.DataFrame(all_runs_summary)
    df_summary.to_csv(os.path.join(output_dir, "all_runs_summary.csv"), index=False)
    df_summary.to_excel(os.path.join(output_dir, "all_runs_summary.xlsx"), index=False)
    
    # Print aggregate statistics
    print("\n" + "=" * 60)
    print("AGGREGATE STATISTICS")
    print("=" * 60)
    
    numeric_cols = df_summary.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col not in ['run', 'seed']:
            print(f"{col}: mean={df_summary[col].mean():.2f}, std={df_summary[col].std():.2f}")
    
    return df_summary


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run DRT-PRR simulation")
    parser.add_argument("--data-dir", type=str, required=True,
                        help="Directory containing input data files")
    parser.add_argument("--output-dir", type=str, default="output",
                        help="Directory for output files")
    parser.add_argument("--multi-run", action="store_true",
                        help="Run multiple stochastic simulations")
    parser.add_argument("--num-runs", type=int, default=10,
                        help="Number of runs for multi-run simulation")
    parser.add_argument("--seed", type=int, default=42,
                        help="Base random seed")
    
    args = parser.parse_args()
    
    if args.multi_run:
        run_multi_simulation(
            data_dir=args.data_dir,
            output_dir=args.output_dir,
            num_runs=args.num_runs,
            base_seed=args.seed
        )
    else:
        run_simulation(
            data_dir=args.data_dir,
            output_dir=args.output_dir
        )
