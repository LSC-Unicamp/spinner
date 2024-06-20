cmake_minimum_required(VERSION 3.10)
project(MPI_IO_Count)

# Set C++ standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Find MPI package
find_package(MPI REQUIRED)

# Include MPI directories
include_directories(${MPI_INCLUDE_PATH})

# Add the executable
add_executable(mpi_io_count main.cpp)

# Link MPI libraries
target_link_libraries(mpi_io_count ${MPI_LIBRARIES})

# Set compiler flags for MPI
if(MPI_COMPILE_FLAGS)
  set_target_properties(mpi_io_count PROPERTIES
    COMPILE_FLAGS "${MPI_COMPILE_FLAGS}")
endif()

if(MPI_LINK_FLAGS)
  set_target_properties(mpi_io_count PROPERTIES
    LINK_FLAGS "${MPI_LINK_FLAGS}")
endif()
