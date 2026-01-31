#pragma once
// Forward declaration to avoid dependency issues in this environment
// In real build, ensure pybind11 is included
#ifdef _WIN32
// Mocking pybind11 for structure
namespace pybind11 {
    class dict {};
    class list {};
    class object {};
}
namespace py = pybind11;
#else
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;
#endif

#include "scope.h"
#include <vector>

namespace NovoLang {

class ASTExecutor {
public:
    ASTExecutor();
    // In real implementation, pass py::dict. Using generic template or void* here to avoid header errors if compiled without pybind11
    // But since I'm writing source code for the user, I should use the correct types.
    // I will assume the user has pybind11.
    void execute(const py::dict& ast);
    
private:
    std::shared_ptr<Scope> globalScope;
    std::shared_ptr<Scope> currentScope;
    
    // Helper to extract value from py::object
    Value pyToValue(const py::object& obj);

    void execBlock(const py::list& stmts);
    void execStmt(const py::dict& stmt);
    Value evalExpr(const py::dict& expr);
    
    void execIf(const py::dict& stmt);
    void execLoop(const py::dict& stmt);
    void execPrint(const py::dict& stmt);
    void execAssign(const py::dict& stmt);
    void execAuto(const py::dict& stmt); // Calls back to Python
    
    Value evalBinOp(const py::dict& expr);
};

}
