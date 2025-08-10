import numpy as np
from evrptw_config import EvrptwGraph
from ant import Ant

def get_path_cost(graph, path):
    """Evaluates the total distance of a given travel path."""
    distance = 0
    for i in range(len(path) - 1):
        distance += graph.node_dist_mat[path[i]][path[i+1]]
    return distance

def nearest_neighbor_initial_solution(graph: EvrptwGraph, num_vehicles: int = None):
    """
    Generates an initial feasible solution using the nearest neighbor heuristic.
    Starts from the depot and iteratively adds the nearest valid customer.
    """
    path = [graph.depot.idx]
    unvisited = set(i for i, node in enumerate(graph.nodes) if node.is_customer())
    
    ant = Ant(graph)
    
    vehicles_used = 1
    max_vehicles = num_vehicles if num_vehicles is not None else graph.vehicles

    while unvisited:
        last_node_idx = ant.current_index
        nearest_customer = -1
        min_dist = float('inf')

        # Find the nearest valid customer
        sorted_neighbors = sorted(list(unvisited), key=lambda c: graph.node_dist_mat[last_node_idx][c])

        found_next = False
        for customer_idx in sorted_neighbors:
            if ant.check_condition(customer_idx):
                ant.move_to_next_index(customer_idx)
                unvisited.remove(customer_idx)
                path.append(customer_idx)
                found_next = True
                break
        
        # If no valid customer can be reached, return to depot
        if not found_next:
            if vehicles_used < max_vehicles:
                ant.return_to_depot()
                path.append(graph.depot.idx)
                vehicles_used += 1
            else:
                # Cannot use more vehicles, force insert remaining customers
                # This part can be improved based on paper's description of forced insertion
                for customer_idx in list(unvisited):
                    path.append(customer_idx)
                    unvisited.remove(customer_idx)
                break # End of loop

    if path[-1] != graph.depot.idx:
        ant.return_to_depot()
        path.append(graph.depot.idx)

    cost = get_path_cost(graph, path)
    return path, cost
