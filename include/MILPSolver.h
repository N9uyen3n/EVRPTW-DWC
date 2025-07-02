// MILPSolver.h
#ifndef MILPSOLVER_H
#define MILPSOLVER_H

#include "SolverBase.h"

class MILPSolver : public SolverBase {
public:
    MILPSolver(const Instance& inst) : SolverBase(inst) {}
    void build_model() override;
    void solve() override;
    void print_solution() const override;
};

#endif // MILPSOLVER_H