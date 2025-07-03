//
// Created by ASUS on 01/07/2025.
//

#include "../include/Instance.h"
#include "../include/Node.h"
#include "../include/Arc.h"
#include <fstream>
#include <sstream>
#include <regex>
#include <iostream>
#include <iomanip>

std::unique_ptr<InstanceSolution> solution;


void Instance::parse_instance_file(const std::string& filename) {
    std::ifstream file(filename);
    std::string line;
    bool parsing_nodes = true;
    std::regex value_regex("/([0-9.]+)/");

    std::vector<Node> all_nodes;
    std::vector<Node> customers_vec;
    std::vector<Node> stations_vec;
    Node depot_node;

    while (std::getline(file, line)) {
        if (line.empty()) continue;
        if (line.rfind("Q ", 0) == 0) {
            parsing_nodes = false;
            std::smatch match;
            if (std::regex_search(line, match, value_regex)) battery_capacity = std::stod(match[1]);
        } else if (line.rfind("C ", 0) == 0) {
            std::smatch match;
            if (std::regex_search(line, match, value_regex)) cargo_capacity = std::stod(match[1]);
        } else if (line.rfind("r ", 0) == 0) {
            std::smatch match;
            if (std::regex_search(line, match, value_regex)) consumption_rate = std::stod(match[1]);
        } else if (line.rfind("g ", 0) == 0) {
            std::smatch match;
            if (std::regex_search(line, match, value_regex)) inverse_refueling_rate = std::stod(match[1]);
        } else if (line.rfind("v ", 0) == 0) {
            std::smatch match;
            if (std::regex_search(line, match, value_regex)) average_speed = std::stod(match[1]);
        } else if (line.rfind("w_charge ", 0) == 0) {
            wireless_charge_rate = 0.9;
        } else if (parsing_nodes && line.rfind("StringID", 0) != 0) {
            std::vector<std::string> parts;
            std::istringstream ss(line);
            std::string part;
            while (ss >> part) parts.push_back(part);
            if (parts.size() >= 8) {
                std::string node_id = parts[0];
                char node_type = parts[1][0];
                double x = std::stod(parts[2]);
                double y = std::stod(parts[3]);
                double demand = std::stod(parts[4]);
                double ready_time = std::stod(parts[5]);
                double due_date = std::stod(parts[6]);
                double service_time = std::stod(parts[7]);
                NodeType type = NodeType::d;
                if (node_type == 'd') type = NodeType::d;
                else if (node_type == 'c') type = NodeType::c;
                else if (node_type == 'f') type = NodeType::f;
                Node node(node_id, static_cast<int>(all_nodes.size()), type, x, y, demand, ready_time, due_date, service_time);
                all_nodes.push_back(node);
                if (type == NodeType::d) depot_node = node;
                else if (type == NodeType::c) customers_vec.push_back(node);
                else if (type == NodeType::f) stations_vec.push_back(node);
            }
        }
    }
    nodes = all_nodes;
    depot = depot_node;
    customers = customers_vec;
    stations = stations_vec;

    // Build arcs
    arcs.clear();
    for (size_t i = 0; i < nodes.size(); ++i) {
        for (size_t j = 0; j < nodes.size(); ++j) {
            if (i != j) {
                double dist = calculate_distance(nodes[i], nodes[j]);
                arcs.emplace_back(i, j, dist, 0.0); // wireless_coverage set later
            }
        }
    }
}

void Instance::set_wireless_coverage(const std::string& pattern) {
    for (Arc& arc : arcs) {
        double coverage = 0.0;
        if (pattern == "none") coverage = 0.0;
        else if (pattern == "light") coverage = 0.2;
        else if (pattern == "moderate") coverage = 0.4;
        else if (pattern == "high") coverage = 0.6;
        wireless_coverage[{arc.get_from(), arc.get_to()}] = coverage;
        arc.set_wireless_coverage(coverage);
    }
}


