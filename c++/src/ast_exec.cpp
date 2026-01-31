#include "../include/ast_exec.h"
#include "../include/io.h"
#include <iostream>
#include <string>

// Ensure we have definitions if not using a real compiler environment
#ifndef _WIN32
#include <pybind11/embed.h>
#endif

namespace NovoLang {

ASTExecutor::ASTExecutor() {
    globalScope = std::make_shared<Scope>();
    currentScope = globalScope;
}

void ASTExecutor::execute(const py::dict& ast) {
    try {
        if (ast.contains("type") && ast["type"].cast<std::string>() == "BLOCK") {
            execBlock(ast["statements"].cast<py::list>());
        }
    } catch (const std::exception& e) {
        std::cerr << "Runtime Error: " << e.what() << std::endl;
    }
}

void ASTExecutor::execBlock(const py::list& stmts) {
    for (auto item : stmts) {
        execStmt(item.cast<py::dict>());
    }
}

void ASTExecutor::execStmt(const py::dict& stmt) {
    std::string type = stmt["type"].cast<std::string>();
    
    if (type == "IF") execIf(stmt);
    else if (type == "LOOP") execLoop(stmt);
    else if (type == "PRINT") execPrint(stmt);
    else if (type == "ASSIGNMENT") execAssign(stmt);
    else if (type == "AUTO_CALL") execAuto(stmt);
    else if (type == "BLOCK") {
        // Create new scope
        auto oldScope = currentScope;
        currentScope = std::make_shared<Scope>(oldScope);
        execBlock(stmt["statements"].cast<py::list>());
        currentScope = oldScope;
    }
}

void ASTExecutor::execIf(const py::dict& stmt) {
    Value cond = evalExpr(stmt["condition"].cast<py::dict>());
    bool isTrue = false;
    if (cond.type == Value::BOOL) isTrue = std::get<bool>(cond.data);
    
    if (isTrue) {
        // Create scope for if block? Usually yes.
        auto oldScope = currentScope;
        currentScope = std::make_shared<Scope>(oldScope);
        
        // Body can be a block or single stmt. Assuming Block from AST builder
        py::dict body = stmt["body"].cast<py::dict>();
        if (body["type"].cast<std::string>() == "BLOCK") {
             execBlock(body["statements"].cast<py::list>());
        } else {
             execStmt(body);
        }
        
        currentScope = oldScope;
    } else if (stmt.contains("else_body") && !stmt["else_body"].is_none()) {
        auto oldScope = currentScope;
        currentScope = std::make_shared<Scope>(oldScope);
        
        py::dict elseBody = stmt["else_body"].cast<py::dict>();
         if (elseBody["type"].cast<std::string>() == "BLOCK") {
             execBlock(elseBody["statements"].cast<py::list>());
        } else {
             execStmt(elseBody);
        }
        
        currentScope = oldScope;
    }
}

void ASTExecutor::execLoop(const py::dict& stmt) {
    while (true) {
        Value cond = evalExpr(stmt["condition"].cast<py::dict>());
        bool isTrue = false;
        if (cond.type == Value::BOOL) isTrue = std::get<bool>(cond.data);
        
        if (!isTrue) break;
        
        auto oldScope = currentScope;
        currentScope = std::make_shared<Scope>(oldScope);
        
        py::dict body = stmt["body"].cast<py::dict>();
        if (body["type"].cast<std::string>() == "BLOCK") {
             execBlock(body["statements"].cast<py::list>());
        } else {
             execStmt(body);
        }
        
        currentScope = oldScope;
    }
}

void ASTExecutor::execPrint(const py::dict& stmt) {
    Value val = evalExpr(stmt["expr"].cast<py::dict>());
    IO::print(val.toString());
}

void ASTExecutor::execAssign(const py::dict& stmt) {
    std::string name = stmt["target"].cast<std::string>();
    Value val = evalExpr(stmt["value"].cast<py::dict>());
    
    if (currentScope->existsLocal(name)) {
        currentScope->assign(name, val);
    } else {
        // Check if exists in parent? 
        // Logic: if exists in any scope, update it. If not, define in current.
        // Simplified: define in current if not found? 
        // Usually assignment to new var defines it in local scope.
        // If it refers to existing var, it updates it.
        try {
            currentScope->assign(name, val);
        } catch (...) {
            currentScope->define(name, val);
        }
    }
}

void ASTExecutor::execAuto(const py::dict& stmt) {
    std::string funcName = stmt["function"].cast<std::string>();
    py::list argsAst = stmt["args"].cast<py::list>();
    py::list args;
    for (auto arg : argsAst) {
        Value v = evalExpr(arg.cast<py::dict>());
        if (v.type == Value::LONG) args.append(std::get<long>(v.data));
        else if (v.type == Value::DOUBLE) args.append(std::get<double>(v.data));
        else if (v.type == Value::STRING) args.append(std::get<std::string>(v.data));
        else if (v.type == Value::BOOL) args.append(std::get<bool>(v.data));
        else args.append(py::none());
    }
    
    try {
        // Need to ensure python path is correct
        py::object auto_module = py::module::import("python.auto_api");
        py::object api = auto_module.attr("AutoAPI")();
        api.attr("execute")(funcName, args);
    } catch (py::error_already_set& e) {
        std::cerr << "Python Error: " << e.what() << std::endl;
    }
}

Value ASTExecutor::evalExpr(const py::dict& expr) {
    std::string type = expr["type"].cast<std::string>();
    
    if (type == "NUMBER") {
        double d = expr["value"].cast<double>();
        // Check if it's integer
        if (d == (long)d) return Value((long)d);
        return Value(d);
    } else if (type == "STRING") {
        return Value(expr["value"].cast<std::string>());
    } else if (type == "BOOL") {
        return Value(expr["value"].cast<bool>());
    } else if (type == "NULL") {
        return Value(nullptr);
    } else if (type == "IDENTIFIER") {
        return currentScope->get(expr["name"].cast<std::string>());
    } else if (type == "BINARY_OP") {
        return evalBinOp(expr);
    }
    
    return Value(nullptr);
}

Value ASTExecutor::evalBinOp(const py::dict& expr) {
    Value left = evalExpr(expr["left"].cast<py::dict>());
    Value right = evalExpr(expr["right"].cast<py::dict>());
    std::string op = expr["op"].cast<std::string>();
    
    // Simplified implementation for numeric operations
    if (left.type == Value::LONG && right.type == Value::LONG) {
        long l = std::get<long>(left.data);
        long r = std::get<long>(right.data);
        if (op == "+") return Value(l + r);
        if (op == "-") return Value(l - r);
        if (op == "*") return Value(l * r);
        if (op == "/") return Value(r == 0 ? 0 : l / r); // Handle div by zero
        if (op == ">") return Value(l > r);
        if (op == "<") return Value(l < r);
        if (op == "==") return Value(l == r);
    }
    // Add more types/ops support...
    
    return Value(nullptr);
}

}
