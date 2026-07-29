# The Air-Gapped Execution Protocol (60 Trials - H1/H2 MTTR Isolation)

For every single trial, you must execute these exact steps in sequence to guarantee experimental integrity.

## [ ] Trial 1: `ECC` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_1_ECC_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=1 -p algo:=ECC -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_1_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 2: `ECC` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_2_ECC_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=2 -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_2_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 3: `ZKP` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_3_ZKP_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=3 -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_3_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 4: `CLOUD` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_4_CLOUD_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=4 -p algo:=CLOUD -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_4_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 5: `CLOUD` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_5_CLOUD_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=5 -p algo:=CLOUD -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_5_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 6: `ECC` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_6_ECC_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=6 -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_6_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 7: `ZKP` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_7_ZKP_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=7 -p algo:=ZKP -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_7_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 8: `ZKP` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_8_ZKP_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=8 -p algo:=ZKP -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_8_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 9: `ECC` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_9_ECC_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=9 -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_9_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 10: `CLOUD` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_10_CLOUD_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=10 -p algo:=CLOUD -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_10_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 11: `CLOUD` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_11_CLOUD_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=11 -p algo:=CLOUD -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_11_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 12: `ECC` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_12_ECC_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=12 -p algo:=ECC -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_12_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 13: `ECC` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_13_ECC_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=13 -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_13_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 14: `ZKP` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_14_ZKP_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=14 -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_14_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 15: `ECC` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_15_ECC_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=15 -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_15_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 16: `ZKP` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_16_ZKP_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=16 -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_16_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 17: `CLOUD` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_17_CLOUD_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=17 -p algo:=CLOUD -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_17_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 18: `ECC` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_18_ECC_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=18 -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_18_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 19: `ZKP` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_19_ZKP_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=19 -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_19_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 20: `CLOUD` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_20_CLOUD_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=20 -p algo:=CLOUD -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_20_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 21: `ECC` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_21_ECC_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=21 -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_21_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 22: `CLOUD` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_22_CLOUD_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=22 -p algo:=CLOUD -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_22_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 23: `ZKP` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_23_ZKP_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=23 -p algo:=ZKP -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_23_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 24: `ECC` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_24_ECC_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=24 -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_24_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 25: `ZKP` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_25_ZKP_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=25 -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_25_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 26: `ECC` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_26_ECC_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=26 -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_26_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 27: `CLOUD` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_27_CLOUD_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=27 -p algo:=CLOUD -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_27_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 28: `ZKP` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_28_ZKP_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=28 -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_28_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 29: `ECC` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_29_ECC_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=29 -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_29_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 30: `ZKP` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_30_ZKP_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=30 -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_30_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 31: `CLOUD` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_31_CLOUD_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=31 -p algo:=CLOUD -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_31_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 32: `ECC` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_32_ECC_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=32 -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_32_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 33: `ECC` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_33_ECC_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=33 -p algo:=ECC -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_33_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 34: `ECC` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_34_ECC_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=34 -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_34_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 35: `ZKP` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_35_ZKP_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=35 -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_35_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 36: `CLOUD` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_36_CLOUD_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=36 -p algo:=CLOUD -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_36_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 37: `ECC` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_37_ECC_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=37 -p algo:=ECC -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_37_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 38: `ZKP` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_38_ZKP_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=38 -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_38_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 39: `ECC` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_39_ECC_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=39 -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_39_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 40: `ZKP` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_40_ZKP_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=40 -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_40_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 41: `CLOUD` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_41_CLOUD_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=41 -p algo:=CLOUD -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_41_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 42: `ZKP` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_42_ZKP_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=42 -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_42_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 43: `ZKP` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_43_ZKP_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=43 -p algo:=ZKP -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_43_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 44: `CLOUD` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_44_CLOUD_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=44 -p algo:=CLOUD -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_44_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 45: `ECC` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_45_ECC_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=45 -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_45_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 46: `ECC` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_46_ECC_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=46 -p algo:=ECC -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_46_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 47: `CLOUD` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_47_CLOUD_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=47 -p algo:=CLOUD -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_47_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 48: `ECC` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_48_ECC_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=48 -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_48_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 49: `ZKP` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_49_ZKP_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=49 -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_49_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 50: `ZKP` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_50_ZKP_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=50 -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_50_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 51: `CLOUD` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_51_CLOUD_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=51 -p algo:=CLOUD -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_51_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 52: `ZKP` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_52_ZKP_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=52 -p algo:=ZKP -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_52_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 53: `CLOUD` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_53_CLOUD_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=53 -p algo:=CLOUD -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_53_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 54: `CLOUD` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 20%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_54_CLOUD_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=54 -p algo:=CLOUD -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_54_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 55: `CLOUD` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_55_CLOUD_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=55 -p algo:=CLOUD -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_55_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 56: `CLOUD` | n=`10` | Loss=`30%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 30%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_56_CLOUD_n10_loss30.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=56 -p algo:=CLOUD -p nodes:=10 -p loss:=30`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_56_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 57: `ZKP` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_57_ZKP_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=57 -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_57_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 58: `CLOUD` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_58_CLOUD_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=58 -p algo:=CLOUD -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_58_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 59: `CLOUD` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc replace dev wlan0 root netem loss 10%` on the Pi.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the CLOUD firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_59_CLOUD_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=59 -p algo:=CLOUD -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_59_CLOUD_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

## [ ] Trial 60: `ZKP` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc del dev wlan0 root 2>/dev/null || true` on the Pi to ensure no artificial loss.
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `mkdir -p data && sudo tshark -i wlan0 -f "udp" -w data/trial_60_ZKP_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger --ros-args -p trial:=60 -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_60_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root 2>/dev/null || true`), then automatically clear the UR5 safety fault by running `python3 scripts/clear_safety_stop.py`.

---

