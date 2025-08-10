from evrptw_config import EvrptwGraph
from LocalSearch import LocalSearch

def get_path_cost(graph, path):
    """Evaluates the total distance of a given travel path."""
    distance = 0
    for i in range(len(path) - 1):
        distance += graph.node_dist_mat[path[i]][path[i+1]]
    return distance

def local_search_2opt_swap(graph: EvrptwGraph, initial_path: list):
    """
    Performs a local search optimization on the given path using a simple swap method.
    This is a simplified version of the local search described in the paper.
    """
    best_path = initial_path.copy()
    best_distance = get_path_cost(graph, best_path)
    ls_checker = LocalSearch(graph)

    improved = True
    while improved:
        improved = False
        for i in range(1, len(best_path) - 2):
            for j in range(i + 1, len(best_path) - 1):
                # Skip if depot or charging station
                if graph.nodes[best_path[i]].is_depot() or graph.nodes[best_path[j]].is_depot() or \
                   graph.nodes[best_path[i]].is_station() or graph.nodes[best_path[j]].is_station():
                    continue

                # Create a new path by swapping two customers
                new_path = best_path.copy()
                new_path[i], new_path[j] = new_path[j], new_path[i]

                # Check feasibility of the new path via LocalSearch (split routes and check each)
                routes = ls_checker._split_routes(new_path)
                feasible = all(ls_checker._check_feasible(r) for r in routes)
                if feasible:
                    new_distance = get_path_cost(graph, new_path)
                    if new_distance < best_distance:
                        best_path = new_path
                        best_distance = new_distance
                        improved = True
                        # Break inner loops to restart the search from the beginning of the improved path
                        break
            if improved:
                break

    return best_path, best_distance
