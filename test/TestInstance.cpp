#include "../include/Instance.h"
#include <iostream>

int main() {
    Instance instance;
    instance.parse_instance_file("../data/evrptw_instances/c101C5.txt");
    instance.print_summary();
    // std::cout << "Number of nodes: " << instance.get_nodes().size() << std::endl;
    // std::cout << "Number of arcs: " << instance.get_arcs().size() << std::endl;
    //
    // // Print all nodes
    // std::cout << "All nodes:" << std::endl;
    // for (const auto& node : instance.get_nodes()) {
    //     std::cout << node.to_string() << std::endl;
    // }
    //
    // // Print depot
    // const Node& depot = instance.get_depot();
    // std::cout << "==============================================================================================" << std::endl;
    // std::cout << "Depot: " << depot.to_string() << std::endl;
    //
    // // Print all customers
    // std::cout << "==============================================================================================" << std::endl;
    // std::cout << "Customers:" << std::endl;
    // for (const auto& customer : instance.get_customers()) {
    //     std::cout << customer.to_string() << std::endl;
    // }
    //
    // // Print all stations
    // std::cout << "==============================================================================================" << std::endl;
    // std::cout << "Stations:" << std::endl;
    // for (const auto& station : instance.get_stations()) {
    //     std::cout << station.to_string() << std::endl;
    // }
    //
    // // Print first 5 arcs
    // std::cout << "First 5 arcs:" << std::endl;
    // const auto& arcs = instance.get_arcs();
    // for (size_t i = 0; i < std::min<size_t>(5, arcs.size()); ++i) {
    //     std::cout << arcs[i].to_string() << std::endl;
    // }

    return 0;
}