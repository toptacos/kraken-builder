#include <stdio.h>
#include <string.h>
int main(void) {
    char buf[4096];
    size_t n = fread(buf, 1, sizeof(buf) - 1, stdin);
    buf[n] = 0;
    const char *name = "world";
    char *p = strstr(buf, "\"name\"");
    static char got[64];
    if (p) {
        p = strchr(p + 6, '"');
        if (p) {
            char *q = strchr(p + 1, '"');
            if (q && (q - p - 1) < 63) {
                memcpy(got, p + 1, (size_t)(q - p - 1));
                got[q - p - 1] = 0;
                name = got;
            }
        }
    }
    printf("{\"v\":1,\"ok\":true,\"result\":{\"arm\":\"hello-c\",\"lang\":\"c\",\"hello\":\"hello, %s\"}}", name);
    return 0;
}
