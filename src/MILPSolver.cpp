#include "../include/MILPSolver.h"
#include <iostream>
#include <cmath>
#include <map>
#include <vector>
#include <string>
#include <sstream>

ILOSTLBEGIN


MILPSolver::MILPSolver(const Instance& inst, int max_vehicles, int max_station_visits)
    : SolverBase(inst), max_vehicles_(max_vehicles), max_station_visits_(max_station_visits),
      model_(env_), cplex_(model_) {

}

MILPSolver::~MILPSolver() {
    env_.end();
}

void MILPSolver::build_model() {

}

void MILPSolver::solve() {
    try {
        cplex_.setParam(IloCplex::Param::TimeLimit, 3600); // 1 hour time limit
        cplex_.setParam(IloCplex::Param::MIP::Tolerances::MIPGap, 0.01); // 1% MIP gap
        if (cplex_.solve()) {
            solution_status_ = cplex_.getCplexStatus();
            solution = std::make_unique<Solution>();
            solution->objective_value = cplex_.getObjValue();
            solution->num_vehicles = cplex_.getValue(num_vehicles_expr_);
            solution->total_distance = cplex_.getValue(total_distance_expr_);
            solution->total_time = cplex_.getValue(total_time_expr_);
            solution->computation_time = cplex_.getTime();
            solution->solver_used = "CPLEX";

            // Extract routes
            for (size_t i = 0; i < V_.size(); ++i) {
                std::vector<int> route;
                for (size_t j = 0; j < V_.size(); ++j) {
                    if (cplex_.getValue(x_[i][j]) > 0.5) {
                        route.push_back(V_[j]);
                    }
                }
                if (!route.empty()) {
                    solution->routes.push_back(route);
                }
            }

            // Extract charging details
            for (size_t i = 0; i < F_prime_.size(); ++i) {
                if (cplex_.getValue(z_[i]) > 0.5) {
                    int station_id = dummy_stations_[i].original_station_id;
                    solution->charging_details[station_id][F_prime_[i]] = cplex_.getValue(ch_[i]);
                }
            }
        } else {
            solution_status_ = cplex_.getCplexStatus();
            std::cout << "[MILPSolver] No feasible solution found.\n";
        }
    } catch (IloException& e) {
        std::cerr << "[MILPSolver] CPLEX Exception: " << e.getMessage() << std::endl;
    }
}

void MILPSolver::print_solution() const {
    if (!solution) {
        std::cout << "[MILPSolver] No solution available.\n";
        return;
    }
    std::cout << "[MILPSolver] Solution:\n";
    std::cout << "Objective Value: " << solution->objective_value << "\n";
    std::cout << "Number of Vehicles: " << solution->num_vehicles << "\n";
    std::cout << "Total Distance: " << solution->total_distance << "\n";
    std::cout << "Total Time: " << solution->total_time << "\n";
    std::cout << "Computation Time: " << solution->computation_time << " seconds\n";
    std::cout << "Routes:\n";
    for (size_t i = 0; i < solution->routes.size(); ++i) {
        std::cout << "Route " << i + 1 << ": ";
        for (int node : solution->routes[i]) {
            std::cout << node << " ";
        }
        std::cout << "\n";
    }
    std::cout << "Charging Details:\n";
    for (const auto& [station_id, details] : solution->charging_details) {
        for (const auto& [dummy_id, charge] : details) {
            std::cout << "Station " << station_id << " (" << dummy_id << "): " << charge << " units\n";
        }
    }
}

std::map<std::string, double> MILPSolver::get_node_data(const int& vertex_id) const {
    std::map<std::string, double> data;
    int original_id = get_original_node_id(vertex_id);
    for (const auto& node : instance.get_nodes()) {
        if (node.get_int_id() == original_id) {
            data["x"] = node.get_x();
            data["y"] = node.get_y();
            data["demand"] = node.get_demand();
            data["ready_time"] = node.get_ready_time();
            data["due_date"] = node.get_due_date();
            data["service_time"] = node.get_service_time();
            break;
        }
    }
    if (data.empty()) {
        std::cerr << "[Error] get_node_data: No node found for vertex_id: " << vertex_id
                  << " (original: " << original_id << ")\n";
        std::terminate();
    }
    return data;
}

int MILPSolver::get_original_node_id(const int& vertex_id) const {
    if (vertex_id == depot_start_ || vertex_id == depot_end_) {
        return instance.get_depot().get_int_id();
    }
    for (const auto& ds : dummy_stations_) {
        if (vertex_id == ds.dummy_id) {
            return ds.original_station_id;
        }
    }
    return vertex_id;
}

double MILPSolver::get_wireless_coverage(const int& i, const int& j) const {
    int from_id = get_original_node_id(i);
    int to_id = get_original_node_id(j);
    return instance.get_wireless_coverage(from_id, to_id);
}

double MILPSolver::calculate_distance_vertices(const int& v1, const int& v2) const {
    auto data1 = get_node_data(v1);
    auto data2 = get_node_data(v2);
    return std::sqrt(std::pow(data1["x"] - data2["x"], 2) + std::pow(data1["y"] - data2["y"], 2));
}

double MILPSolver::calculate_travel_time_vertices(const int& v1, const int& v2) const {
    return calculate_distance_vertices(v1, v2) / instance.get_average_speed();
}

double MILPSolver::calculate_wireless_charge(const int& i, const int& j) const {
    return instance.get_wireless_charge_rate() * calculate_distance_vertices(i, j) * get_wireless_coverage(i, j);
}

double MILPSolver::calculate_nonlinear_charging_time(double charge_amount) const {
    return instance.get_alpha() * std::pow(charge_amount, instance.get_beta()) + instance.get_inverse_refueling_rate() * charge_amount;
}

double MILPSolver::get_load_dependent_consumption(double distance, double load_ratio) const {
    return instance.get_consumption_rate() * distance * (1 + instance.get_load_factor() * load_ratio);
}