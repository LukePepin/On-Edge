#include <stdint.h>
#include <time.h>
#include <stdlib.h>
#include <stdio.h>
#include "micro-ecc/uECC.h"

/*
 * C-Wrapper for uECC_verify to benchmark exact execution time on Cortex-A72.
 * Uses /dev/urandom for cryptographically secure entropy.
 * Executes full ECDSA verification using secp256r1.
 */

// Cryptographically secure RNG using /dev/urandom
static int urandom_RNG(uint8_t *dest, unsigned size) {
    FILE *f = fopen("/dev/urandom", "r");
    if (!f) return 0;
    size_t bytes_read = fread(dest, 1, size, f);
    fclose(f);
    return bytes_read == size;
}

// Struct to return both the boolean result and the elapsed nanoseconds
typedef struct {
    int success;
    unsigned long long elapsed_ns;
} VerifyResult;

VerifyResult benchmark_uecc_verify(const uint8_t* public_key, const uint8_t* message_hash, const uint8_t* signature) {
    // Set the true RNG (must be set for verification algorithms that require entropy to prevent fault attacks)
    uECC_set_rng(&urandom_RNG);
    
    struct timespec start, end;
    VerifyResult result;
    
    clock_gettime(CLOCK_MONOTONIC, &start);
    result.success = uECC_verify(public_key, message_hash, 32, signature, uECC_secp256r1());
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    result.elapsed_ns = (unsigned long long)(end.tv_sec - start.tv_sec) * 1000000000ULL + (end.tv_nsec - start.tv_nsec);
    
    return result;
}
