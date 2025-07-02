cmake_minimum_required(VERSION 3.31)
project(Test1)

set(CMAKE_CXX_STANDARD 17)

add_executable(Test1 main.cpp
        src/Node.cpp
        include/Node.h
        src/Arc.cpp
        include/Arc.h
        src/Instance.cpp
        include/Instance.h
        include/SolverBase.h
        src/MILPSolver.cpp
        include/MILPSolver.h
        src/MHSolver.cpp
        include/MHSolver.h)

add_executable(TestInstance test/TestInstance.cpp
        include/Node.h
        include/Arc.h
        include/Instance.h
        src/Node.cpp
        src/Arc.cpp
        src/Instance.cpp
       )
