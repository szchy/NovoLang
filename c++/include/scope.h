#pragma once
#include <string>
#include <unordered_map>
#include <memory>
#include <vector>
#include <iostream>
#include <variant>
#include <stdexcept>

namespace NovoLang {

// Value type supporting Long, Double, String, Bool, Null
// Corresponds to Requirement 47: Type Mapping
struct Value {
    enum Type { LONG, DOUBLE, STRING, BOOL, NONE };
    Type type;
    std::variant<long, double, std::string, bool, std::nullptr_t> data;

    Value() : type(NONE), data(nullptr) {}
    Value(long v) : type(LONG), data(v) {}
    Value(double v) : type(DOUBLE), data(v) {}
    Value(std::string v) : type(STRING), data(v) {}
    Value(bool v) : type(BOOL), data(v) {}
    Value(std::nullptr_t) : type(NONE), data(nullptr) {}

    std::string toString() const;
};

class Scope {
public:
    Scope(std::shared_ptr<Scope> parent = nullptr);
    
    void define(const std::string& name, Value value);
    void assign(const std::string& name, Value value);
    Value get(const std::string& name);
    bool existsLocal(const std::string& name);
    
private:
    std::unordered_map<std::string, Value> variables;
    std::shared_ptr<Scope> parent;
};

}
