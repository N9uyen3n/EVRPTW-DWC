cmake_minimum_required(VERSION 3.31)
project(Test1)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)

# CPLEX directory
set(CPLEX_DIR "D:/Program Files/IBM/ILOG/CPLEX_Studio2211")

# Link directories for CPLEX and Concert libraries
link_directories(
        "${CPLEX_DIR}/cplex/lib/x64_windows_msvc14/stat_mda"
        "${CPLEX_DIR}/concert/lib/x64_windows_msvc14/stat_mda"
)

# Find CPLEX libraries
find_library(CPLEX_LIBRARY NAMES cplex2211 PATHS "${CPLEX_DIR}/cplex/lib/x64_windows_msvc14/stat_mda")
find_library(CONCERT_LIBRARY NAMES concert PATHS "${CPLEX_DIR}/concert/lib/x64_windows_msvc14/stat_mda")
find_library(ILOCPLEX_LIBRARY NAMES ilocplex PATHS "${CPLEX_DIR}/cplex/lib/x64_windows_msvc14/stat_mda")

# Check if libraries were found
if(NOT CPLEX_LIBRARY)
       message(FATAL_ERROR "Could not find cplex2211.lib")
endif()
if(NOT CONCERT_LIBRARY)
       message(FATAL_ERROR "Could not find concert.lib")
endif()
if(NOT ILOCPLEX_LIBRARY)
       message(FATAL_ERROR "Could not find ilocplex.lib")
endif()

# Include directories
include_directories(
        "${CPLEX_DIR}/cplex/include"
        "${CPLEX_DIR}/concert/include"
        "${CMAKE_SOURCE_DIR}/Test1/src"
)

# MSVC-specific compiler flags
if(MSVC)
       set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /MD /O2 /DNDEBUG /D_ITERATOR_DEBUG_LEVEL=0")
       set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} /MDd /Zi /Ob0 /Od /RTC1 /D_ITERATOR_DEBUG_LEVEL=2")
endif()

# Copy data files to build directory
file(COPY "${CMAKE_SOURCE_DIR}/data/Input/" DESTINATION "${CMAKE_BINARY_DIR}/data")

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

add_executable(TestCPLEX  test/TestCPLEX.cpp
)
target_link_libraries(TestCPLEX PRIVATE
        ${ILOCPLEX_LIBRARY}
        ${CPLEX_LIBRARY}
        ${CONCERT_LIBRARY}
)
target_compile_definitions(TestCPLEX PRIVATE _ITERATOR_DEBUG_LEVEL=0)
if(MSVC)
       set_property(TARGET TestCPLEX PROPERTY
               MSVC_RUNTIME_LIBRARY "MultiThreadedDLL"
       )
endif()

# TestMILPSolver
add_executable(TestMILPSolver  test/TestMILPSolver.cpp
        include/Node.h
        include/Arc.h
        include/Instance.h
        include/SolverBase.h
        include/MILPSolver.h
        src/MILPSolver.cpp
        src/Instance.cpp
        src/Arc.cpp
        src/Node.cpp
)
target_link_libraries(TestMILPSolver PRIVATE
        ${ILOCPLEX_LIBRARY}
        ${CPLEX_LIBRARY}
        ${CONCERT_LIBRARY}
)
target_compile_definitions(TestMILPSolver PRIVATE _ITERATOR_DEBUG_LEVEL=0)
if(MSVC)
       set_property(TARGET TestMILPSolver PROPERTY
               MSVC_RUNTIME_LIBRARY "MultiThreadedDLL"
       )
endif()