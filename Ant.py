import numpy as np
from target import Node, Vehicle
from evrptw_config import EvrptwGraph

class Ant(Vehicle):
    def __init__(self, graph: EvrptwGraph, ant_id: int, params: dict):
        super().__init__(idx=ant_id, graph=graph)
        self.graph = graph
        self.id = ant_id
        self.params = params
        self.target_vehicles = float('inf')

        # Ant-specific state
        self.reset()

    def reset(self):
        """Resets the ant's state for a new solution construction."""
        self.current_node_idx = 0
        self.path = [0]
        self.path_distance = 0.0
        # Consider all customers; use positional indices in graph.nodes
        self.unvisited_nodes = {i for i, node in enumerate(self.graph.nodes) if node.is_customer()}
        self.vehicles_used = 1
        # Reset vehicle-specific state from parent
        self.current_load = 0.0
        self.current_battery = self.graph.tank_capacity
        self.current_time = 0.0

    def construct_solution(self):
        """
        Constructs a complete solution (route) for the ant based on Algorithm 2.
        """
        self.reset()

        while self.unvisited_nodes and self.vehicles_used <= self.target_vehicles:
            feasible_neighbors = self._get_feasible_neighbors()

            if not feasible_neighbors:
                if self.vehicles_used >= self.target_vehicles:
                    break 
                self._return_to_depot()
                self.vehicles_used += 1
                continue

            next_node_idx = self._select_next_node(feasible_neighbors)
            if next_node_idx is None:
                # Try to recharge at best station to unlock feasibility instead of immediately returning
                # Find a station that allows reaching at least one unvisited customer
                unlocked = False
                for station_idx, _ in sorted(
                    ((s, self.graph.node_dist_mat[self.current_node_idx][s]) for s, n in enumerate(self.graph.nodes) if n.is_station()),
                    key=lambda x: x[1]
                ):
                    fuel_to_station = self.graph.node_dist_mat[self.current_node_idx][station_idx] * self.graph.fuel_consumption_rate
                    if self.current_battery < fuel_to_station:
                        continue
                    # Move to station and fully recharge
                    self._move_to_station(station_idx, (self.graph.tank_capacity - (self.current_battery - fuel_to_station)) / self.graph.charging_rate if self.graph.charging_rate > 0 else 0)
                    feasible_neighbors = self._get_feasible_neighbors()
                    if feasible_neighbors:
                        unlocked = True
                        break
                if unlocked:
                    continue
                if self.vehicles_used >= self.target_vehicles:
                    break
                self._return_to_depot()
                self.vehicles_used += 1
                continue

            fuel_to_next = self.graph.node_dist_mat[self.current_node_idx][next_node_idx] * self.graph.fuel_consumption_rate
            
            if self.current_battery < fuel_to_next:
                recharge_success = self._go_to_charging_station(next_node_idx)
                if not recharge_success:
                    if self.vehicles_used >= self.target_vehicles:
                        break
                    self._return_to_depot()
                    self.vehicles_used += 1
                    continue

            self._move_to_node(next_node_idx)

        if self.unvisited_nodes:
            self._handle_unvisited_customers()

        # Ensure path ends at depot
        if self.path[-1] != 0:
            self._return_to_depot(final_return=True)

        # If still unvisited customers remain, mark as infeasible by clearing path
        if self.unvisited_nodes:
            # Infeasible solution: not all customers served
            return [], float('inf')

        return self.path, self.path_distance

    def _get_feasible_neighbors(self):
        """
        Identifies the set of unvisited customers that are feasible to visit next,
        including a lookahead for paths via charging stations.
        """
        feasible = {}
        for node_idx in self.unvisited_nodes:
            node = self.graph.nodes[node_idx]

            # 1. Capacity constraint
            if self.current_load + node.demand > self.graph.load_capacity + 1e-9:
                continue

            # 2. Direct travel feasibility (time and energy)
            distance_direct = self.graph.node_dist_mat[self.current_node_idx][node_idx]
            travel_time = distance_direct / self.graph.velocity
            arrival_time = self.current_time + travel_time
            service_start_time = max(arrival_time, node.ready_time)
            fuel_to_next = distance_direct * self.graph.fuel_consumption_rate

            if self.current_battery >= fuel_to_next and service_start_time <= node.due_date + 1e-9:
                feasible[node_idx] = self._calculate_heuristic_value(node_idx)
                continue

            # 3. Indirect feasibility via any charging station (try all stations)
            station_indices = [idx for idx, n in enumerate(self.graph.nodes) if n.is_station()]
            # Try closer stations first to reduce detour
            station_indices.sort(key=lambda s: self.graph.node_dist_mat[self.current_node_idx][s])

            for station_idx in station_indices:
                # Energy to reach station
                dist_to_station = self.graph.node_dist_mat[self.current_node_idx][station_idx]
                fuel_to_station = dist_to_station * self.graph.fuel_consumption_rate
                if self.current_battery < fuel_to_station:
                    continue

                # Time to reach and recharge at station
                station_node = self.graph.nodes[station_idx]
                time_to_station = dist_to_station / self.graph.velocity
                arrival_at_station = self.current_time + time_to_station
                if arrival_at_station > station_node.due_date + 1e-9:
                    continue
                wait_time_station = max(0.0, station_node.ready_time - arrival_at_station)
                needed_energy = self.graph.tank_capacity - (self.current_battery - fuel_to_station)
                charging_time = needed_energy / self.graph.charging_rate if self.graph.charging_rate > 0 else 0.0
                depart_station_time = arrival_at_station + wait_time_station + station_node.service_time + charging_time

                # From station to customer (must be possible with full tank)
                dist_station_to_node = self.graph.node_dist_mat[station_idx][node_idx]
                if dist_station_to_node * self.graph.fuel_consumption_rate > self.graph.tank_capacity + 1e-9:
                    continue
                time_station_to_node = dist_station_to_node / self.graph.velocity
                arrival_at_node = depart_station_time + time_station_to_node
                service_start_time = max(arrival_at_node, node.ready_time)
                if service_start_time <= node.due_date + 1e-9:
                    feasible[node_idx] = self._calculate_heuristic_value(node_idx)
                    break

        return feasible

    def _calculate_heuristic_value(self, node_idx_j):
        raise NotImplementedError("Heuristic calculation must be defined in a subclass.")

    def _select_next_node(self, feasible_neighbors: dict):
        if not feasible_neighbors:
            return None
            
        q = np.random.rand()
        
        if q <= self.params['q0']:
            best_node = -1
            max_value = -1
            for node_idx, eta in feasible_neighbors.items():
                tau = self.graph.pheromone_mat[self.current_node_idx][node_idx]
                value = (tau ** self.params['alpha']) * (eta ** self.params['beta'])
                if value > max_value:
                    max_value = value
                    best_node = node_idx
            return best_node
        else:
            probabilities = []
            nodes = list(feasible_neighbors.keys())
            total_prob_sum = 0

            for node_idx in nodes:
                eta = feasible_neighbors[node_idx]
                tau = self.graph.pheromone_mat[self.current_node_idx][node_idx]
                prob = (tau ** self.params['alpha']) * (eta ** self.params['beta'])
                probabilities.append(prob)
                total_prob_sum += prob
            
            if total_prob_sum == 0:
                return np.random.choice(nodes) if nodes else None

            probabilities = np.array(probabilities) / total_prob_sum
            return np.random.choice(nodes, p=probabilities)

    def _move_to_node(self, next_node_idx: int):
        distance = self.graph.node_dist_mat[self.current_node_idx][next_node_idx]
        travel_time = distance / self.graph.velocity
        
        node = self.graph.nodes[next_node_idx]
        
        arrival_time = self.current_time + travel_time
        wait_time = max(0, node.ready_time - arrival_time)
        self.current_time = arrival_time + wait_time + node.service_time
        self.current_battery -= distance * self.graph.fuel_consumption_rate
        if node.is_customer():
            self.current_load += node.demand

        self.path.append(next_node_idx)
        self.path_distance += distance
        self.unvisited_nodes.remove(next_node_idx)
        
        self._local_pheromone_update(self.current_node_idx, next_node_idx)
        self.current_node_idx = next_node_idx

    def _go_to_charging_station(self, target_node_idx: int):
        # Try stations in order of minimal detour distance i->s + s->target
        station_indices = [idx for idx, node in enumerate(self.graph.nodes) if node.is_station()]
        station_indices.sort(key=lambda s: self.graph.node_dist_mat[self.current_node_idx][s] + self.graph.node_dist_mat[s][target_node_idx])

        target_node = self.graph.nodes[target_node_idx]

        for station_idx in station_indices:
            fuel_to_station = self.graph.node_dist_mat[self.current_node_idx][station_idx] * self.graph.fuel_consumption_rate
            if self.current_battery < fuel_to_station:
                continue

            station_node = self.graph.nodes[station_idx]
            time_to_station = self.graph.node_dist_mat[self.current_node_idx][station_idx] / self.graph.velocity
            arrival_at_station = self.current_time + time_to_station
            if arrival_at_station > station_node.due_date:
                continue

            fuel_needed = self.graph.tank_capacity - (self.current_battery - fuel_to_station)
            charging_time = fuel_needed / self.graph.charging_rate if self.graph.charging_rate > 0 else float('inf')
            departure_from_station = max(arrival_at_station, station_node.ready_time) + station_node.service_time + charging_time

            time_station_to_target = self.graph.node_dist_mat[station_idx][target_node_idx] / self.graph.velocity
            arrival_at_target = departure_from_station + time_station_to_target
            if arrival_at_target > target_node.due_date:
                continue

            self._move_to_station(station_idx, charging_time)
            return True

        return False

    def _move_to_station(self, station_idx, charging_time):
        distance = self.graph.node_dist_mat[self.current_node_idx][station_idx]
        travel_time = distance / self.graph.velocity
        station_node = self.graph.nodes[station_idx]

        arrival_time = self.current_time + travel_time
        wait_time = max(0, station_node.ready_time - arrival_time)
        self.current_time = arrival_time + wait_time + station_node.service_time + charging_time
        self.current_battery = self.graph.tank_capacity

        self.path.append(station_idx)
        self.path_distance += distance
        self._local_pheromone_update(self.current_node_idx, station_idx)
        self.current_node_idx = station_idx

    def _return_to_depot(self, final_return=False):
        """Return to depot 0, inserting a charging station if energy is insufficient."""
        while True:
            distance_to_depot = self.graph.node_dist_mat[self.current_node_idx][0]
            fuel_needed = distance_to_depot * self.graph.fuel_consumption_rate
            if self.current_battery >= fuel_needed:
                # Move to depot with proper timing and battery updates
                depot_idx = 0
                distance = distance_to_depot
                travel_time = distance / self.graph.velocity
                depot_node = self.graph.nodes[depot_idx]
                arrival_time = self.current_time + travel_time
                wait_time = max(0, depot_node.ready_time - arrival_time)
                self.current_time = arrival_time + wait_time + depot_node.service_time
                self.current_battery -= distance * self.graph.fuel_consumption_rate
                self.path.append(depot_idx)
                self.path_distance += distance
                self._local_pheromone_update(self.current_node_idx, depot_idx)
                self.current_node_idx = depot_idx
                break
            # Try to recharge en-route
            recharge_success = self._go_to_charging_station(0)
            if not recharge_success:
                # If cannot reach any station or depot, append depot to terminate
                self.path.append(0)
                self.path_distance += distance_to_depot
                self._local_pheromone_update(self.current_node_idx, 0)
                self.current_node_idx = 0
                break

        if not final_return:
            # Reset vehicle state at depot for next route
            self.current_load = 0.0
            self.current_battery = self.graph.tank_capacity
            self.current_time = 0.0

    def _local_pheromone_update(self, i, j):
        xi = self.params['local_update_xi']
        tau_0 = self.graph.tau_0
        self.graph.pheromone_mat[i][j] = (1 - xi) * self.graph.pheromone_mat[i][j] + xi * tau_0

    # def _handle_unvisited_customers(self):
    #     """
    #     Inserts unvisited customers into the best feasible position in the current path.
    #     This is a greedy insertion heuristic as described in the paper.
    #     """
    #     from LocalSearch import LocalSearch # Use LocalSearch's feasibility check
    #     ls_checker = LocalSearch(self.graph)

    #     initial_unvisited_count = len(self.unvisited_nodes)
    #     print(f"[Ant {self.id}] Starting _handle_unvisited_customers. Unvisited: {list(self.unvisited_nodes)}")

    #     for customer_idx in list(self.unvisited_nodes):
    #         best_insertion_pos = -1
    #         min_cost_increase = float('inf')
            
    #         print(f"  [Ant {self.id}] Trying to insert customer {customer_idx}")
    #         # Find the best position to insert the customer
    #         for i in range(len(self.path) + 1): # +1 to allow insertion at the end
    #             # Create a temporary path with the customer inserted
    #             temp_path = self.path[:i] + [customer_idx] + self.path[i:]
                
    #             # Split into routes to check feasibility of the affected route
    #             routes = ls_checker._split_routes(temp_path)
                
    #             is_feasible = True
    #             for route in routes:
    #                 # Only check routes that contain the customer being inserted
    #                 if customer_idx in route or (i > 0 and route[-1] == self.path[i-1] and route[0] == self.path[i]): # Check affected routes
    #                     feasible_route, reason = ls_checker._check_feasible(route, return_reason=True)
    #                     if not feasible_route:
    #                         is_feasible = False
    #                         print(f"    [Ant {self.id}]   Route {route} with {customer_idx} at pos {i} is INFEASIBLE. Reason: {reason}")
    #                         break
                
    #             if is_feasible:
    #                 # Calculate cost increase
    #                 _, new_dist = ls_checker._merge_routes(routes)
    #                 cost_increase = new_dist - self.path_distance
                    
    #                 print(f"    [Ant {self.id}]   Route with {customer_idx} at pos {i} is FEASIBLE. Cost increase: {cost_increase:.2f}")

    #                 if cost_increase < min_cost_increase:
    #                     min_cost_increase = cost_increase
    #                     best_insertion_pos = i

    #         if best_insertion_pos != -1:
    #             # Insert the customer at the best found position
    #             self.path.insert(best_insertion_pos, customer_idx)
    #             self.unvisited_nodes.remove(customer_idx)
                
    #             # Recalculate the total distance of the updated path
    #             _, self.path_distance = ls_checker._merge_routes(ls_checker._split_routes(self.path))
    #             print(f"  [Ant {self.id}] Successfully inserted customer {customer_idx} at position {best_insertion_pos}. Current path: {self.path}")
    #         else:
    #             print(f"  [Ant {self.id}] Could not find a feasible insertion position for customer {customer_idx}.")
        
    #     print(f"[Ant {self.id}] Finished _handle_unvisited_customers. Remaining unvisited: {list(self.unvisited_nodes)}")
    #     if len(self.unvisited_nodes) < initial_unvisited_count:
    #         print(f"[Ant {self.id}] Successfully inserted {initial_unvisited_count - len(self.unvisited_nodes)} customers.")

    def _handle_unvisited_customers(self):
        """
        Inserts unvisited customers into the best feasible position in the current path.
        Uses repair-based feasibility (may add stations) when evaluating insertions.
        """
        from LocalSearch import LocalSearch  # Use LocalSearch's feasibility/repair
        ls_checker = LocalSearch(self.graph)

        # Ensure we have an accurate baseline distance for the current path
        base_routes = ls_checker._split_routes(self.path)
        _, base_distance = ls_checker._merge_routes(base_routes)

        initial_unvisited_count = len(self.unvisited_nodes)
        print(f"[Ant {self.id}] Starting _handle_unvisited_customers. Unvisited: {list(self.unvisited_nodes)}")

        for customer_idx in list(self.unvisited_nodes):
            print(f"  [Ant {self.id}] Trying to insert customer {customer_idx}")

            best_new_path = None
            best_new_distance = float('inf')

            # Try each possible insertion position (including end)
            for i in range(len(self.path) + 1):
                # Skip inserting directly between consecutive depots 0-0
                if i < len(self.path) - 1 and self.path[i] == 0 and self.path[i+1] == 0:
                    continue

                temp_path = self.path[:i] + [customer_idx] + self.path[i:]

                # Evaluate with repair: split -> repair each route if needed -> merge
                routes = ls_checker._split_routes(temp_path)
                repaired_routes = []
                feasible_all = True
                for r in routes:
                    ok, rr = ls_checker._check_and_repair(r)
                    if not ok:
                        feasible_all = False
                        break
                    repaired_routes.append(rr)
                if not feasible_all:
                    continue

                candidate_path, candidate_distance = ls_checker._merge_routes(repaired_routes)

                # Prefer minimal distance increase
                if candidate_distance < best_new_distance - 1e-9:
                    best_new_distance = candidate_distance
                    best_new_path = candidate_path

            # Apply best insertion if found
            if best_new_path is not None:
                self.path = best_new_path
                self.path_distance = best_new_distance
                self.unvisited_nodes.remove(customer_idx)
                print(f"    [Ant {self.id}] Inserted customer {customer_idx}. New distance: {self.path_distance:.2f}")
            else:
                print(f"    [Ant {self.id}] Could not find feasible position for customer {customer_idx}")

        print(f"[Ant {self.id}] Finished _handle_unvisited_customers. Remaining unvisited: {list(self.unvisited_nodes)}")
        if len(self.unvisited_nodes) < initial_unvisited_count:
            print(f"[Ant {self.id}] Successfully inserted {initial_unvisited_count - len(self.unvisited_nodes)} customers.")
