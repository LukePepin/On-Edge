# The Air-Gapped Execution Protocol (60 Trials)

For every single trial, you must execute these exact steps in sequence to guarantee experimental integrity.

## [ ] Trial 1: `ZKP` | n=`3` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_1_ZKP_n3_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=1 -p algo:=ZKP -p nodes:=3 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_1_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 2: `ZKP` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_2_ZKP_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=2 -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_2_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 3: `ECC` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_3_ECC_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=3 -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_3_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 4: `ZKP` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_4_ZKP_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=4 -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_4_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 5: `ZKP` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_5_ZKP_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=5 -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_5_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 6: `ECC` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_6_ECC_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=6 -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_6_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 7: `ECC` | n=`3` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_7_ECC_n3_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=7 -p algo:=ECC -p nodes:=3 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_7_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 8: `ECC` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_8_ECC_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=8 -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_8_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 9: `ECC` | n=`3` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_9_ECC_n3_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=9 -p algo:=ECC -p nodes:=3 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_9_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 10: `ECC` | n=`3` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_10_ECC_n3_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=10 -p algo:=ECC -p nodes:=3 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_10_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 11: `ECC` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_11_ECC_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=11 -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_11_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 12: `ECC` | n=`3` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_12_ECC_n3_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=12 -p algo:=ECC -p nodes:=3 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_12_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 13: `ZKP` | n=`3` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_13_ZKP_n3_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=13 -p algo:=ZKP -p nodes:=3 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_13_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 14: `ECC` | n=`3` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_14_ECC_n3_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=14 -p algo:=ECC -p nodes:=3 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_14_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 15: `ECC` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_15_ECC_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=15 -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_15_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 16: `ZKP` | n=`3` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_16_ZKP_n3_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=16 -p algo:=ZKP -p nodes:=3 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_16_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 17: `ECC` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_17_ECC_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=17 -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_17_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 18: `ZKP` | n=`3` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_18_ZKP_n3_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=18 -p algo:=ZKP -p nodes:=3 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_18_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 19: `ZKP` | n=`3` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_19_ZKP_n3_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=19 -p algo:=ZKP -p nodes:=3 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_19_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 20: `ZKP` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_20_ZKP_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=20 -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_20_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 21: `ECC` | n=`3` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_21_ECC_n3_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=21 -p algo:=ECC -p nodes:=3 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_21_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 22: `ZKP` | n=`3` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_22_ZKP_n3_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=22 -p algo:=ZKP -p nodes:=3 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_22_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 23: `ECC` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_23_ECC_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=23 -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_23_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 24: `ZKP` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_24_ZKP_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=24 -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_24_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 25: `ZKP` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_25_ZKP_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=25 -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_25_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 26: `ECC` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_26_ECC_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=26 -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_26_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 27: `ZKP` | n=`3` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_27_ZKP_n3_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=27 -p algo:=ZKP -p nodes:=3 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_27_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 28: `ZKP` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_28_ZKP_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=28 -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_28_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 29: `ECC` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_29_ECC_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=29 -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_29_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 30: `ECC` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_30_ECC_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=30 -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_30_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 31: `ZKP` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_31_ZKP_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=31 -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_31_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 32: `ZKP` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_32_ZKP_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=32 -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_32_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 33: `ZKP` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_33_ZKP_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=33 -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_33_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 34: `ECC` | n=`3` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_34_ECC_n3_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=34 -p algo:=ECC -p nodes:=3 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_34_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 35: `ZKP` | n=`3` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_35_ZKP_n3_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=35 -p algo:=ZKP -p nodes:=3 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_35_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 36: `ZKP` | n=`3` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_36_ZKP_n3_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=36 -p algo:=ZKP -p nodes:=3 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_36_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 37: `ZKP` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_37_ZKP_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=37 -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_37_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 38: `ZKP` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_38_ZKP_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=38 -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_38_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 39: `ZKP` | n=`3` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_39_ZKP_n3_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=39 -p algo:=ZKP -p nodes:=3 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_39_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 40: `ECC` | n=`3` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_40_ECC_n3_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=40 -p algo:=ECC -p nodes:=3 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_40_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 41: `ZKP` | n=`3` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_41_ZKP_n3_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=41 -p algo:=ZKP -p nodes:=3 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_41_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 42: `ZKP` | n=`3` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_42_ZKP_n3_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=42 -p algo:=ZKP -p nodes:=3 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_42_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 43: `ZKP` | n=`3` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_43_ZKP_n3_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=43 -p algo:=ZKP -p nodes:=3 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_43_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 44: `ECC` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_44_ECC_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=44 -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_44_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 45: `ZKP` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_45_ZKP_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=45 -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_45_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 46: `ECC` | n=`3` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_46_ECC_n3_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=46 -p algo:=ECC -p nodes:=3 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_46_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 47: `ECC` | n=`3` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_47_ECC_n3_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=47 -p algo:=ECC -p nodes:=3 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_47_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 48: `ECC` | n=`3` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_48_ECC_n3_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=48 -p algo:=ECC -p nodes:=3 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_48_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 49: `ECC` | n=`3` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_49_ECC_n3_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=49 -p algo:=ECC -p nodes:=3 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_49_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 50: `ECC` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_50_ECC_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=50 -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_50_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 51: `ECC` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_51_ECC_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=51 -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_51_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 52: `ECC` | n=`3` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_52_ECC_n3_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=52 -p algo:=ECC -p nodes:=3 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_52_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 53: `ZKP` | n=`10` | Loss=`10%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 10%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_53_ZKP_n10_loss10.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=53 -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_53_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 54: `ZKP` | n=`3` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_54_ZKP_n3_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=54 -p algo:=ZKP -p nodes:=3 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_54_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 55: `ECC` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_55_ECC_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=55 -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_55_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 56: `ECC` | n=`3` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_56_ECC_n3_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=56 -p algo:=ECC -p nodes:=3 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_56_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 57: `ZKP` | n=`10` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ZKP firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_57_ZKP_n10_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=57 -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_57_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 58: `ZKP` | n=`3` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ZKP firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_58_ZKP_n3_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=58 -p algo:=ZKP -p nodes:=3 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_58_ZKP_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 59: `ECC` | n=`3` | Loss=`0%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 0%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 2 Arduinos are powered and running the ECC firmware. (n=3 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_59_ECC_n3_loss0.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=59 -p algo:=ECC -p nodes:=3 -p loss:=0`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_59_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

