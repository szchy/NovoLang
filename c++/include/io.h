#pragma once
#include <string>

namespace NovoLang {
    class IO {
    public:
        static void print(const std::string& msg);
        static std::string input(const std::string& prompt);
    };
}
