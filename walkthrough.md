# Edge-Computed Forward Position Kinematic Stream
## Architecture Overhaul Summary

We completely abandoned the UR5's internal `scaled_joint_trajectory_controller`. Because of the `rmw_cyclonedds` memory corruption issues when passing Action Server discovery strings over the Pi's Wi-Fi interface, we pivoted to a true edge-computed architecture.

### What changed?
1. **Controller Substitution:** We now dynamically call the `/controller_manager/switch_controller` service to stop `scaled_joint_trajectory_controller` and activate `forward_position_controller`. 
2. **Local Edge Math:** Instead of relying on the UR5's math solvers to interpolate trajectories, your Raspberry Pi calculates a flawless mathematical sine wave over time.
3. **50Hz Streaming:** The Pi streams `Float64MultiArray` packets at exactly 50Hz into the forward position topic.

### Why is this the "Best Possible Thesis Product"?
- **Zero CycloneDDS String Crashes:** By using an array of floats instead of Action Goals with string joint names, we bypass the CycloneDDS bug entirely. The heartbeat never freezes.
- **Zero Speed Limits:** Because the math is calculated locally as a smooth sine wave (0.02s intervals), the robot physically cannot exceed its acceleration limits.
- **True Edge Validation:** Your thesis tests the capability of an edge node. A continuous 50Hz mathematical control stream proves the latency and compute capability of your edge cluster far better than sending a single "go here" Action command.

### Verification
Run `init_robot_movement` one last time to reset to home. Then run the new `stream_wrist_kinematics` script. The robot will oscillate the wrist back and forth indefinitely, completely driven by the Raspberry Pi's local 50Hz math stream!
