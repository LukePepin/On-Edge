"""On-Edge V8 experiment system: acquisition, campaign execution, recording and replay.

The core is standard-library Python so the same code runs on the Raspberry Pi
(Ubuntu 22.04, Python 3.10, ROS 2 Humble) and on the Windows dashboard host.
ROS (rclpy) and pyserial are imported lazily, only by the modules that need them.
"""

SOFTWARE_NAME = "onedge_v8"
SOFTWARE_VERSION = "0.1.0"

# Version identifiers written into every dataset. Bump when a file format changes.
DATASET_SCHEMA = "onedge.v8.dataset/1"
CAMPAIGN_SCHEMA = "onedge.v8.campaign/1"
DAEMON_CONFIG_SCHEMA = "onedge.v8.daemon/1"
EXCLUSION_SCHEMA = "onedge.v8.exclusion/1"
ANALYSIS_DEFINITIONS = "onedge.v8.definitions/1"
