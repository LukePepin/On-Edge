#!/bin/bash
set -e

echo "Building cycle-accurate uECC_verify wrapper..."

# 1. Clone micro-ecc if not already cloned
if [ ! -d "micro-ecc" ]; then
    echo "Cloning micro-ecc repository..."
    git clone https://github.com/kmackay/micro-ecc.git
fi

# 2. Compile micro-ecc to an object file with Position Independent Code
echo "Compiling micro-ecc..."
gcc -c -fPIC micro-ecc/uECC.c -o uECC.o

# 3. Compile the wrapper and link to micro-ecc as a shared library
echo "Compiling shared library libuecc_wrapper.so..."
gcc -shared -fPIC -o libuecc_wrapper.so uecc_wrapper.c uECC.o

# 4. Cleanup object files
rm uECC.o

echo "Done! libuecc_wrapper.so is ready."
