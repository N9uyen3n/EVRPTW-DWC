// MILPSolver.h
#ifndef MILPSOLVER_H
#define MILPSOLVER_H

#include "SolverBase.h"
#include <ilcplex/ilocplex.h>
#include <vector>
#include <string>

ILOSTLBEGIN

struct DummyStation {
    int original_station_id;
    int visit_index;
    int dummy_id;
};

class MILPSolver : public SolverBase {
private:
    int max_vehicles_;
    int max_station_visits_;
    std::vector<DummyStation> dummy_stations_;
    int depot_start_;
    int depot_end_;
    std::vector<int> I_;
    std::vector<int> F_prime_;
    std::vector<int> V_;
    std::vector<int> V0_;
    std::vector<int> Vn1_;
    std::vector<int> V0n1_;
    std::vector<int> I0_;
    std::vector<int> F_prime_0_;
    int num_charge_segments_;
    std::vector<double> charge_breakpoints_;
    std::map<int, size_t> vertex_to_index_;
    std::map<int, size_t> id_to_index;

    // CPLEX variables
    IloEnv env_;
    IloModel model_;
    IloCplex cplex_;
    IloArray<IloBoolVarArray> x_;
    IloNumVarArray tau_;
    IloNumVarArray u_;
    IloNumVarArray y_;
    IloNumVarArray ch_;
    IloBoolVarArray z_;
    IloArray<IloNumVarArray> lambda_;
    IloNumVarArray charge_time_;
    IloNumVarArray load_ratio_;
    IloArray<IloNumVarArray>  load_consumption_;
    IloExpr num_vehicles_expr_;
    IloExpr total_distance_expr_;
    IloExpr total_time_expr_;
    IloCplex::CplexStatus solution_status_;

public:
    MILPSolver(const Instance& inst, int max_vehicles = 0, int max_station_visits = 2);
    ~MILPSolver();
    void build_model() override;
    void solve() override;
    void print_solution() const override;

    // Helper methods
    std::map<std::string, double> get_node_data(const int& vertex_id) const;
    int get_original_node_id(const int& vertex_id) const;
    double get_wireless_coverage(const int& i, const int& j) const;
    double calculate_distance_vertices(const int& i, const int& j) const;
    double calculate_travel_time_vertices(const int& v1, const int& v2) const;
    double calculate_wireless_charge(const int& i, const int& j) const;
    double calculate_nonlinear_charging_time(double charge_amount) const;
    double get_load_dependent_consumption(double distance, double load_ratio) const;
};

#endif // MILPSOLVER_H