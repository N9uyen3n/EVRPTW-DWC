import argparse
import os
import glob
import time
import pandas as pd
import yaml
from MACS import MACS
from evrptw_config import EvrptwGraph

def run_single_instance(macs_instance, num_runs):
    """
    Runs the MACS algorithm for a single instance multiple times and returns the best result.
    """
    best_solution = (None, float('inf'), float('inf')) # (path, distance, num_vehicles)
    run_times = []

    for i in range(num_runs):
        start_time = time.time()
        current_solution = macs_instance.run()
        end_time = time.time()
        run_time = end_time - start_time
        run_times.append(run_time)

        # Prioritize total distance only
        if current_solution[1] < best_solution[1]:
            best_solution = current_solution

    avg_time = sum(run_times) / len(run_times) if run_times else 0
    
    return best_solution, avg_time

def tune_parameters(base_config, instance_path, num_runs):
    """
    Performs parameter tuning for the MACS algorithm.
    """
    print("--- Starting Parameter Tuning ---")
    print(f"Instance: {instance_path}")

    instance_name = os.path.basename(instance_path).replace('.txt', '')
    output_filename = f"{instance_name}_tune_results.csv"
    output_path = os.path.join('results_macs', output_filename)
    
    os.makedirs('results_macs', exist_ok=True)

    results_list = []

    # Define parameter ranges to test
    alphas = [1, 2, 3, 4]
    betas = [1, 2, 3, 4]
    rhos = [0.1, 0.2, 0.5]
    q0s = [0.5, 0.7, 0.9]

    best_overall_solution = (None, float('inf'), float('inf'))
    best_params = {}
    total_combinations = len(alphas) * len(betas) * len(rhos) * len(q0s)
    current_combination = 0

    for alpha in alphas:
        for beta in betas:
            for rho in rhos:
                for q0 in q0s:
                    current_combination += 1
                    print(f"\n[Tuning {current_combination}/{total_combinations}] alpha={alpha}, beta={beta}, rho={rho}, q0={q0}")
                    
                    # Create a copy of the base config and override with tuning params
                    tune_config = base_config.copy()
                    tune_config['global_update_rho'] = rho
                    tune_config['acs_dist']['alpha'] = alpha
                    tune_config['acs_dist']['beta'] = beta
                    tune_config['acs_dist']['q0'] = q0
                    tune_config['acs_vei']['alpha'] = alpha
                    tune_config['acs_vei']['beta'] = beta
                    tune_config['acs_vei']['q0'] = q0

                    # Run instance with tuned config
                    macs = MACS(instance_path, tune_config)
                    best_solution, avg_time = run_single_instance(macs, num_runs)
                    best_path, best_distance, best_vehicles = best_solution
                    print(f"Result: {best_vehicles} vehicles, distance {best_distance:.2f}")

                    results_list.append({
                        'alpha': alpha,
                        'beta': beta,
                        'rho': rho,
                        'q0': q0,
                        'best_vehicles': best_vehicles,
                        'best_distance': best_distance,
                        'avg_time_s': avg_time,
                    })

                    # Check against the overall best solution
                    if best_vehicles < best_overall_solution[2] or \
                       (best_vehicles == best_overall_solution[2] and best_distance < best_overall_solution[1]):
                        best_overall_solution = (None, best_distance, best_vehicles)
                        best_params = {'alpha': alpha, 'beta': beta, 'rho': rho, 'q0': q0}
                        print(f"*** New overall best solution found! Params: {best_params} ***")

    df = pd.DataFrame(results_list)
    df.to_csv(output_path, index=False)
    print(f"\n--- Tuning results saved to {output_path} ---")

    print("\n--- Tuning Finished ---")
    print(f"Best parameters found: {best_params}")
    print(f"Best solution: {best_overall_solution[2]} vehicles, distance {best_overall_solution[1]:.2f}")


def print_detailed_solution(graph, solution_path):
    """Simulates the final path and prints detailed information for each step."""
    if solution_path is None or not solution_path:
        print("No feasible solution found to print.")
        return
    print("\n--- Detailed Best Route ---")
    
    routes = [[]]
    for node_idx in solution_path:
        if node_idx == 0 and len(routes[-1]) > 0:
            routes[-1].append(0)
            routes.append([0])
        else:
            if not routes[-1]:
                routes[-1].append(0)
            if routes[-1][-1] != node_idx:
                 routes[-1].append(node_idx)

    if not routes[-1] or routes[-1][-1] != 0:
        routes[-1].append(0)

    for i, route in enumerate(routes):
        if len(route) <= 2: continue
        print(f"\nVehicle {i + 1}: Route: {' -> '.join(map(str, route))}")
        print("""--------------------------------------------------------------------------------
| Node | Type      | Arrival Time | Service Start | Departure Time | Battery on Arrival |
|------|-----------|--------------|---------------|----------------|--------------------|""")

        current_time = 0.0
        current_battery = graph.tank_capacity
        current_load = 0.0

        for j in range(len(route) - 1):
            from_node_idx = route[j]
            to_node_idx = route[j+1]
            
            from_node = graph.nodes[from_node_idx]
            to_node = graph.nodes[to_node_idx]

            dist = graph.node_dist_mat[from_node_idx][to_node_idx]
            travel_time = dist / graph.velocity
            fuel_consumed = dist * graph.fuel_consumption_rate

            arrival_time = current_time + travel_time
            battery_on_arrival = current_battery - fuel_consumed

            service_start_time = max(arrival_time, to_node.ready_time)
            wait_time = service_start_time - arrival_time
            
            departure_time = service_start_time + to_node.service_time
            
            # Special handling for charging stations
            if to_node.is_station():
                fuel_needed = graph.tank_capacity - battery_on_arrival
                charging_time = fuel_needed / graph.charging_rate if graph.charging_rate > 0 else 0
                departure_time += charging_time

            # Enforce non-negative display for battery on arrival
            battery_display = max(battery_on_arrival, 0.0)
            time_violate_flag = " !" if to_node.is_customer() and service_start_time > to_node.due_date + 1e-9 else ""
            print(f"| {to_node_idx:<4} | {to_node.node_type:<9} | {arrival_time:<12.2f} | {service_start_time:<13.2f} | {departure_time:<14.2f} | {battery_display:<18.2f} |{time_violate_flag}")

            # Update state for next leg
            current_time = departure_time
            current_battery = graph.tank_capacity if to_node.is_station() else battery_on_arrival
            if to_node.is_depot(): # Reset for next route if depot is intermediate
                current_battery = graph.tank_capacity

    print("--------------------------------------------------------------------------------")

