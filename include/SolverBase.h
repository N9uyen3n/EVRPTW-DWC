// SolverBase.h
#ifndef SOLVERBASE_H
#define SOLVERBASE_H

#include "Instance.h"

// Solution storage
struct Solution {
    double objective_value;
    int num_vehicles;
    double total_distance;
    double total_time;
    std::vector<std::vector<int> > routes;
    std::map<int, std::map<std::string, double> > charging_details;
    double computation_time;
    std::string solver_used;
};


class SolverBase {
protected:
    const Instance &instance;

public:
    SolverBase(const Instance &inst) : instance(inst) {
    }

    virtual ~SolverBase() = default;

    virtual void build_model() = 0;

    virtual void solve() = 0;

    virtual void print_solution() const = 0;
};

#endif // SOLVERBASE_H
