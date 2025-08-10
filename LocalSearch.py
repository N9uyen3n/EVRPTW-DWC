from copy import deepcopy

class LocalSearch:
    def __init__(self, graph, verbose: bool = False, max_segment_len: int = 2):
        self.graph = graph
        self.verbose = verbose
        self.max_segment_len = max(1, int(max_segment_len))

    def _route_distance(self, route):
        distance = 0.0
        for i in range(len(route)-1):
            distance += self.graph.node_dist_mat[route[i]][route[i+1]]
        return distance

    def _routes_total_distance(self, routes):
        return sum(self._route_distance(r) for r in routes if r)

    def try_merge_routes(self, routes):
        """
        Attempt to merge routes to reduce the number of vehicles.
        Preference: fewer routes first; if tied, smaller total distance.
        """
        improved = True
        current_routes = [r[:] for r in routes if r]
        while improved:
            improved = False
            best_merge = None
            best_result_routes = None
            best_distance = float('inf')
            base_num_routes = len(current_routes)

            for a in range(len(current_routes)):
                for b in range(a+1, len(current_routes)):
                    r_a = current_routes[a]
                    r_b = current_routes[b]
                    if len(r_a) <= 2 or len(r_b) <= 2:
                        continue
                    merged = [0] + r_a[1:-1] + r_b[1:-1] + [0]
                    ok, repaired = self._check_and_repair(merged)
                    if not ok:
                        continue
                    candidate_routes = []
                    for k in range(len(current_routes)):
                        if k == a or k == b:
                            continue
                        candidate_routes.append(current_routes[k])
                    candidate_routes.append(repaired)
                    candidate_num_routes = len(candidate_routes)
                    candidate_distance = self._routes_total_distance(candidate_routes)
                    if candidate_num_routes < base_num_routes or (
                        candidate_num_routes == base_num_routes and candidate_distance + 1e-9 < best_distance
                    ):
                        best_merge = (a, b)
                        best_result_routes = candidate_routes
                        best_distance = candidate_distance

            if best_result_routes is not None:
                current_routes = best_result_routes
                improved = True

        return current_routes

    def try_relocate_segments(self, routes):
        """
        Try relocating short segments (length 1..max_segment_len) between routes (and within a route)
        to reduce number of routes or distance. Returns improved routes if found, else original.
        """
        improved = True
        current_routes = [r[:] for r in routes if r]
        while improved:
            improved = False
            best_candidate = None
            best_routes = None
            base_num_routes = len(current_routes)
            base_distance = self._routes_total_distance(current_routes)

            for a in range(len(current_routes)):
                r_a = current_routes[a]
                if len(r_a) <= 2:
                    continue
                # segment within r_a excluding depots
                for start_a in range(1, len(r_a)-1):
                    for end_a in range(start_a, min(len(r_a)-2, start_a + self.max_segment_len - 1)):
                        seg = r_a[start_a:end_a+1]
                        r_a_removed = r_a[:start_a] + r_a[end_a+1:]
                        # Ensure route remains at least [0,0]
                        if len(r_a_removed) < 2:
                            r_a_removed = [0, 0]

                        for b in range(len(current_routes)):
                            r_b = current_routes[b]
                            # insertion positions in r_b between depots
                            for pos in range(1, len(r_b)):
                                candidate_routes = []
                                for k in range(len(current_routes)):
                                    if k == a and k == b:
                                        continue
                                    if k == a:
                                        continue
                                    if k == b:
                                        continue
                                    candidate_routes.append(current_routes[k])

                                # Build new versions of r_a and r_b
                                new_r_a = r_a_removed
                                new_r_b = r_b[:pos] + seg + r_b[pos:]

                                feasible_a, repaired_a = self._check_and_repair(new_r_a)
                                if not feasible_a:
                                    continue
                                feasible_b, repaired_b = self._check_and_repair(new_r_b)
                                if not feasible_b:
                                    continue

                                candidate_routes_full = candidate_routes[:]
                                # Only add repaired routes if non-trivial
                                if len(repaired_a) > 2:
                                    candidate_routes_full.append(repaired_a)
                                if len(repaired_b) > 2:
                                    candidate_routes_full.append(repaired_b)
                                if not candidate_routes_full:
                                    candidate_routes_full = [[0, 0]]

                                candidate_num_routes = len(candidate_routes_full)
                                candidate_distance = self._routes_total_distance(candidate_routes_full)

                                better = False
                                if candidate_num_routes < base_num_routes:
                                    better = True
                                elif candidate_num_routes == base_num_routes and candidate_distance + 1e-9 < base_distance:
                                    better = True

                                if better:
                                    best_candidate = (a, b, start_a, end_a, pos)
                                    best_routes = candidate_routes_full
                                    base_distance = candidate_distance
                                    base_num_routes = candidate_num_routes
                                    improved = True

            if improved and best_routes is not None:
                current_routes = best_routes

        return current_routes

    def run(self, solution, distance):
        """
        CROSS-exchange local search implementation with station repair.
        """
        best_solution = solution[:]
        best_distance = distance

        routes = self._split_routes(best_solution)
        # Try route merging and relocation first to reduce vehicles
        merged_once = self.try_merge_routes(routes)
        relocated_once = self.try_relocate_segments(merged_once)
        merged_solution, merged_distance = self._merge_routes(merged_once)
        relocated_solution, relocated_distance = self._merge_routes(relocated_once)
        # Prefer relocated result if better in vehicles or distance
        if relocated_solution:
            merged_solution = relocated_solution
            merged_distance = relocated_distance
        if merged_solution:
            # Accept merge even if distance is not better, to enable subsequent improvements
            best_solution = merged_solution
            best_distance = merged_distance
            routes = self._split_routes(best_solution)

        improved = True
        while improved:
            improved = False
            num_routes = len(routes)
            for a in range(num_routes):
                for b in range(a, num_routes):
                    r_a = routes[a]
                    r_b = routes[b]
                    if len(r_a) <= 2 and len(r_b) <= 2:
                        continue

                    for start_a in range(1, max(1, len(r_a)-1)):
                        for end_a in range(start_a, len(r_a)-1):
                            seg_a = r_a[start_a:end_a+1]
                            if len(seg_a) > self.max_segment_len:
                                continue

                            for start_b in range(1, max(1, len(r_b)-1)):
                                for end_b in range(start_b, len(r_b)-1):
                                    seg_b = r_b[start_b:end_b+1]
                                    if len(seg_b) > self.max_segment_len:
                                        continue

                                    new_r_a = r_a[:start_a] + seg_b + r_a[end_a+1:]
                                    new_r_b = r_b[:start_b] + seg_a + r_b[end_b+1:]

                                    feasible_a, repaired_a = self._check_and_repair(new_r_a)
                                    if not feasible_a:
                                        continue
                                    
                                    feasible_b, repaired_b = self._check_and_repair(new_r_b)
                                    if not feasible_b:
                                        continue

                                    new_routes = routes.copy()
                                    new_routes[a] = repaired_a
                                    new_routes[b] = repaired_b

                                    new_solution, new_distance = self._merge_routes(new_routes)

                                    if new_distance + 1e-8 < best_distance:
                                        best_distance = new_distance
                                        best_solution = new_solution
                                        routes = self._split_routes(best_solution)
                                        improved = True
                                        break
                                if improved: break
                            if improved: break
                        if improved: break
                    if improved: break
                if improved: break
        # Final merge/relocate attempt after local exchanges
        final_routes = self.try_merge_routes(self._split_routes(best_solution))
        final_routes = self.try_relocate_segments(final_routes)
        final_solution, final_distance = self._merge_routes(final_routes)
        # Prefer fewer vehicles, then distance
        best_nv = best_solution.count(0) - 1
        final_nv = final_solution.count(0) - 1
        if final_nv < best_nv or (final_nv == best_nv and final_distance + 1e-9 < best_distance):
            best_solution, best_distance = final_solution, final_distance
        return best_solution, best_distance

    def _check_and_repair(self, route):
        """Checks feasibility and attempts repair if it's an energy issue."""
        is_feasible, reason = self._check_feasible(route, return_reason=True)
        if is_feasible:
            return True, route
        if reason == 'ENERGY':
            repaired_route = self._repair_route_with_stations(route)
            is_repaired_feasible, _ = self._check_feasible(repaired_route, return_reason=True)
            return is_repaired_feasible, repaired_route
        return False, route

    def _repair_route_with_stations(self, route):
        """Repairs a route by adding/removing charging stations (stationInRe operator)."""
        repaired_route = [0]
        current_load = 0.0
        current_battery = self.graph.tank_capacity
        current_time = 0.0
        
        nodes_to_visit = route[1:-1]

        for i, node_idx in enumerate(nodes_to_visit):
            node = self.graph.nodes[node_idx]
            
            # Calculate travel to next node
            dist_to_next = self.graph.node_dist_mat[repaired_route[-1]][node_idx]
            fuel_needed_to_next = dist_to_next * self.graph.fuel_consumption_rate

            # Check if recharge is needed
            if current_battery < fuel_needed_to_next:
                best_station_idx, _ = self.graph.select_closest_station(repaired_route[-1], node_idx)
                if best_station_idx != -1:
                    # Simulate going to station
                    dist_to_station = self.graph.node_dist_mat[repaired_route[-1]][best_station_idx]
                    travel_time_to_station = dist_to_station / self.graph.velocity
                    
                    # Check if we can reach the station
                    if current_battery >= dist_to_station * self.graph.fuel_consumption_rate:
                        repaired_route.append(best_station_idx)
                        station_node = self.graph.nodes[best_station_idx]

                        # Update state after reaching station (consume battery to reach station, then charge)
                        arrival_at_station = current_time + travel_time_to_station
                        wait_time_at_station = max(0, station_node.ready_time - arrival_at_station)
                        battery_used_to_station = dist_to_station * self.graph.fuel_consumption_rate
                        current_battery -= battery_used_to_station
                        needed_energy = self.graph.tank_capacity - current_battery
                        charging_time = (
                            needed_energy / self.graph.charging_rate if self.graph.charging_rate > 0 else 0.0
                        )
                        current_time = arrival_at_station + wait_time_at_station + station_node.service_time + charging_time
                        current_battery = self.graph.tank_capacity # Full recharge

            # Move to the actual node
            repaired_route.append(node_idx)
            
            # Update state after reaching current node
            dist = self.graph.node_dist_mat[repaired_route[-2]][node_idx] # Distance from previous node in repaired_route
            travel_time = dist / self.graph.velocity
            arrival_time = current_time + travel_time
            wait_time = max(0, node.ready_time - arrival_time)
            current_time = arrival_time + wait_time + node.service_time
            current_battery -= dist * self.graph.fuel_consumption_rate
            current_load += node.demand

        repaired_route.append(0)
        return repaired_route

    def _check_feasible(self, route, return_reason=False):
        """
        Check feasibility of a single route.
        """
        current_load = 0.0
        current_battery = self.graph.tank_capacity
        current_time = 0.0

        if not route or route[0] != 0:
            if self.verbose:
                print(f"[Feasibility Check] Route {route}: FORMAT error (starts not with depot or empty).")
            return (False, 'FORMAT') if return_reason else False

        for idx in range(len(route)-1):
            cur = route[idx]
            nxt = route[idx+1]
            node_nxt = self.graph.nodes[nxt]

            dist = self.graph.node_dist_mat[cur][nxt]
            battery_usage = dist * self.graph.fuel_consumption_rate

            # Enforce strictly positive battery after traversal
            if current_battery - battery_usage <= 1e-9:
                if self.verbose:
                    print(f"[Feasibility Check] Route {route}: ENERGY violation from {cur} to {nxt}. Battery: {current_battery:.2f}, Needed: {battery_usage:.2f}")
                return (False, 'ENERGY') if return_reason else False

            travel_time = dist / self.graph.velocity
            current_time += travel_time
            current_battery -= battery_usage

            if node_nxt.is_customer():
                if current_load + node_nxt.demand > self.graph.load_capacity + 1e-9:
                    if self.verbose:
                        print(f"[Feasibility Check] Route {route}: CAPACITY violation at {nxt}. Current load: {current_load:.2f}, Demand: {node_nxt.demand:.2f}, Capacity: {self.graph.load_capacity:.2f}")
                    return (False, 'CAPACITY') if return_reason else False
                current_load += node_nxt.demand

                service_start_time = max(current_time, node_nxt.ready_time)
                
                # Time-window: service must start within [ready, due]
                if service_start_time > node_nxt.due_date + 1e-9:
                    if self.verbose:
                        print(f"[Feasibility Check] Route {route}: TIME WINDOW violation at {nxt}. Arrival: {current_time:.2f}, Ready: {node_nxt.ready_time:.2f}, Due: {node_nxt.due_date:.2f}")
                    return (False, 'TIME') if return_reason else False

                current_time = service_start_time + node_nxt.service_time

            elif node_nxt.is_station():
                # Recharge to full and include charging time needed
                needed_energy = self.graph.tank_capacity - current_battery
                charging_time = (
                    needed_energy / self.graph.charging_rate if self.graph.charging_rate > 0 else 0.0
                )
                current_time = max(current_time, node_nxt.ready_time) + node_nxt.service_time + charging_time
                current_battery = self.graph.tank_capacity

            elif node_nxt.is_depot():
                # Arrival at depot must respect depot due time as well
                if current_time > node_nxt.due_date + 1e-9:
                    if self.verbose:
                        print(f"[Feasibility Check] Route {route}: TIME WINDOW violation at depot {nxt}. Arrival: {current_time:.2f}, Due: {node_nxt.due_date:.2f}")
                    return (False, 'TIME') if return_reason else False
                # Reset for next route
                current_load = 0.0
                current_battery = self.graph.tank_capacity
                current_time = max(current_time, node_nxt.ready_time)

        if route[-1] != 0:
            if self.verbose:
                print(f"[Feasibility Check] Route {route}: FORMAT error (ends not with depot).")
            return (False, 'FORMAT') if return_reason else False

        if self.verbose:
            print(f"[Feasibility Check] Route {route}: FEASIBLE.")
        return (True, None) if return_reason else True

    def _split_routes(self, path):
        """
        Convert full path (list) into list of routes (each route ends with depot 0).
        """
        routes = []
        route = []
        for node in path:
            route.append(node)
            if node == 0 and len(route) > 1:
                routes.append(route)
                route = [0]
        if route and route != [0]:
            if route[0] != 0:
                route = [0] + route
            if route[-1] != 0:
                route.append(0)
            routes.append(route)
        return routes

    def _merge_routes(self, routes):
        """
        Convert list of routes back to solution path (list) and compute total distance.
        """
        solution = []
        total_dist = 0.0
        for r in routes:
            if not r: continue
            if r[0] != 0:
                r = [0] + r
            solution.extend(r[:-1])
            for i in range(len(r)-1):
                total_dist += self.graph.node_dist_mat[r[i]][r[i+1]]
        if solution and solution[-1] != 0:
            solution.append(0)
        elif not solution:
            solution = [0]
        return solution, total_dist
""