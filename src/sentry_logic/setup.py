from setuptools import find_packages, setup

package_name = 'sentry_logic'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=[
        'setuptools',
    ],
    zip_safe=True,
    maintainer='root',
    maintainer_email='lukepepin@outlook.com',
    description='Supervisor-side ROS 2 nodes for the On-Edge trust-monitor experiments',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'supervisor_node = sentry_logic.supervisor_node:main',
            'joint_logger = sentry_logic.joint_logger_node:main',
            'stream_wrist_kinematics = sentry_logic.stream_wrist_kinematics:main',
        ],
    },
)
