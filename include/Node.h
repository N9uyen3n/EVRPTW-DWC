#ifndef NODE_H
#define NODE_H

#include <string>

enum NodeType {d, c, f}; //depot, customer, station

class Node {
private:
    std::string stringID;
    int intID;
    NodeType type;
    double x, y;
    double demand;
    double ready_time, due_date;
    double service_time;

public:
    Node() :
    stringID(""), intID(0), type(NodeType::d), x(0), y(0), demand(0), ready_time(0), due_date(0), service_time(0) {}

    Node(const std::string& string_id, int int_id, NodeType type, double x, double y,
         double demand, double ready_time, double due_date, double service_time)
        : stringID(string_id), intID(int_id), type(type), x(x), y(y),
          demand(demand), ready_time(ready_time), due_date(due_date), service_time(service_time) {}

    // Getter and setter methods
    std::string get_string_id() const { return stringID; }
    int get_int_id() const { return intID; }
    NodeType get_type() const { return type; }
    double get_x() const { return x; }
    double get_y() const { return y; }
    double get_demand() const { return demand; }
    double get_ready_time() const { return ready_time; }
    double get_due_date() const { return due_date; }
    double get_service_time() const { return service_time; }

    void set_type(NodeType t) { type = t; }
    void set_string_id(const std::string &string_id) {stringID = string_id;}
    void set_int_id(int int_id) {intID = int_id;}
    void set_x(double x) {this->x = x;}
    void set_y(double y) {this->y = y;}
    void set_demand(double demand) {this->demand = demand;}
    void set_ready_time(double ready_time) {this->ready_time = ready_time;}
    void set_due_date(double due_date) {this->due_date = due_date;}
    void set_service_time(double service_time) {this->service_time = service_time;}

    std::string to_string() const {
        return "Node(ID: " + stringID + ", Type: " + std::to_string(type) +
               ", x: " + std::to_string(x) + ", y: " + std::to_string(y) +
               ", demand: " + std::to_string(demand) +
               ", time_window: [" + std::to_string(ready_time) + ", " + std::to_string(due_date) + "]" +
               ", service_time: " + std::to_string(service_time) + ")";
    }
};

#endif // NODE_H