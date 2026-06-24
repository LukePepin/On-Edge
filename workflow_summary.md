# Edge Node Development Workflow

Developing directly on the Raspberry Pi proved to be slow and fraught with compiler architecture mismatches (specifically, ARM64 vs ARM Cortex-M4 float ABI issues). 

The new, much more efficient workflow separates **development** from **execution**. You will do all the heavy lifting on your fast Windows PC, and use the Pi strictly for what it's good at: running the ROS 2 environment and communicating with the hardware.

Yes, this approach works perfectly and is the standard industry practice for embedded systems.

## The New Workflow

### 1. Firmware Development & Compilation (Windows)
All Arduino code (the `edge_node` firmware) will be developed and compiled on your Windows PC.
*   **Why:** Windows has the correct pre-compiled `libmicroros.a` libraries for the Cortex-M4 architecture and compiles much faster.
*   **Tools:** VS Code with PlatformIO (or Arduino IDE).
*   **Action:** Write your micro-ROS code, hit "Build", and compile the `firmware.bin` in seconds instead of minutes.

### 2. Firmware Flashing (Windows)
You will upload the compiled firmware to the Arduino Nano 33 BLE directly from Windows.
*   **Action:** Plug the Arduino into your PC, double-tap the reset button to enter bootloader mode, and use PlatformIO's "Upload" button (or the `bossac` command) to flash the board.

### 3. Hardware Deployment (Raspberry Pi)
Once flashed, the Arduino is completely self-sufficient.
*   **Action:** Unplug the Arduino from your PC and plug it into the Raspberry Pi via USB.

### 4. Supervisor & Network Management (Raspberry Pi via SSH)
The Pi's only job is to act as the micro-ROS supervisor and bridge the Arduino to the wider ROS 2 network.
*   **How to access:** You will SSH into the Pi from your Windows terminal (e.g., `ssh seeker@<PI_IP_ADDRESS>`).
*   **Action:** From the SSH session, you will start the `MicroXRCEAgent` to listen to the Arduino:
    ```bash
    sudo chmod 666 /dev/ttyACM0
    MicroXRCEAgent serial --dev /dev/ttyACM0 -b 115200
    ```
*   **Action:** In a second SSH session, you can run standard ROS 2 commands to verify the data is flowing:
    ```bash
    ros2 topic echo /heartbeat
    ```

---

> [!TIP]
> **To summarize:** Code and flash on **Windows** -> Plug Arduino into **Pi** -> Run the Agent on **Pi via SSH**. 

This completely eliminates the need to run VS Code, PlatformIO, or heavy C++ compilers on the Pi, solving the speed and architecture issues simultaneously!