## [ ] Trial 60: `ECC` | n=`10` | Loss=`20%`
- [ ] **1. Network Provisioning**: Run `sudo tc qdisc add dev wlan0 root netem loss 20%` on the Pi (if loss > 0, otherwise ensure it's cleared with `sudo tc qdisc del dev wlan0 root`).
- [ ] **2. Hardware Provisioning**: Ensure exactly 9 Arduinos are powered and running the ECC firmware. (n=10 total nodes)
- [ ] **3. Instrumentation Boot (TShark)**: Start the sniffer to capture FastDDS queue depth (Phase 3.6):
      `tshark -i wlan0 -f "udp" -w data/trial_60_ECC_n10_loss20.pcap`
- [ ] **4. Instrumentation Boot (Logger)**: Start the ROS 2 logger to capture IMU and Trust Score (Phase 3.5):
      `ros2 run sentry_logic joint_logger_node --ros-args -p trial:=60 -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **5. Kinematic Spool-Up**: Start the UR5 motion script (`ros2 run sentry_logic stream_wrist_kinematics`) and wait for the Trust Score to stabilize for 8 cycles.
- [ ] **6. The Strike**: Trigger the 256-byte payload by calling the service in a new terminal:
      `ros2 service call /inject_attack std_srvs/srv/Trigger`
- [ ] **7. Data Archival**: Once the UR5 physically halts, press Ctrl+C on the `tshark` and `joint_logger_node` terminals. (The CSV is already correctly named `trial_60_ECC_...csv`).
- [ ] **8. The Reset**: Clear the network rules (`sudo tc qdisc del dev wlan0 root`), clear the UR5 teach pendant safety fault, and prepare for the next trial.

---

