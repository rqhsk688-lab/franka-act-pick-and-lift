#!/usr/bin/env python3
"""
デモ収集用ノード
コサイン連続軌道
持ち上げ姿勢 (Q_LIFT) を高く直立寄りに設定、降下時の姿勢との混同を解消
"""

import math
import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

ARM_JOINT_NAMES = [
    'panda_joint1', 'panda_joint2', 'panda_joint3',
    'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7'
]
FINGER_JOINT_NAMES = ['panda_finger_joint1', 'panda_finger_joint2']

# 1. 初期姿勢 
Q_HOME     = np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785])

# 2. 直上アプローチ (上空約15cm)
Q_APPROACH = np.array([0.0,  0.220, 0.0, -1.800, 0.0, 2.000, 0.785])

# 3. 把持
Q_PICK     = np.array([0.0,  0.421, 0.0, -2.221, 0.0, 2.700, 0.785])

# 4. 持ち上げ完了 (高く直立寄りに引き上げる姿勢: アプローチと差別化)
Q_LIFT     = np.array([0.0, -0.100, 0.0, -1.750, 0.0, 1.950, 0.785])

GRIPPER_OPEN  = 0.04
GRIPPER_CLOSE = 0.00


def smooth_interp(q_start, q_end, ratio):
    """コサイン曲線による滑らかな加減速補間"""
    ratio = np.clip(ratio, 0.0, 1.0)
    smooth_ratio = (1.0 - math.cos(math.pi * ratio)) / 2.0
    return q_start + (q_end - q_start) * smooth_ratio


class PickDemoNode(Node):
    def __init__(self):
        super().__init__('pick_smooth_node')
        self.rate_hz = 50.0
        self.timer_period = 1.0 / self.rate_hz
        self.time_elapsed = 0.0
        self.total_duration = 7.2  # 全体で約7.2秒の連続動作

        self.arm_publishers = [
            self.create_publisher(Float64, f'/{name}_cmd', 10)
            for name in ARM_JOINT_NAMES
        ]
        self.finger_publishers = [
            self.create_publisher(Float64, f'/{name}_cmd', 10)
            for name in FINGER_JOINT_NAMES
        ]

        self.timer = self.create_timer(self.timer_period, self.control_loop)
        self.get_logger().info("start")

    def control_loop(self):
        t = self.time_elapsed

        if t < 2.5:
            # Phase 1 (0.0〜2.5s): Home -> 直上アプローチ（指オープン）
            ratio = t / 2.5
            arm_cmd = smooth_interp(Q_HOME, Q_APPROACH, ratio)
            gripper_cmd = GRIPPER_OPEN

        elif t < 4.2:
            # Phase 2 (2.5〜4.2s: 1.7秒間): アプローチ -> 把持位置へ降下
            ratio = (t - 2.5) / 1.7
            arm_cmd = smooth_interp(Q_APPROACH, Q_PICK, ratio)
            gripper_cmd = GRIPPER_OPEN

        elif t < 4.8:
            # Phase 3 (4.2〜4.8s: 0.6秒間): ブロックを挟み込む
            arm_cmd = Q_PICK
            gripper_cmd = GRIPPER_CLOSE

        elif t < 6.6:
            # Phase 4 (4.8〜6.6s: 1.8秒間): しっかりリフト
            ratio = (t - 4.8) / 1.8
            arm_cmd = smooth_interp(Q_PICK, Q_LIFT, ratio)
            gripper_cmd = GRIPPER_CLOSE

        else:
            # Phase 5 (6.6〜7.2s: 0.6秒間): 持ち上げ姿勢をキープ
            arm_cmd = Q_LIFT
            gripper_cmd = GRIPPER_CLOSE

        # アーム関節指令の送信 (50Hz)
        for pub, val in zip(self.arm_publishers, arm_cmd):
            pub.publish(Float64(data=float(val)))

        # グリッパー指令の送信
        for pub in self.finger_publishers:
            pub.publish(Float64(data=float(gripper_cmd)))

        if t >= self.total_duration:
            self.get_logger().info("complete")
            self.timer.cancel()
            return

        self.time_elapsed += self.timer_period


def main():
    rclpy.init()
    node = PickDemoNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()