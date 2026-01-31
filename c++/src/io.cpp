#include "../include/io.h"
#include <iostream>

namespace NovoLang {

void IO::print(const std::string& msg) {
    std::cout << msg << std::endl;
}

std::string IO::input(const std::string& prompt) {
    if (!prompt.empty()) {
        std::cout << prompt;
    }
    std::string line;
    std::getline(std::cin, line);
    return line;
}

}
