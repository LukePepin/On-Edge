// Host-side mock of the pre-1.0 micro-ecc API. TEST HARNESS ONLY: the "workloads" advance
// virtual time by configured durations instead of computing elliptic-curve operations.
#pragma once
#include <stdint.h>

#define uECC_secp160r1 1
#define uECC_secp192r1 2
#define uECC_secp256r1 3
#define uECC_secp256k1 4
#define uECC_secp224r1 5
#ifndef uECC_CURVE
#define uECC_CURVE uECC_secp160r1
#endif
#define uECC_BYTES 32

typedef int (*uECC_RNG_Function)(uint8_t *dest, unsigned size);
void uECC_set_rng(uECC_RNG_Function rng_function);
int uECC_make_key(uint8_t public_key[uECC_BYTES * 2], uint8_t private_key[uECC_BYTES]);
int uECC_compute_public_key(const uint8_t private_key[uECC_BYTES], uint8_t public_key[uECC_BYTES * 2]);
