"""Start the V8 acquisition daemon without setting PYTHONPATH.

  python3 v8/scripts/daemon.py --config v8/config/daemon/pi_bench.json      (Pi, bench)
  python3 v8/scripts/daemon.py --config v8/config/daemon/pi_robot.json      (Pi, robot; source ROS first)
  python  v8/scripts/daemon.py --config v8/config/daemon/sim_local.json     (any PC, simulation)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from onedge_v8.daemon import main  # noqa: E402

if __name__ == "__main__":
    main()
