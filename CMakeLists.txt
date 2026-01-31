cmake_minimum_required(VERSION 3.10)
project(NovoLang)

set(CMAKE_CXX_STANDARD 14)

find_package(pybind11 REQUIRED)
find_package(PythonLibs REQUIRED)

include_directories(c++/include)

pybind11_add_module(novolang_core
    c++/src/scope.cpp
    c++/src/ast_exec.cpp
    c++/src/io.cpp
    c++/src/py_bind.cpp
)
