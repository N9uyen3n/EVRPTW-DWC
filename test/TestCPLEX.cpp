#include <ilcplex/ilocplex.h>
#include <vector>
#include <cmath>
#include <iostream>

ILOSTLBEGIN

struct Node {
    int id;
    double x, y;
    double ready_time, due_time; // a_i, b_i
    double service_time;
    bool is_charging_station;
};

struct Arc {
    int from, to;
    double cost; // distance or travel time
};

int main() {
    IloEnv env;
    try {
        IloModel model(env);

        // === 1. Input Data (Mock Example) === //
        int num_customers = 5;
        int charging_duplicates = 2;
        int K = 2; // number of vehicles
        double battery_capacity = 100.0;
        double energy_rate = 1.0;
        double Tmax = 1000.0;
        double bigM = 1e5;

        // Nodes: DepotOut = 0, DepotIn = 1, customers, and charging stations
        std::vector<Node> nodes = {
            {0, 0, 0, 0, Tmax, 0, false}, // DepotOut
            {1, 0, 0, 0, Tmax, 0, false}, // DepotIn
            {2, 10, 20, 10, 100, 5, false}, // customer 1
            {3, 15, 25, 20, 120, 5, false}, // customer 2
            {4, 20, 30, 30, 150, 5, false}, // customer 3
            {5, 25, 15, 40, 200, 5, false}, // customer 4
            {6, 30, 10, 50, 250, 5, false}, // customer 5
            {7, 30, 10, 0, Tmax, 15, true},  // charging station (original)
            {8, 30, 10, 0, Tmax, 15, true},  // copy 1
            {9, 30, 10, 0, Tmax, 15, true}   // copy 2
        };

        int N = nodes.size();

        // === 2. Arc Construction === //
        std::vector<Arc> arcs;
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                if (i == j) continue;
                double dx = nodes[i].x - nodes[j].x;
                double dy = nodes[i].y - nodes[j].y;
                double dist = sqrt(dx * dx + dy * dy);
                arcs.push_back({i, j, dist});
            }
        }

        // === 3. Variables === //
        IloArray<IloBoolVarArray> x(env, N);
        for (int i = 0; i < N; ++i) {
            x[i] = IloBoolVarArray(env, N);
            for (int j = 0; j < N; ++j) {
                if (i != j) {
                    x[i][j] = IloBoolVar(env, ("x_" + std::to_string(i) + "_" + std::to_string(j)).c_str());
                }
            }
        }

        // Energy variables
        IloNumVarArray e(env, N);
        for (int i = 0; i < N; ++i)
            e[i] = IloNumVar(env, 0, battery_capacity, ("e_" + std::to_string(i)).c_str());

        // Time variables
        IloNumVarArray t(env, N);
        for (int i = 0; i < N; ++i)
            t[i] = IloNumVar(env, 0, Tmax, ("t_" + std::to_string(i)).c_str());

        // Subtour elimination variables
        IloNumVarArray u(env, N);
        for (int i = 0; i < N; ++i)
            u[i] = IloNumVar(env, 0, N-1, ("u_" + std::to_string(i)).c_str());


        // === 4. Objective === //
        IloExpr obj(env);
        for (auto& arc : arcs) {
            obj += arc.cost * x[arc.from][arc.to];
        }
        model.add(IloMinimize(env, obj));
        obj.end();

        // === 5. Constraints === //

        // 5.1 Each customer visited once
        for (int i = 2; i <= 6; ++i) { // Customers from 2 to 6
            IloExpr in(env), out(env);
            for (int j = 0; j < N; ++j) {
                if (j != i) {
                    in += x[j][i];
                    out += x[i][j];
                }
            }
            model.add(in == 1);
            model.add(out == 1);
            in.end(); out.end();
        }

        // 5.2 Flow conservation
        for (int i = 2; i < N; ++i) {
            IloExpr in(env), out(env);
            for (int j = 0; j < N; ++j) {
                if (j != i) {
                    in += x[j][i];
                    out += x[i][j];
                }
            }
            model.add(in == out);
            in.end(); out.end();
        }

        // 5.3 Start and End at depot
        IloExpr start(env), end(env);
        for (int j = 2; j < N; ++j) start += x[0][j];
        for (int i = 2; i < N; ++i) end += x[i][1];
        model.add(start == K);
        model.add(end == K);
        start.end(); end.end();

        // 5.4 No in to DepotOut, no out from DepotIn
        for (int i = 0; i < N; ++i) model.add(x[i][0] == 0);
        for (int j = 0; j < N; ++j) model.add(x[1][j] == 0);

        // 5.5 Energy constraints
        for (auto& arc : arcs) {
            int i = arc.from, j = arc.to;
            double consumption = arc.cost * energy_rate;

            if (nodes[j].is_charging_station) {
                // Full charge at charging station
                model.add(e[j] >= battery_capacity - bigM * (1 - x[i][j]));
            } else if (i != 0) {
                // Energy consumption for non-depot-out nodes
                model.add(e[j] >= e[i] - consumption - bigM * (1 - x[i][j]));
            }
        }
        model.add(e[0] == battery_capacity); // Full battery at DepotOut

        // 5.6 Time window constraints
        for (int i = 0; i < N; ++i) {
            model.add(t[i] >= nodes[i].ready_time);
            model.add(t[i] <= nodes[i].due_time);
        }
        model.add(t[1] <= Tmax); // Ensure return to DepotIn within Tmax

        // 5.7 Time propagation
        for (auto& arc : arcs) {
            int i = arc.from, j = arc.to;
            model.add(t[j] >= t[i] + nodes[i].service_time + arc.cost - bigM * (1 - x[i][j]));
        }

        // 5.8 Subtour elimination (Miller-Tucker-Zemlin)
        for (auto& arc : arcs) {
            int i = arc.from, j = arc.to;
            if (i != 0 && j != 1) {
                model.add(u[j] >= u[i] + 1 - N * (1 - x[i][j]));
            }
        }
        model.add(u[0] == 0); // DepotOut as starting point

        // === 6. Solve === //
        IloCplex cplex(model);
        cplex.setOut(env.getNullStream());
        if (cplex.solve()) {
            std::cout << "Objective Value: " << cplex.getObjValue() << std::endl;
            std::cout << "\nRoutes:\n";
            for (int i = 0; i < N; ++i) {
                for (int j = 0; j < N; ++j) {
                    if (i != j && cplex.getValue(x[i][j]) > 0.5) {
                        std::cout << "Vehicle travels from node " << i << " to node " << j << std::endl;
                    }
                }
            }
            std::cout << "\nEnergy Levels:\n";
            for (int i = 0; i < N; ++i) {
                std::cout << "Node " << i << ": " << cplex.getValue(e[i]) << std::endl;
            }
            std::cout << "\nArrival Times:\n";
            for (int i = 0; i < N; ++i) {
                std::cout << "Node " << i << ": " << cplex.getValue(t[i]) << std::endl;
            }
        } else {
            std::cout << "No solution found.\n";
        }

    } catch (IloException& e) {
        std::cerr << "CPLEX Exception: " << e.getMessage() << std::endl;
    } catch (...) {
        std::cerr << "Unknown exception.\n";
    }
    env.end();
    return 0;
}