#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>

typedef char *(*run_function)(unsigned long long, char *, char *);
typedef void (*free_function)(char *);

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: smoke_ohos LIBRARY PROJECT ENTRY\n");
        return 2;
    }

    void *library = dlopen(argv[1], RTLD_NOW);
    if (library == NULL) {
        fprintf(stderr, "%s\n", dlerror());
        return 2;
    }
    run_function run = (run_function)dlsym(library, "QfliGoRun");
    free_function release = (free_function)dlsym(library, "QfliGoFree");
    if (run == NULL || release == NULL) {
        fprintf(stderr, "Go runtime exports are missing\n");
        return 2;
    }

    char *result = run(1, argv[2], argv[3]);
    if (result == NULL) {
        fprintf(stderr, "Go runtime returned no result\n");
        return 2;
    }
    puts(result);
    release(result);
    dlclose(library);
    return 0;
}
