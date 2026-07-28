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

VerifyResult benchmark_uecc_verify(const uint8_t* message, unsigned message_size) {
    VerifyResult result = {0, 0};
    
    // Use secp256r1 curve
    const struct uECC_Curve_t * curve = uECC_secp256r1();
    
    uint8_t private_key[32];
    uint8_t public_key[64];
    uint8_t hash[32]; // 256-bit hash
    uint8_t signature[64];
    
    // Set the true RNG
    uECC_set_rng(&urandom_RNG);
    
    // 1. Generate keys (Done outside timing block)
    if (!uECC_make_key(public_key, private_key, curve)) {
        return result; 
    }
    
    // 2. Generate hash (Done outside timing block)
    // Normally this would use a real SHA-256 library.
    for(int i = 0; i < 32; i++) {
        hash[i] = message[i % message_size] ^ i;
    }
    
    // 3. Generate signature (Done outside timing block)
    if (!uECC_sign(private_key, hash, sizeof(hash), signature, curve)) {
        return result; 
    }
    
    // 4. VERIFICATION BLOCK (This is the critical deterministic measurement)
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    int valid = uECC_verify(public_key, hash, sizeof(hash), signature, curve);
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    unsigned long long start_ns = (unsigned long long)start.tv_sec * 1000000000ULL + start.tv_nsec;
    unsigned long long end_ns = (unsigned long long)end.tv_sec * 1000000000ULL + end.tv_nsec;
    
    result.success = valid;
    result.elapsed_ns = end_ns - start_ns;
    
    return result;
}
