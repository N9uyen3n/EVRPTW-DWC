from Ant import Ant, ACS_DIST_Ant, ACS_VEI_Ant
from evrptw_config import EvrptwGraph
import random
import math

class ACS:
    """Base class for Ant Colony System algorithms."""
    def __init__(self, graph: EvrptwGraph, params: dict):
        self.graph = graph
        self.params = params
        
        self.alpha = params.get('alpha', 1.0)
        self.beta = params.get('beta', 2.0)
        self.rho = params.get('rho', 0.1) 
        self.num_ants = params.get('num_ants', 10)
        
        self.ants = []
        self.best_solution_in_iteration = None 
        self.best_distance_in_iteration = float('inf')

    def run_single_iteration(self):
        """Runs one iteration of the ACS algorithm."""
        self.best_solution_in_iteration = None
        self.best_distance_in_iteration = float('inf')
        self._create_ants()
        self._construct_solutions()
        self._update_pheromones()

    def run(self):
        """Public interface - runs single iteration for MACS coordination."""
        self.run_single_iteration()

    def _create_ants(self):
        """Creates a new set of ants for an iteration."""
        raise NotImplementedError("This method should be implemented by subclasses.")

    def _construct_solutions(self):
        """Has each ant construct its solution."""
        for ant in self.ants:
            ant.target_vehicles = self._get_target_vehicles()
            path, distance = ant.construct_solution()
            
            if path and len(path) > 2: # Ensure path is not trivial
                ant.path = path
                ant.distance = distance
                
                if self._is_better_solution(path, distance):
                    self.best_distance_in_iteration = distance
                    self.best_solution_in_iteration = path[:]

    def _get_target_vehicles(self):
        """Get target number of vehicles - to be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement target vehicles.")

    def _is_better_solution(self, path, distance):
        """Check if this solution is better than current best."""
        return distance < self.best_distance_in_iteration

    def _update_pheromones(self):
        """Updates the pheromone trails."""
        raise NotImplementedError("This method should be implemented by subclasses.")


class ACS_DIST(ACS):
    """Implements the ACS-DIST algorithm (Algorithm 4)."""
    def __init__(self, graph: EvrptwGraph, params: dict, local_search):
        super().__init__(graph, params)
        self.local_search = local_search
        self.target_vehicles = params.get('target_vehicles', graph.vehicles)

    def _create_ants(self):
        self.ants = [ACS_DIST_Ant(self.graph, i, self.params) for i in range(self.num_ants)]

    def _get_target_vehicles(self):
        """ACS-DIST uses current number of vehicles (m)."""
        return self.target_vehicles

    def _construct_solutions(self):
        """Override to apply local search after construction for each ant."""
        for ant in self.ants:
            ant.target_vehicles = self._get_target_vehicles()
            path, distance = ant.construct_solution()

            if path and len(path) > 2:
                # Apply local search to each ant's solution as per Algorithm 4
                if self.local_search:
                    # Run a cheaper local search by limiting segment length
                    self.local_search.max_segment_len = self.params.get('ls_max_segment_len', 2)
                    self.local_search.verbose = self.params.get('ls_verbose', False)
                    path, distance = self.local_search.run(path, distance)

                ant.path = path
                ant.distance = distance

                if self._is_better_solution(path, distance):
                    self.best_distance_in_iteration = distance
                    self.best_solution_in_iteration = path[:]

    def _update_pheromones(self):
        """
        Algorithm 4: Global pheromone update for ACS-DIST.
        """
        self.graph.pheromone_mat *= (1 - self.rho)
        
        if self.best_solution_in_iteration:
            self.graph.global_update_pheromone(
                self.best_solution_in_iteration, 
                self.best_distance_in_iteration
            )

    def set_target_vehicles(self, num_vehicles):
        self.target_vehicles = num_vehicles

    def _is_better_solution(self, path, distance):
        """Accept only solutions that visit all customers; then compare by distance."""
        all_customers = {i for i, node in enumerate(self.graph.nodes) if node.is_customer()}
        visited_customers = {node_idx for node_idx in path if self.graph.nodes[node_idx].is_customer()}
        if len(visited_customers) != len(all_customers):
            return False
        return distance < self.best_distance_in_iteration


class ACS_VEI(ACS):
    """Implements the ACS-VEI algorithm (Algorithm 3)."""
    def __init__(self, graph: EvrptwGraph, params: dict):
        super().__init__(graph, params)
        self.infeasibility_counters = {i: 0 for i, node in enumerate(graph.nodes) if node.is_customer()}
        self.target_vehicles = params.get('target_vehicles', graph.vehicles - 1)
        self.global_best_feasible = None

    def _create_ants(self):
        self.ants = [
            ACS_VEI_Ant(self.graph, i, self.params, self.infeasibility_counters) 
            for i in range(self.num_ants)
        ]

    def _get_target_vehicles(self):
        return self.target_vehicles

    def _is_better_solution(self, path, distance):
        all_customers = {i for i, node in enumerate(self.graph.nodes) if node.is_customer()}
        visited_customers = {node_idx for node_idx in path if self.graph.nodes[node_idx].is_customer()}
        is_feasible = (len(visited_customers) == len(all_customers))

        if not self.best_solution_in_iteration:
            return True

        best_visited_customers = {node_idx for node_idx in self.best_solution_in_iteration if self.graph.nodes[node_idx].is_customer()}
        best_is_feasible = (len(best_visited_customers) == len(all_customers))

        num_vehicles = path.count(0) - 1
        best_num_vehicles = self.best_solution_in_iteration.count(0) - 1

        if is_feasible and not best_is_feasible:
            return True
        if not is_feasible and best_is_feasible:
            return False

        if is_feasible and best_is_feasible:
            # Prioritize fewer vehicles, then distance
            return num_vehicles < best_num_vehicles or (
                num_vehicles == best_num_vehicles and distance < self.best_distance_in_iteration
            )
        else:  # Both infeasible: prefer more customers served
            return len(visited_customers) > len(best_visited_customers)

    def run(self, T_best):
        """Runs one iteration, accepting the global best solution T_best."""
        self.best_solution_in_iteration = None
        self.best_distance_in_iteration = float('inf')
        self._create_ants()
        self._construct_solutions()
        self._update_pheromones(T_best)

    def _update_pheromones(self, T_best=None):
        """
        Algorithm 3: Global pheromone update for ACS-VEI.
        Updates based on the colony's best feasible solution (T_vei) and 
        the global best solution (T_best).
        """
        # Update infeasibility counters for unvisited customers
        all_customers = {i for i, node in enumerate(self.graph.nodes) if node.is_customer()}
        for ant in self.ants:
            if ant.path:
                visited_customers = {node_idx for node_idx in ant.path if self.graph.nodes[node_idx].is_customer()}
                unvisited = all_customers - visited_customers
                for customer_idx in unvisited:
                    self.infeasibility_counters[customer_idx] += 1

        # Check if a new best feasible solution was found in this iteration
        feasible_solution_found_this_iter = False
        if self.best_solution_in_iteration:
            visited_customers = {node_idx for node_idx in self.best_solution_in_iteration if self.graph.nodes[node_idx].is_customer()}
            if len(visited_customers) == len(all_customers):
                feasible_solution_found_this_iter = True

        # If a new feasible solution is found, reset counters and update colony's best (T_vei)
        if feasible_solution_found_this_iter:
            for customer_idx in self.infeasibility_counters:
                self.infeasibility_counters[customer_idx] = 0
            
            # Update the colony's best known feasible solution (T_vei)
            if not self.global_best_feasible or self.best_distance_in_iteration < self.global_best_feasible[1]:
                self.update_global_best_feasible(self.best_solution_in_iteration, self.best_distance_in_iteration)

        # --- Pheromone Update Logic --- #
        # 1. Evaporation
        self.graph.pheromone_mat *= (1 - self.rho)
        
        # 2. Global update for T_vei (colony's best feasible)
        if self.global_best_feasible:
            solution, distance = self.global_best_feasible
            self.graph.global_update_pheromone(solution, distance)

        # 3. Global update for T_best (overall best)
        if T_best:
            solution, distance, _ = T_best
            self.graph.global_update_pheromone(solution, distance)

    def set_target_vehicles(self, num_vehicles):
        self.target_vehicles = num_vehicles

    def update_global_best_feasible(self, solution, distance):
        self.global_best_feasible = (solution[:], distance)
