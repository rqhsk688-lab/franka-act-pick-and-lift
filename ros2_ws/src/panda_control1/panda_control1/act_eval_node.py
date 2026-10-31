#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64
import torch

try:
    from lerobot.policies.act.modeling_act import ACTPolicy
except ImportError:
    from lerobot.common.policies.act.modeling_act import ACTPolicy

# Franka の関節定義（9軸）
ARM_JOINT_NAMES = [
    'panda_joint1',
    'panda_joint2',
    'panda_joint3',
    'panda_joint4',
    'panda_joint5',
    'panda_joint6',
    'panda_joint7',
]
FINGER_JOINT_NAMES = [
    'panda_finger_joint1',
    'panda_finger_joint2',
]
ALL_JOINT_NAMES = ARM_JOINT_NAMES + FINGER_JOINT_NAMES


class FrankaACTInferenceNode(Node):
    def __init__(self, model_path: str, control_rate_hz: float = 20.0):
        super().__init__('franka_act_infer_node')
        self.control_rate_hz = control_rate_hz
        self.device = torch.device('cpu')

        self.get_logger().info(f"Loading ACT Policy from: {model_path}")
        model_dir = Path(model_path).resolve()

        # stats.json が同封されていれば読み込む
        stats_file = model_dir / "stats.json"
        dataset_stats = None
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                dataset_stats = json.load(f)
            self.get_logger().info("Loaded normalization stats from stats.json")

        # モデルの読み込み
        try:
            if dataset_stats is not None:
                self.policy = ACTPolicy.from_pretrained(str(model_dir), dataset_stats=dataset_stats)
            else:
                self.policy = ACTPolicy.from_pretrained(str(model_dir))
        except TypeError:
            self.policy = ACTPolicy.from_pretrained(str(model_dir))

        self.policy.eval()
        self.policy.to(self.device)
        self.policy.reset()  # 内部のアクションキューをリセット
        self.get_logger().info("ACT Policy initialized successfully on CPU!")

        # 2. 各関節コマンド用 Publisher の作成 (std_msgs/Float64)
        self.cmd_publishers = {
            name: self.create_publisher(Float64, f'/{name}_cmd', 10)
            for name in ALL_JOINT_NAMES
        }

        # 3. 現在の関節状態用 Subscriber (/joint_states)
        self.subscription = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )

        self.latest_joint_state = None
        self.step_count = 0

        # 4. 制御ループタイマー (20Hz = 0.05秒周期)
        timer_period = 1.0 / self.control_rate_hz
        self.timer = self.create_timer(timer_period, self.control_loop)
        self.get_logger().info(f"Inference loop started at {self.control_rate_hz} Hz. Waiting for /joint_states...")

    def joint_state_callback(self, msg: JointState):
        """Gazebo から配信される /joint_states から9関節の現在位置を正しい順序で抽出"""
        name_to_pos = dict(zip(msg.name, msg.position))
        
        # 全関節がメッセージに含まれているか確認
        if all(name in name_to_pos for name in ALL_JOINT_NAMES):
            current_positions = [name_to_pos[name] for name in ALL_JOINT_NAMES]
            self.latest_joint_state = np.array(current_positions, dtype=np.float32)

    def control_loop(self):
        """20Hz で実行される推論 & 指令パブリッシュループ"""
        if self.latest_joint_state is None:
            return  # 関節情報がまだ届いていなければ待機

        # 学習時と同じく (1, 9) の形状で observation と environment_state を作成
        state_tensor = torch.tensor(
            self.latest_joint_state, 
            dtype=torch.float32, 
            device=self.device
        ).unsqueeze(0)  # (1, 9)

        obs = {
            'observation.state': state_tensor,
            'observation.environment_state': state_tensor,
        }

        # 推論
        with torch.no_grad():
            action = self.policy.select_action(obs).cpu().numpy().flatten()  # (9,)

        # 各関節へ Float64 メッセージをパブリッシュ
        for i, name in enumerate(ALL_JOINT_NAMES):
            cmd_msg = Float64()
            cmd_msg.data = float(action[i])
            self.cmd_publishers[name].publish(cmd_msg)

        # 1秒ごとにログを表示
        if self.step_count % int(self.control_rate_hz) == 0:
            arm_str = [f"{q:.2f}" for q in action[:7]]
            gripper_str = f"{action[7]:.3f}"
            self.get_logger().info(
                f"[Step {self.step_count:4d}] Arm: {arm_str} | Gripper: {gripper_str}"
            )

        self.step_count += 1


def main():
    parser = argparse.ArgumentParser(description='ACTPolicy inference node for Franka (ROS 2)')
    parser.add_argument(
        '--model-path',
        type=str,
        default='./franka_act_policy',
        help='Path to the trained ACTPolicy model directory'
    )
    parser.add_argument(
        '--rate',
        type=float,
        default=20.0,
        help='Control frequency in Hz (default: 20.0)'
    )
    args = parser.parse_args()

    rclpy.init()
    node = FrankaACTInferenceNode(model_path=args.model_path, control_rate_hz=args.rate)
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down inference node...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()