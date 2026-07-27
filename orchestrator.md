# Physical Campaign Test Matrix (60 Trials)

Manually execute the trials in this exact randomized order. For each trial:
1. Set the network loss using `tc` on the Pi (or the router).
2. Ensure the Arduino is flashed with the correct Algorithm and Node count.
3. Run the logger with the specific parameters to correctly name the CSV.
4. Execute the test and wait for the Category 0 halt.
5. Reset the UR5.

- [ ] **Trial 1**: `ZKP` | n=`10` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **Trial 2**: `ZKP` | n=`3` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=20`
- [ ] **Trial 3**: `ECC` | n=`3` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=0`
- [ ] **Trial 4**: `ECC` | n=`3` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=20`
- [ ] **Trial 5**: `ECC` | n=`3` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=0`
- [ ] **Trial 6**: `ECC` | n=`10` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **Trial 7**: `ZKP` | n=`3` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=20`
- [ ] **Trial 8**: `ECC` | n=`10` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **Trial 9**: `ZKP` | n=`10` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **Trial 10**: `ECC` | n=`3` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=10`
- [ ] **Trial 11**: `ZKP` | n=`10` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **Trial 12**: `ECC` | n=`3` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=20`
- [ ] **Trial 13**: `ECC` | n=`3` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=10`
- [ ] **Trial 14**: `ZKP` | n=`3` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=20`
- [ ] **Trial 15**: `ZKP` | n=`10` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **Trial 16**: `ECC` | n=`10` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **Trial 17**: `ECC` | n=`10` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **Trial 18**: `ECC` | n=`3` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=0`
- [ ] **Trial 19**: `ZKP` | n=`10` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **Trial 20**: `ZKP` | n=`3` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=0`
- [ ] **Trial 21**: `ZKP` | n=`10` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **Trial 22**: `ECC` | n=`10` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **Trial 23**: `ECC` | n=`10` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **Trial 24**: `ECC` | n=`3` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=0`
- [ ] **Trial 25**: `ECC` | n=`10` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **Trial 26**: `ZKP` | n=`10` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **Trial 27**: `ECC` | n=`3` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=10`
- [ ] **Trial 28**: `ZKP` | n=`10` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **Trial 29**: `ZKP` | n=`3` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=0`
- [ ] **Trial 30**: `ZKP` | n=`10` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **Trial 31**: `ECC` | n=`10` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **Trial 32**: `ZKP` | n=`10` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **Trial 33**: `ZKP` | n=`10` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=0`
- [ ] **Trial 34**: `ZKP` | n=`10` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **Trial 35**: `ZKP` | n=`3` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=10`
- [ ] **Trial 36**: `ZKP` | n=`3` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=0`
- [ ] **Trial 37**: `ECC` | n=`3` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=10`
- [ ] **Trial 38**: `ZKP` | n=`3` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=10`
- [ ] **Trial 39**: `ECC` | n=`10` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **Trial 40**: `ZKP` | n=`10` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **Trial 41**: `ECC` | n=`10` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **Trial 42**: `ZKP` | n=`3` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=10`
- [ ] **Trial 43**: `ZKP` | n=`3` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=20`
- [ ] **Trial 44**: `ZKP` | n=`3` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=0`
- [ ] **Trial 45**: `ECC` | n=`3` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=0`
- [ ] **Trial 46**: `ZKP` | n=`3` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=0`
- [ ] **Trial 47**: `ECC` | n=`10` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=0`
- [ ] **Trial 48**: `ECC` | n=`3` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=10`
- [ ] **Trial 49**: `ZKP` | n=`10` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=10`
- [ ] **Trial 50**: `ECC` | n=`10` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=20`
- [ ] **Trial 51**: `ZKP` | n=`3` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=10`
- [ ] **Trial 52**: `ZKP` | n=`3` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=20`
- [ ] **Trial 53**: `ZKP` | n=`3` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=3 -p loss:=10`
- [ ] **Trial 54**: `ECC` | n=`3` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=20`
- [ ] **Trial 55**: `ECC` | n=`10` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **Trial 56**: `ECC` | n=`3` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=20`
- [ ] **Trial 57**: `ECC` | n=`10` | Loss=`10%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=10`
- [ ] **Trial 58**: `ECC` | n=`3` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=3 -p loss:=20`
- [ ] **Trial 59**: `ZKP` | n=`10` | Loss=`20%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ZKP -p nodes:=10 -p loss:=20`
- [ ] **Trial 60**: `ECC` | n=`10` | Loss=`0%`
      Logger Command: `ros2 run sentry_logic joint_logger_node --ros-args -p algo:=ECC -p nodes:=10 -p loss:=0`
