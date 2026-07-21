# Academic Audit: Phase 2 Experimental Methodology

As your advisor, I am reviewing your methodology for Phase 2.4 and 2.5. While the infrastructure is excellent, if you submit this methodology as it currently stands in a thesis defense, your defense committee will tear it apart. 

Here are the four most glaring academic vulnerabilities in your current experiment design.

## 1. The ZKP "Tax" is a For-Loop Mock (Fatal Flaw)
**The Problem:** In `main.cpp`, to simulate the escalating computational tax of selective disclosure, you are running a dummy integer loop (`dummy += (j % 3)`). 
**The Critique:** This is academically invalid. You cannot claim to measure the "ZKP Security Tax" without actually executing Zero-Knowledge cryptography. Real selective disclosure protocols (like Schnorr commitments or Bulletproofs) involve heavy multi-scalar multiplications (MSM) and elliptic curve point additions. These operations stress the Cortex-M4's ALU, branch predictor, and memory bus in ways a simple `for` loop does not. 
**The Fix:** You must replace the dummy loop with actual cryptographic primitives. For example, for every 32 bytes of payload, execute one actual `uECC_shared_secret()` or elliptic curve point multiplication. 

## 2. You are Profiling the Prover, Not the Verifier
**The Problem:** Your `profile_disclosure_single()` function executes `uECC_make_key()`, which simulates *generating* a proof (the Prover).
**The Critique:** In your thesis architecture, the most dangerous bottleneck is the **Verifier** (e.g., the robot receiving an Emergency Stop command). In asymmetric cryptography, verifying a signature or a ZKP takes significantly more CPU cycles than generating one. If you only prove that the edge node can *generate* a key in 111ms, you haven't proven that the UR5 robot can *verify* it before the 500ms safety ceiling expires.
**The Fix:** You must generate a keypair in `setup()`, and then benchmark `uECC_verify()` or `uECC_shared_secret()` in your profiling loop to capture the true worst-case latency.

## 3. Ignoring Network Stack Interrupts (RTOS Jitter)
**The Problem:** You are measuring the algorithmic latency in a vacuum.
**The Critique:** While `DWT_CYCCNT` accurately tracks exact CPU cycles, it does not stop hardware interrupts. In a real deployed MANET, the edge node will be bombarded with ROS 2 packets, Bluetooth stack events, and serial interrupts. If an interrupt fires during your cryptography, the CPU pauses the math to handle the network packet. This pushes the total *wall-clock* execution time up. Your thesis must prove the 500ms safety ceiling holds up *under network load*, not just in an empty test harness.
**The Fix:** You need to bombard the Arduino with network traffic (e.g., your Python bridge sending dummy data) *while* the crypto profiling is running, to see how much RTOS jitter degrades the 111ms baseline.

## 4. Weak Entropy Generation (TRNG)
**The Problem:** Your `RNG()` function uses the standard C library `rand()`. 
**The Critique:** Standard `rand()` is a simple Linear Congruential Generator (LCG). Real hardware cryptography requires a True Random Number Generator (TRNG) to read hardware entropy. Fetching entropy from the silicon takes CPU clock cycles. By using a fast `rand()` loop, you are artificially lowering your ECDSA latency.
**The Fix:** The nRF52840 inside the Nano 33 BLE has a built-in hardware TRNG. You must map your `uECC_set_rng()` function to read from the actual Nordic TRNG registers to get an academically valid cycle count.
