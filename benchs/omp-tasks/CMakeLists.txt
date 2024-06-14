cmake_minimum_required(VERSION 3.10)
project(program1)

set(CMAKE_CXX_STANDARD 11)

find_package(OpenMP REQUIRED)

add_executable(lustre1 main.cpp)

target_link_libraries(lustre1 OpenMP::OpenMP_CXX)

