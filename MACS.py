from evrptw_config import EvrptwGraph
from ACS import ACS_DIST, ACS_VEI
from LocalSearch import LocalSearch

class MACS:
    def __init__(self, instance_path: str, config: dict):
        self.config = config
        self.graph = EvrptwGraph(instance_path, rho=config.get('global_update_rho', 0.1))
        
        self.T_best = (self.graph.nnh_travel_path, self.graph.Cnn, self.graph.vehicles)
        self.fixed_vehicles = self.config.get('fixed_vehicles', None)
        self.m = self.fixed_vehicles if self.fixed_vehicles is not None else self.T_best[2]

        self.local_search = LocalSearch(self.graph)

        dist_params = self.config.get('acs_dist', {})
        # Ensure consistent rho across evaporation and deposition
        dist_params['rho'] = self.config.get('global_update_rho', 0.1)
        dist_params['local_update_xi'] = self.config.get('local_update_xi', 0.1)
        self.acs_dist = ACS_DIST(self.graph, dist_params, self.local_search)

        vei_params = self.config.get('acs_vei', {})
        vei_params['rho'] = self.config.get('global_update_rho', 0.1)
        vei_params['local_update_xi'] = self.config.get('local_update_xi', 0.1)
        self.acs_vei = ACS_VEI(self.graph, vei_params)

    # def run(self):
    #     """
    #     Executes the main MACS loop (Algorithm 1).
    #     """
    #     print(f"Starting MACS with initial solution: {self.m} vehicles, distance {self.T_best[1]:.2f}")

    #     max_iterations = self.config.get('max_iterations', 100)
    #     for i in range(max_iterations):
    #         print(f"\n--- Outer Iteration {i+1}/{max_iterations} ---")
            
    #         # Set vehicle targets (fixed if provided)
    #         target_v = self.fixed_vehicles if self.fixed_vehicles is not None else self.m
    #         self.acs_dist.set_target_vehicles(target_v)
    #         self.acs_vei.set_target_vehicles(target_v)

    #         # Inner loop for optimization (lines 6-19 of Algorithm 1)
    #         inner_iterations = self.config.get('inner_iterations', 10) # Example value
    #         for j in range(inner_iterations):
    #             # Run both colonies
    #             self.acs_dist.run()
    #             self.acs_vei.run(self.T_best)

    #             # Update T_best based on ACS-DIST's findings (prioritize fewer vehicles, then distance)
    #             T_dist_path = self.acs_dist.best_solution_in_iteration
    #             if T_dist_path:
    #                 if self._path_is_fully_feasible(T_dist_path):
    #                     T_dist_distance = self.acs_dist.best_distance_in_iteration
    #                     num_vehicles_dist = T_dist_path.count(0) - 1
    #                     cur_nv = self.T_best[2]
    #                     cur_dist = self.T_best[1]
    #                     if (num_vehicles_dist < cur_nv) or (num_vehicles_dist == cur_nv and T_dist_distance < cur_dist - 1e-9):
    #                         self.T_best = (T_dist_path, T_dist_distance, num_vehicles_dist)
    #                         self.m = num_vehicles_dist
    #                         # Update targets immediately to encourage fewer vehicles
    #                         self.acs_dist.set_target_vehicles(self.m)
    #                         self.acs_vei.set_target_vehicles(self.m)
    #                         print(f"New global best from ACS-DIST: {self.T_best[2]} vehicles, distance {self.T_best[1]:.2f}")

    #             # Update T_best based on ACS-VEI's findings (prioritize fewer vehicles, then distance)
    #             T_vei_path = self.acs_vei.best_solution_in_iteration
    #             if T_vei_path:
    #                 if self._path_is_fully_feasible(T_vei_path):
    #                     T_vei_distance = self.acs_vei.best_distance_in_iteration
    #                     num_vehicles_vei = T_vei_path.count(0) - 1
    #                     cur_nv = self.T_best[2]
    #                     cur_dist = self.T_best[1]
    #                     if (num_vehicles_vei < cur_nv) or (num_vehicles_vei == cur_nv and T_vei_distance < cur_dist - 1e-9):
    #                         self.T_best = (T_vei_path, T_vei_distance, num_vehicles_vei)
    #                         self.m = num_vehicles_vei
    #                         # Encourage fewer vehicles immediately
    #                         self.acs_dist.set_target_vehicles(self.m)
    #                         self.acs_vei.set_target_vehicles(self.m)
    #                         print(f"New global best from ACS-VEI: {self.T_best[2]} vehicles, distance {self.T_best[1]:.2f}")

    #             # No special re-run on fewer vehicles; focus on distance only
            
    #         # Optional: Add a condition to break the outer loop if no improvement
    #         # if no_improvement_for_x_iterations: break

    #     # Final feasibility repair/validation
    #     self.T_best = self._ensure_feasible(self.T_best)

    #     # If still infeasible, try building a trivial multi-vehicle feasible solution
    #     final_path = self.T_best[0]
    #     if not final_path or not self._path_is_fully_feasible(final_path):
    #         fallback_path, fallback_dist, fallback_nv = self._build_trivial_feasible_solution()
    #         if fallback_path and self._path_is_fully_feasible(fallback_path):
    #             self.T_best = (fallback_path, fallback_dist, fallback_nv)
    #         else:
    #             print("\n--- MACS Finished ---")
    #             print("No feasible solution found that satisfies all time windows and constraints.")
    #             return ([], float('inf'), float('inf'))

    #     print("\n--- MACS Finished ---")
    #     print(f"Final Best Solution: {self.T_best[2]} vehicles, distance {self.T_best[1]:.2f}")
    #     return self.T_best

    
    def _objective_score(self, num_vehicles, distance):
        """Calculate weighted objective score prioritizing number of vehicles."""
        w1, w2 = self.config.get('objective_weights', (0.9, 0.1))  # Prioritize vehicles
        return w1 * num_vehicles + w2 * distance

    def run(self):
        """
        Executes the main MACS loop (Algorithm 1), prioritizing fewer vehicles over distance.
        """
        print(f"Starting MACS with initial solution: {self.m} vehicles, distance {self.T_best[1]:.2f}")
        
        max_iterations = self.config.get('max_iterations', 100)
        max_vehicles = len([n for n in self.graph.nodes if n.is_customer()])  # Max possible vehicles
        best_score = self._objective_score(self.T_best[2], self.T_best[1])
        no_improvement_count = 0
        max_no_improvement = 50  # Early stopping threshold

        for i in range(max_iterations):
            print(f"\n--- Outer Iteration {i+1}/{max_iterations} ---")
            
            # Try vehicle counts from 1 (or m-1) up to current m to prioritize fewer vehicles
            min_vehicles = max(1, self.m - 1)
            for target_v in range(min_vehicles, self.m + 1):
                # Set vehicle targets (fixed if provided, else try target_v)
                target_vehicles = self.fixed_vehicles if self.fixed_vehicles is not None else target_v
                self.acs_dist.set_target_vehicles(target_vehicles)
                self.acs_vei.set_target_vehicles(max(1, target_vehicles - 1))  # ACS-VEI tries to reduce vehicles
                
                inner_iterations = self.config.get('inner_iterations', 5)
                for j in range(inner_iterations):
                    # Run both colonies
                    self.acs_dist.run()
                    self.acs_vei.run(self.T_best)

                    # Update T_best based on ACS-DIST's findings (prioritize fewer vehicles)
                    T_dist_path = self.acs_dist.best_solution_in_iteration
                    if T_dist_path and self._path_is_fully_feasible(T_dist_path):
                        T_dist_distance = self.acs_dist.best_distance_in_iteration
                        num_vehicles_dist = T_dist_path.count(0) - 1
                        curr_score = self._objective_score(num_vehicles_dist, T_dist_distance)
                        if curr_score < best_score - 1e-9:
                            self.T_best = (T_dist_path, T_dist_distance, num_vehicles_dist)
                            best_score = curr_score
                            self.m = num_vehicles_dist
                            no_improvement_count = 0
                            # Reset pheromone to focus on new best solution
                            self.graph.pheromone_mat.fill(self.graph.tau_0)
                            self.graph.global_update_pheromone(T_dist_path, T_dist_distance)
                            print(f"New global best from ACS-DIST: {self.T_best[2]} vehicles, distance {self.T_best[1]:.2f}")
                            # Update targets to encourage fewer vehicles
                            self.acs_dist.set_target_vehicles(self.m)
                            self.acs_vei.set_target_vehicles(max(1, self.m - 1))

                    # Update T_best based on ACS-VEI's findings (prioritize fewer vehicles)
                    T_vei_path = self.acs_vei.best_solution_in_iteration
                    if T_vei_path and self._path_is_fully_feasible(T_vei_path):
                        T_vei_distance = self.acs_vei.best_distance_in_iteration
                        num_vehicles_vei = T_vei_path.count(0) - 1
                        curr_score = self._objective_score(num_vehicles_vei, T_vei_distance)
                        if curr_score < best_score - 1e-9:
                            self.T_best = (T_vei_path, T_vei_distance, num_vehicles_vei)
                            best_score = curr_score
                            self.m = num_vehicles_vei
                            no_improvement_count = 0
                            # Reset pheromone to focus on new best solution
                            self.graph.pheromone_mat.fill(self.graph.tau_0)
                            self.graph.global_update_pheromone(T_vei_path, T_vei_distance)
                            print(f"New global best from ACS-VEI: {self.T_best[2]} vehicles, distance {self.T_best[1]:.2f}")
                            # Update targets to encourage fewer vehicles
                            self.acs_dist.set_target_vehicles(self.m)
                            self.acs_vei.set_target_vehicles(max(1, self.m - 1))
                
                # Early stopping if no improvement in vehicle count
                no_improvement_count += 1
                if no_improvement_count >= max_no_improvement:
                    print("Early stopping due to no improvement in vehicle count.")
                    break
            
            if no_improvement_count >= max_no_improvement:
                break

        # Final feasibility repair/validation
        self.T_best = self._ensure_feasible(self.T_best)

        # If still infeasible, try building a trivial multi-vehicle feasible solution
        final_path = self.T_best[0]
        if not final_path or not self._path_is_fully_feasible(final_path):
            fallback_path, fallback_dist, fallback_nv = self._build_trivial_feasible_solution()
            if fallback_path and self._path_is_fully_feasible(fallback_path):
                self.T_best = (fallback_path, fallback_dist, fallback_nv)
            else:
                print("\n--- MACS Finished ---")
                print("No feasible solution found that satisfies all time windows and constraints.")
                return ([], float('inf'), float('inf'))

        print("\n--- MACS Finished ---")
        print(f"Final Best Solution: {self.T_best[2]} vehicles, distance {self.T_best[1]:.2f}")
        return self.T_best

    
    def _path_is_fully_feasible(self, path: list) -> bool:
        routes = self.local_search._split_routes(path)
        for r in routes:
            ok = self.local_search._check_feasible(r)
            if not ok:
                return False
        # ensure all customers served exactly once
        all_customers = {i for i, node in enumerate(self.graph.nodes) if node.is_customer()}
        visited_customers = [idx for idx in path if self.graph.nodes[idx].is_customer()]
        if len(visited_customers) != len(all_customers):
            return False
        # uniqueness
        counts = {}
        for cid in visited_customers:
            counts[cid] = counts.get(cid, 0) + 1
            if counts[cid] > 1:
                return False
        return True

    def _ensure_feasible(self, t_best: tuple) -> tuple:
        path, dist, nv = t_best
        routes = self.local_search._split_routes(path)
        repaired_routes = []
        for r in routes:
            ok, rr = self.local_search._check_and_repair(r)
            if not ok:
                # if still infeasible, keep original to avoid crashing
                repaired_routes.append(r)
            else:
                repaired_routes.append(rr)
        new_path, new_dist = self.local_search._merge_routes(repaired_routes)
        new_nv = new_path.count(0) - 1 if new_path else nv
        return (new_path, new_dist, new_nv)

    def _build_trivial_feasible_solution(self) -> tuple:
        """
        Build a simple feasible solution by assigning each customer to its own route [0, c, 0],
        repairing for energy via stations if needed. This maximizes vehicles but guarantees feasibility
        if individual customers are serviceable within their time windows.
        """
        customers = [i for i, node in enumerate(self.graph.nodes) if node.is_customer()]
        # Sort by ready time to reduce time-window conflicts per route
        customers.sort(key=lambda c: self.graph.nodes[c].ready_time)

        repaired_routes = []
        for c in customers:
            route = [0, c, 0]
            ok, rr = self.local_search._check_and_repair(route)
            if not ok:
                # If even single-customer route is infeasible (e.g., time window impossible), skip
                # This indicates overall infeasibility under given data
                return ([], float('inf'), float('inf'))
            repaired_routes.append(rr)
        # After building single-customer routes, attempt to merge them greedily
        merged_routes = self.local_search.try_merge_routes(repaired_routes)
        new_path, new_dist = self.local_search._merge_routes(merged_routes)
        new_nv = new_path.count(0) - 1 if new_path else 0
        return (new_path, new_dist, new_nv)