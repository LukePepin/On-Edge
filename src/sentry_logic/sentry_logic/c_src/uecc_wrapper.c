#include <stdint.h>
#include <time.h>
#include <stdlib.h>
#include "micro-ecc/uECC.h"

/*
 * C-Wrapper for uECC_verify to benchmark exact execution time on Cortex-A72.
 * This function handles key generation, signature generation, and verification natively in C
 * to eliminate Python overhead, using POSIX CLOCK_MONOTONIC for nanosecond precision.
 */

// Custom RNG for uECC
static int default_RNG(uint8_t *dest, unsigned size) {
    while (size) {
        uint8_t val = (uint8_t)rand();
        *dest = val;
        ++dest;
        --size;
    }
    return 1;
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
    uint8_t hash[32]; // Normally SHA-256 of the message
    uint8_t signature[64];
    
    uECC_set_rng(&default_RNG);
    
    // Generate keys
    if (!uECC_make_key(public_key, private_key, curve)) {
        return result; // Failed to make key
    }
    
    // Generate a simple hash from the message (for simulation purposes)
    for(int i = 0; i < 32; i++) {
        hash[i] = message[i % message_size] ^ i;
    }
    
    // Generate signature
    if (!uECC_sign(private_key, hash, sizeof(hash), signature, curve)) {
        return result; // Failed to sign
    }
    
    struct timespec start, end;
    
    // POSIX MONOTONIC TIMER - Start
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    // Execution payload (The Verifier)
    int valid = uECC_verify(public_key, hash, sizeof(hash), signature, curve);
    
    // POSIX MONOTONIC TIMER - End
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    // Calculate precise absolute delta in nanoseconds
    unsigned long long start_ns = (unsigned long long)start.tv_sec * 1000000000ULL + start.tv_nsec;
    unsigned long long end_ns = (unsigned long long)end.tv_sec * 1000000000ULL + end.tv_nsec;
    
    result.success = valid;
    result.elapsed_ns = end_ns - start_ns;
    
    return result;
}