void Instance::print_summary() const {
    std::cout << "==================== INSTANCE SUMMARY ====================\n";
    std::cout << "Parameters:\n";
    std::cout << "  Battery capacity (Q): " << battery_capacity << "\n";
    std::cout << "  Cargo capacity (C):   " << cargo_capacity << "\n";
    std::cout << "  Average speed (v):    " << average_speed << "\n";
    std::cout << "  Consumption rate (r): " << consumption_rate << "\n";
    std::cout << "  Refuel rate (g):      " << inverse_refueling_rate << "\n";
    std::cout << "  Load factor:          " << load_factor << "\n";
    std::cout << "  Alpha:                " << alpha << "\n";
    std::cout << "  Beta:                 " << beta << "\n";
    std::cout << "  Wireless charge rate: " << wireless_charge_rate << "\n";
    std::cout << "----------------------------------------------------------\n";

    std::cout << "Node counts:\n";
    std::cout << "  Depot:     " << 1 << "\n";
    std::cout << "  Customers: " << customers.size() << "\n";
    std::cout << "  Stations:  " << stations.size() << "\n";
    std::cout << "  Total:     " << nodes.size() << "\n";
    std::cout << "----------------------------------------------------------\n";

    // Print depot
    std::cout << "Depot:\n";
    std::cout << std::setw(6) << "ID " << std::setw(8) << "StringID"
              << std::setw(12) << "Type" << std::setw(8) << "x"
              << std::setw(8) << "y" << std::setw(10) << "Demand"
              << std::setw(12) << "ReadyTime" << std::setw(10) << "DueDate"
              << std::setw(12) << "ServiceT" << "\n";
    std::cout << std::string(74, '-') << "\n";
    std::cout << std::setw(6) << depot.get_int_id()
              << std::setw(8) << depot.get_string_id()
              << std::setw(12) << "Depot"
              << std::setw(8) << depot.get_x()
              << std::setw(8) << depot.get_y()
              << std::setw(10) << depot.get_demand()
              << std::setw(12) << depot.get_ready_time()
              << std::setw(10) << depot.get_due_date()
              << std::setw(12) << depot.get_service_time() << "\n\n";

    // Print customers
    std::cout << "Customers:\n";
    std::cout << std::setw(6) << "ID "<< std::setw(8) << "StringID" << std::setw(12) << "Type" << std::setw(8) << "x"
              << std::setw(8) << "y" << std::setw(10) << "Demand"
              << std::setw(12) << "ReadyTime" << std::setw(10) << "DueDate"
              << std::setw(12) << "ServiceT" << "\n";
    std::cout << std::string(74, '-') << "\n";
    for (const auto& customer : customers) {
        std::cout << std::setw(6) << customer.get_int_id()
             << std::setw(8) << customer.get_string_id()
             << std::setw(12) << "Customer"
             << std::setw(8) << customer.get_x()
             << std::setw(8) << customer.get_y()
             << std::setw(10) << customer.get_demand()
             << std::setw(12) << customer.get_ready_time()
             << std::setw(10) << customer.get_due_date()
             << std::setw(12) << customer.get_service_time() << "\n";
    }
    std::cout << "\n";

    // Print stations
    std::cout << "Stations:\n";
    std::cout << std::setw(6) << "ID " << std::setw(8) << "StringID" << std::setw(12) << "Type" << std::setw(8) << "x"
              << std::setw(8) << "y" << std::setw(10) << "Demand"
              << std::setw(12) << "ReadyTime" << std::setw(10) << "DueDate"
              << std::setw(12) << "ServiceT" << "\n";
    std::cout << std::string(74, '-') << "\n";
    for (const auto& station : stations) {
        std::cout << std::setw(6) << station.get_int_id()
            << std::setw(8) << station.get_string_id()
            << std::setw(12) << "Station"
            << std::setw(8) << station.get_x()
            << std::setw(8) << station.get_y()
            << std::setw(10) << station.get_demand()
            << std::setw(12) << station.get_ready_time()
            << std::setw(10) << station.get_due_date()
            << std::setw(12) << station.get_service_time() << "\n";
    }
    std::cout << "\n";

    // Print arcs
    std::cout << "Arcs (first 10):\n";
    std::cout << std::setw(6) << "From" << std::setw(6) << "To"
              << std::setw(12) << "Distance"
              << std::setw(12) << "WirelessCov" << "\n";
    std::cout << std::string(36, '-') << "\n";
    for (size_t i = 0; i < std::min<size_t>(10, arcs.size()); ++i) {
        const auto& arc = arcs[i];
        std::cout << std::setw(6) << arc.get_from()
                  << std::setw(6) << arc.get_to()
                  << std::setw(12) << arc.get_distance()
                  << std::setw(12) << arc.get_wireless_coverage() << "\n";
    }
    std::cout << "==========================================================\n";
}
