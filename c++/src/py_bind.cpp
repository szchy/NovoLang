#include "../include/ast_exec.h"

// Ensure we have definitions if not using a real compiler environment
#ifndef _WIN32
#include <pybind11/pybind11.h>
namespace py = pybind11;
#endif

// Mock macro for syntax checking in this environment
#ifdef _WIN32
#ifndef PYBIND11_MODULE
#define PYBIND11_MODULE(name, m) void init_##name(py::object m)
#endif
namespace pybind11 {
    class module_ : public object {};
    template <typename T>
    class class_ {
    public:
        class_(object m, const char* name) {}
        class_& def(const char* name, void (T::*f)(const dict&), const char* doc = "") { return *this; }
        class_& def(object init) { return *this; }
    };
    object init() { return object(); }
}
#endif

namespace NovoLang {

PYBIND11_MODULE(novolang_core, m) {
    // m.doc() = "NovoLang C++ Execution Engine"; // doc() might not be in mock

    py::class_<ASTExecutor>(m, "ASTExecutor")
        .def(py::init<>())
        .def("execute", &ASTExecutor::execute, "Execute AST");
}

}