def test_read_data(instance_path):
    print(f"--- Testing Data Reading for {os.path.basename(instance_path)} ---")
    try:
        # We need a dummy config for EvrptwGraph, as it expects one.
        # The rho value is not critical for just reading data.
        graph = EvrptwGraph(instance_path, rho=0.1)

        print(f"Total Nodes: {graph.node_num}")
        print(f"Depot Node (ID {graph.depot.idx}): ({graph.depot.x}, {graph.depot.y})")
        print(f"Number of Fuel Stations: {len(graph.fuel_stations)}")
        for i, fs in enumerate(graph.fuel_stations):
            if i < 3: # Print details for up to 3 fuel stations
                print(f"  Fuel Station {fs.idx}: ({fs.x}, {fs.y})")
            elif i == 3:
                print("  ...")
        
        customer_nodes = [node for node in graph.nodes if node.is_customer()]
        print(f"Number of Customer Nodes: {len(customer_nodes)}")
        for i, cust in enumerate(customer_nodes):
            if i < 3: # Print details for up to 3 customer nodes
                print(f"  Customer {cust.idx}: ({cust.x}, {cust.y}), Demand: {cust.demand}, Time Window: [{cust.ready_time}, {cust.due_date}], Service Time: {cust.service_time}")
            elif i == 3:
                print("  ...")

        print(f"Vehicle Tank Capacity: {graph.tank_capacity}")
        print(f"Vehicle Load Capacity: {graph.load_capacity}")
        print(f"Fuel Consumption Rate: {graph.fuel_consumption_rate}")
        print(f"Charging Rate: {graph.charging_rate}")
        print(f"Vehicle Velocity: {graph.velocity}")
        print("--- Data Reading Test Complete ---")

    except Exception as e:
        print(f"Error reading instance file: {e}")

def main():
    parser = argparse.ArgumentParser(description="Run MACS algorithm for E-VRPTW.")
    
    parser.add_argument('--file', type=str, help='Path to a single instance file to run.')
    parser.add_argument('--dir', type=str, help='Path to a directory containing instance files to run.')
    parser.add_argument('--runs', type=int, default=1, help='Number of times to run the algorithm for each instance.')
    parser.add_argument('--output', type=str, default='results.csv', help='Path to save the summary results CSV file.')
    parser.add_argument('--config', type=str, default='config/aco_config.yaml', help='Path to the ACO configuration file.')
    parser.add_argument('--tune', action='store_true', help='Enable parameter tuning mode.')
    parser.add_argument('--test-read', type=str, help='Path to an instance file to test data reading.')

    args = parser.parse_args()

    # Load base configuration from YAML
    with open(args.config, 'r') as f:
        base_config = yaml.safe_load(f)

    if args.tune:
        if not args.file:
            print("Error: Tuning mode requires a single file specified with --file.")
            return
        tune_parameters(base_config, args.file, args.runs)

    elif args.test_read:
        test_read_data(args.test_read)

    elif args.file:
        macs = MACS(args.file, base_config)
        best_solution, avg_time = run_single_instance(macs, args.runs)
        
        print(f"\n--- Final Result for {os.path.basename(args.file)} ---")
        print(f"Best solution: {best_solution[2]} vehicles, distance {best_solution[1]:.2f}")
        print(f"Avg. time: {avg_time:.2f}s over {args.runs} runs.")
        print_detailed_solution(macs.graph, best_solution[0])

    elif args.dir:
        instance_paths = glob.glob(os.path.join(args.dir, '*.txt'))
        if not instance_paths:
            print(f"No .txt files found in directory: {args.dir}")
            return

        results_list = []
        for path in sorted(instance_paths):
            print(f"\nProcessing {os.path.basename(path)}...")
            macs = MACS(path, base_config)
            result, avg_time = run_single_instance(macs, args.runs)
            results_list.append({
                'instance': os.path.basename(path),
                'best_vehicles': result[2],
                'best_distance': result[1],
                'avg_time_s': avg_time,
                'num_runs': args.runs
            })
        
        df = pd.DataFrame(results_list)
        df.to_csv(args.output, index=False)
        print(f"\nBatch run complete. Results saved to {args.output}")

    else:
        print("Please specify an execution mode: --file <path> or --dir <path> or --tune")

if __name__ == "__main__":
    main()

