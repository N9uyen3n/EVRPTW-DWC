// SolverBase.h
#ifndef SOLVERBASE_H
#define SOLVERBASE_H

#include "Instance.h"

class SolverBase {
protected:
    const Instance& instance;
public:
    SolverBase(const Instance& inst) : instance(inst) {}
    virtual ~SolverBase() = default;

    virtual void build_model() = 0;
    virtual void solve() = 0;
    virtual void print_solution() const = 0;
};

#endif // SOLVERBASE_H