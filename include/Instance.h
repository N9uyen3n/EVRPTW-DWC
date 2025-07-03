#ifndef INSTANCE_H
#define INSTANCE_H

#include "Node.h"
#include "Arc.h"
#include <vector>
#include <string>
#include <map>
#include <cmath>
#include <memory>

// tạo mọt cấu trúc dùng để lưu trữ các kết quả cuối cùng sau khi giải của Instance
struct InstanceSolution {
    double objective_value;
    int num_vehicles;
    double total_distance;
    double total_time;
    std::vector<std::vector<int> > routes;
    std::map<int, std::map<std::string, double> > charging_details;
    double computation_time;
    std::string solver_used;
};

std::unique_ptr<InstanceSolution> solution;

class Instance {
private:
    std::vector<Node> nodes;
    std::vector<Arc> arcs;
    Node depot;
    std::vector<Node> customers;
    std::vector<Node> stations;
    std::vector<Node> dummy_stations;  // For multiple visits
    double battery_capacity; // Q
    double cargo_capacity; // C
    double average_speed; // v
    double consumption_rate; // r
    double inverse_refueling_rate; // g
    double load_factor; //
    double alpha, beta;  // For non-linear charging
    double wireless_charge_rate; // Rate of wireless charging per unit distance
    std::map<std::pair<int, int>, double> wireless_coverage;  // (from, to) -> coverage fraction

    // Helper method to calculate distance between two nodes
    double calculate_distance(const Node& n1, const Node& n2) const {
        return std::sqrt(std::pow(n1.get_x() - n2.get_x(), 2) + std::pow(n1.get_y() - n2.get_y(), 2));
    }

public:
    // Instance() : battery_capacity(0), cargo_capacity(0), average_speed(0), load_factor(0),
    //              alpha(0), beta(0), wireless_charge_rate(0) {}

    Instance() : depot(), battery_capacity(0), cargo_capacity(0), average_speed(0), load_factor(0),
             alpha(0), beta(0), wireless_charge_rate(0) {}

    // Parse instance from file
    void parse_instance_file(const std::string& filename);

    // Set wireless coverage for arcs
    void set_wireless_coverage(const std::string& pattern);

    // Create dummy nodes for multiple station visits
    void create_dummy_stations(int max_visits);

    // Getter methods
    const std::vector<Node>& get_nodes() const { return nodes; }
    const std::vector<Arc>& get_arcs() const { return arcs; }
    const Node& get_depot() const { return depot; }
    const std::vector<Node>& get_customers() const { return customers; }
    const std::vector<Node>& get_stations() const { return stations; }
    const std::vector<Node>& get_dummy_stations() const { return dummy_stations; }
    double get_battery_capacity() const { return battery_capacity; }
    double get_cargo_capacity() const { return cargo_capacity; }
    double get_average_speed() const { return average_speed; }
    double get_consumption_rate() const { return consumption_rate; }
    double get_inverse_refueling_rate() const { return inverse_refueling_rate; }
    double get_load_factor() const { return load_factor; }
    double get_alpha() const { return alpha; }
    double get_beta() const { return beta; }
    double get_wireless_charge_rate() const { return wireless_charge_rate; }
    double get_wireless_coverage(int from, int to) const {
        auto key = std::make_pair(from, to);
        auto it = wireless_coverage.find(key);
        return (it != wireless_coverage.end()) ? it->second : 0.0;
    }

    void set_nodes(const std::vector<Node> &nodes) {
        this->nodes = nodes;
    }

    void set_arcs(const std::vector<Arc> &arcs) {
        this->arcs = arcs;
    }

    void set_depot(const Node &depot) {
        this->depot = depot;
    }

    void set_customers(const std::vector<Node> &customers) {
        this->customers = customers;
    }

    void set_stations(const std::vector<Node> &stations) {
        this->stations = stations;
    }

    void set_dummy_stations(const std::vector<Node> &dummy_stations) {
        this->dummy_stations = dummy_stations;
    }

    void set_battery_capacity(double battery_capacity) {
        this->battery_capacity = battery_capacity;
    }

    void set_cargo_capacity(double cargo_capacity) {
        this->cargo_capacity = cargo_capacity;
    }

    void set_average_speed(double average_speed) {
        this->average_speed = average_speed;
    }

    void set_consumption_rate(double consumption_rate) {
        this->consumption_rate = consumption_rate;
    }

    void set_inverse_refueling_rate(double inverse_refueling_rate) {
        this->inverse_refueling_rate = inverse_refueling_rate;
    }

    void set_load_factor(double load_factor) {
        this->load_factor = load_factor;
    }

    void set_alpha(double alpha) {
        this->alpha = alpha;
    }

    void set_beta(double beta) {
        this->beta = beta;
    }

    void set_wireless_charge_rate(double wireless_charge_rate) {
        this->wireless_charge_rate = wireless_charge_rate;
    }

    void set_wireless_coverage1(const std::map<std::pair<int, int>, double> &wireless_coverage) {
        this->wireless_coverage = wireless_coverage;
    }


    void print_summary() const;
};

#endif // INSTANCE_H