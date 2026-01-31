#include "../include/scope.h"

namespace NovoLang {

std::string Value::toString() const {
    switch (type) {
        case LONG: return std::to_string(std::get<long>(data));
        case DOUBLE: return std::to_string(std::get<double>(data));
        case STRING: return std::get<std::string>(data);
        case BOOL: return std::get<bool>(data) ? "真" : "假"; // Requirement 47
        case NONE: return "空";
    }
    return "";
}

Scope::Scope(std::shared_ptr<Scope> parent) : parent(parent) {}

void Scope::define(const std::string& name, Value value) {
    variables[name] = value;
}

void Scope::assign(const std::string& name, Value value) {
    if (variables.find(name) != variables.end()) {
        variables[name] = value;
    } else if (parent) {
        parent->assign(name, value);
    } else {
        throw std::runtime_error("错误：变量 '" + name + "' 未定义"); // Requirement 45
    }
}

Value Scope::get(const std::string& name) {
    if (variables.find(name) != variables.end()) {
        return variables[name];
    } else if (parent) {
        return parent->get(name);
    } else {
        throw std::runtime_error("错误：变量 '" + name + "' 未定义");
    }
}

bool Scope::existsLocal(const std::string& name) {
    return variables.find(name) != variables.end();
}

}
