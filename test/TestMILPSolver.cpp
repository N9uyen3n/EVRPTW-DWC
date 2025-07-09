// test/TestMILPSolver.cpp

#include "../include/Instance.h"
#include "../include/MILPSolver.h"
#include "../include/SolverBase.h"
#include <iostream>
#include <chrono>

void test_enhanced_features() {
    std::string instance_file = "../data/evrptw_instances/c101_21.txt";
    Instance instance;
    instance.parse_instance_file(instance_file);
    //
    //
    // // Set enhanced parameters
    // instance.set_wireless_charge_rate(0.9);
    // instance.set_load_factor(0.3); // 30% load dependency
    // instance.set_alpha(2.0);       // Non-linear charging parameter
    // instance.set_beta(0.5);        // Square root charging
    // instance.set_wireless_coverage("light"); // 20% coverage
    //
    // instance.print_summary();
    //
    // MILPSolver solver(instance, 4, 2);
    //
    // auto start = std::chrono::steady_clock::now();
    // solver.build_model();
    // solver.solve();
    // auto end = std::chrono::steady_clock::now();
    // double solve_time = std::chrono::duration<double>(end - start).count();
    //
    // if (solver.solution) {
    //     std::cout << " SOLVED\n";
    //     std::cout << "Objective: " << solver.solution->objective_value << "\n";
    //     std::cout << "Vehicles: " << solver.solution->num_vehicles << "\n";
    //     std::cout << "Distance: " << solver.solution->total_distance << "\n";
    //     std::cout << "Time: " << solver.solution->total_time << "\n";
    //     std::cout << "Solve Time: " << solve_time << "s\n";
    //     solver.print_solution();
    // } else {
    //     std::cout << " No solution found\n";
    // }
}

int main() {
    test_enhanced_features();
    return 0;
}