import itertools
import csv
import time
import os
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from MACS import MACS

def tune_macs_parameters(
    instance_path: str,
    param_grid: dict,
    output_file: str,
    num_runs_per_param_set: int = 5,
    macs_config_base: dict = None
):
    """
    Tunes MACS parameters by running the algorithm with different parameter combinations
    and saving the results to a CSV file.

    Args:
        instance_path (str): Absolute path to the EVRPTW instance file.
        param_grid (dict): A dictionary where keys are parameter names (e.g., 'alpha', 'beta')
                           and values are lists of values to test for that parameter.
        output_file (str): Absolute path to the CSV file where results will be saved.
        num_runs_per_param_set (int): Number of times to run MACS for each parameter set
                                      to get average results.
        macs_config_base (dict, optional): Base configuration dictionary for MACS.
                                           Tuning parameters will override these.
                                           Defaults to an empty dict.
    """
    if macs_config_base is None:
        macs_config_base = {}

    # Prepare CSV header
    fieldnames = list(param_grid.keys()) + [
        'avg_vehicles', 'avg_distance', 'avg_time_sec',
        'best_vehicles', 'best_distance', 'best_time_sec'
    ]

    # Generate all parameter combinations
    param_names = list(param_grid.keys())
    param_combinations = list(itertools.product(*param_grid.values()))

    print(f"Starting parameter tuning for {len(param_combinations)} combinations, {num_runs_per_param_set} runs each.")
    print(f"Results will be saved to: {output_file}")

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i, combo in enumerate(param_combinations):
            param_set = dict(zip(param_names, combo))
            print(f"\n--- Tuning combination {i+1}/{len(param_combinations)}: {param_set} ---")

            total_vehicles = 0
            total_distance = 0.0
            total_time = 0.0
            
            run_best_vehicles = float('inf')
            run_best_distance = float('inf')
            run_best_time = float('inf')

            for run_idx in range(num_runs_per_param_set):
                print(f"  Run {run_idx+1}/{num_runs_per_param_set}...")
                
                # Create a new config for this run, merging base and tuning params
                current_macs_config = macs_config_base.copy()
                for k, v in param_set.items():
                    # Assuming tuning parameters are directly under macs_config_base
                    # If they are nested (e.g., under 'acs_dist'), this needs adjustment
                    current_macs_config[k] = v 
                
                # Special handling for nested parameters like alpha, beta, q0
                # These are typically under acs_dist or acs_vei
                if 'alpha' in param_set or 'beta' in param_set or 'q0' in param_set:
                    if 'acs_dist' not in current_macs_config:
                        current_macs_config['acs_dist'] = {}
                    if 'acs_vei' not in current_macs_config:
                        current_macs_config['acs_vei'] = {}
                    
                    if 'alpha' in param_set:
                        current_macs_config['acs_dist']['alpha'] = param_set['alpha']
                        current_macs_config['acs_vei']['alpha'] = param_set['alpha']
                    if 'beta' in param_set:
                        current_macs_config['acs_dist']['beta'] = param_set['beta']
                        current_macs_config['acs_vei']['beta'] = param_set['beta']
                    if 'q0' in param_set:
                        current_macs_config['acs_dist']['q0'] = param_set['q0']
                        current_macs_config['acs_vei']['q0'] = param_set['q0']

                macs_solver = MACS(instance_path, current_macs_config)
                
                start_time = time.time()
                final_path, final_distance, final_vehicles = macs_solver.run()
                end_time = time.time()
                
                run_time = end_time - start_time

                total_vehicles += final_vehicles
                total_distance += final_distance
                total_time += run_time

                if final_vehicles < run_best_vehicles or \
                   (final_vehicles == run_best_vehicles and final_distance < run_best_distance):
                    run_best_vehicles = final_vehicles
                    run_best_distance = final_distance
                    run_best_time = run_time # Store time for this best run

            avg_vehicles = total_vehicles / num_runs_per_param_set
            avg_distance = total_distance / num_runs_per_param_set
            avg_time = total_time / num_runs_per_param_set

            row = param_set.copy()
            row['avg_vehicles'] = avg_vehicles
            row['avg_distance'] = avg_distance
            row['avg_time_sec'] = avg_time
            row['best_vehicles'] = run_best_vehicles
            row['best_distance'] = run_best_distance
            row['best_time_sec'] = run_best_time
            
            writer.writerow(row)
            csvfile.flush() # Ensure data is written immediately

    print("\nParameter tuning complete.")

# Example usage (this part would be in a separate script or directly executed)
if __name__ == '__main__':
    # Define your instance path (absolute path)
    # You might need to adjust this based on where you run the script
    # For example, if running from ACO_4 directory:
    # instance_file = os.path.join(os.getcwd(), 'paper_total_instances', 'c101C5.txt')
    
    # For this example, let's assume a dummy path and remind the user to change it
    instance_file = r"test_instances/c202C15.txt"
    output_csv = r"D:\Work\ORLab\Python\EVRP_TW_DWC1\EVRPTW_ACO\ACO_4\tuning_results.csv"

    # Define the parameter grid
    param_grid = {
        'alpha': [1.0, 2.0, 3.0, 4.0],
        'beta': [1.0, 2.0, 3.0, 4.0],
        'q0': [0.5, 0.7, 0.9]
    }

    # Base MACS configuration (other parameters not being tuned)
    macs_base_config = {
        'max_iterations': 1000,
        'inner_iterations': 5,
        'num_ants': 10,
        'global_update_rho': 0.1,
        'local_update_xi': 0.1,
        'ls_max_segment_len': 2,
        'ls_verbose': False,
        'objective_weights': (0.9, 0.1)
    }

    tune_macs_parameters(
        instance_path=instance_file,
        param_grid=param_grid,
        output_file=output_csv,
        num_runs_per_param_set=2, # Reduced for quick testing
        macs_config_base=macs_base_config
    )
