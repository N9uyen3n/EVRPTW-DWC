#ifndef ARC_H
#define ARC_H

#include <string>

class Arc {
private:
    int from, to;
    double distance;
    double wireless_coverage;  // Fraction [0,1]

public:
    Arc(int from, int to, double distance, double wireless_coverage)
        : from(from), to(to), distance(distance), wireless_coverage(wireless_coverage) {}

    int get_from() const { return from; }
    int get_to() const { return to; }
    double get_distance() const { return distance; }
    double get_wireless_coverage() const { return wireless_coverage; }

    // Setter methods if needed
    void set_wireless_coverage(double coverage) { wireless_coverage = coverage; }

    // Calculate travel time based on average speed
    double calculate_travel_time(double average_speed) const {
        return distance / average_speed;
    }

    // Calculate wireless charge gained on this arc
    double calculate_wireless_charge(double wireless_charge_rate) const {
        return wireless_charge_rate * distance * wireless_coverage;
    }

    std::string to_string() const {
        return "Arc(from: " + std::to_string(from) + ", to: " + std::to_string(to) +
               ", distance: " + std::to_string(distance) +
               ", wireless_coverage: " + std::to_string(wireless_coverage) + ")";
    }
};

#endif // ARC_H