#include <iostream>
#include <string>
int main() {
    std::string s((std::istreambuf_iterator<char>(std::cin)), std::istreambuf_iterator<char>());
    std::string name = "world";
    auto k = s.find("\"name\"");
    if (k != std::string::npos) {
        auto q = s.find('"', k + 6);
        if (q != std::string::npos) {
            auto q2 = s.find('"', q + 1);
            if (q2 != std::string::npos) name = s.substr(q + 1, q2 - q - 1);
        }
    }
    std::cout << "{\"v\":1,\"ok\":true,\"result\":{\"arm\":\"hello-cpp\",\"lang\":\"cpp\",\"hello\":\"hello, " << name << "\"}}";
    return 0;
}