class ACS_DIST_Ant(Ant):
    """Ant for the ACS-DIST algorithm, focusing on minimizing distance."""
    # def _calculate_heuristic_value(self, node_idx_j):
    #     """
    #     Calculates heuristic value eta for ACS-DIST (Equation 16).
    #     """
    #     node_j = self.graph.nodes[node_idx_j]
    #     travel_time = self.graph.node_dist_mat[self.current_node_idx][node_idx_j] / self.graph.velocity
    #     dt_j = max(self.current_time + travel_time, node_j.ready_time)
    #     ct_k = self.current_time
    #     l_j = node_j.due_date
        
    #     denominator = max(1, (dt_j - ct_k) * (l_j - ct_k))
    #     return 1.0 / denominator

    def _calculate_heuristic_value(self, node_idx_j):
        """
        Calculates heuristic value eta for ACS-DIST with energy consideration (Enhanced Equation 16).
        """
        node_j = self.graph.nodes[node_idx_j]
        dist = self.graph.node_dist_mat[self.current_node_idx][node_idx_j]
        travel_time = dist / self.graph.velocity
        
        # Time window component
        dt_j = max(self.current_time + travel_time, node_j.ready_time)
        ct_k = self.current_time
        l_j = node_j.due_date
        time_component = max(1, (dt_j - ct_k) * (l_j - ct_k))
        
        # Energy component
        energy_needed = dist * self.graph.fuel_consumption_rate
        energy_component = energy_needed / self.graph.tank_capacity
        
        # Combined heuristic
        denominator = time_component * (1 + energy_component)
        return 1.0 / denominator

class ACS_VEI_Ant(Ant):
    """Ant for the ACS-VEI algorithm, focusing on minimizing vehicle count."""
    def __init__(self, graph: EvrptwGraph, ant_id: int, params: dict, infeasibility_counters: dict):
        super().__init__(graph, ant_id, params)
        self.infeasibility_counters = infeasibility_counters

    def _calculate_heuristic_value(self, node_idx_j):
        """
        Calculates heuristic value eta for ACS-VEI (Equation 17).
        """
        node_j = self.graph.nodes[node_idx_j]
        travel_time = self.graph.node_dist_mat[self.current_node_idx][node_idx_j] / self.graph.velocity
        dt_j = max(self.current_time + travel_time, node_j.ready_time)
        ct_k = self.current_time
        l_j = node_j.due_date
        in_j = self.infeasibility_counters.get(node_idx_j, 0)
        
        denominator = max(1, (dt_j - ct_k) * (l_j - ct_k) - in_j)
        return 1.0 / denominator