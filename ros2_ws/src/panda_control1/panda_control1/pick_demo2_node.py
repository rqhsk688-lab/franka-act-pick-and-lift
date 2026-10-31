import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

class PickActionNode(Node):
    def __init__(self):
        super().__init__('pick_demo2_node')
        
        self.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7',
            'panda_finger_joint1', 'panda_finger_joint2'
        ]
        
        self.joint_pub = {}
        for name in self.joint_names:
            self.joint_pub[name] = self.create_publisher(Float64, f'/{name}_cmd', 10)
            
        # 元祖 pick_node と完全に同一の4ステップ関節角度
        self.steps = [
            # 1. アプローチ（直上、指オープン）
            {
                'panda_joint1': 0.0, 'panda_joint2': 0.25, 'panda_joint3': 0.0,
                'panda_joint4': -1.90, 'panda_joint5': 0.0, 'panda_joint6': 2.15,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.04, 'panda_finger_joint2': 0.04
            },
            # 2. 下降（把持位置へ着地）
            {
                'panda_joint1': 0.0, 'panda_joint2': 0.45, 'panda_joint3': 0.0,
                'panda_joint4': -2.15, 'panda_joint5': 0.0, 'panda_joint6': 2.60,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.04, 'panda_finger_joint2': 0.04
            },
            # 3. 把持（指を閉じる）
            {
                'panda_joint1': 0.0, 'panda_joint2': 0.45, 'panda_joint3': 0.0,
                'panda_joint4': -2.15, 'panda_joint5': 0.0, 'panda_joint6': 2.60,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.0, 'panda_finger_joint2': 0.0
            },
            # 4. 持ち上げ（Lift）
            {
                'panda_joint1': 0.0, 'panda_joint2': 0.25, 'panda_joint3': 0.0,
                'panda_joint4': -1.90, 'panda_joint5': 0.0, 'panda_joint6': 2.15,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.0, 'panda_finger_joint2': 0.0
            }
        ]
        
        self.current_step = 0
        self.step_names = [
            "1. アプローチ (直上)",
            "2. 下降 (把持位置)",
            "3. 把持 (Grasp)",
            "4. 持ち上げ (Lift)"
        ]
        
        # ★動作間の待ち時間を 0.7秒 に設定
        self.timer = self.create_timer(0.7, self.execute_step)
        self.get_logger().info("PickDemoNode started (0.7s interval)...")

    def execute_step(self):
        if self.current_step >= len(self.steps):
            self.get_logger().info("🎉 Pick sequence completed!")
            self.timer.cancel()
            return
            
        step_data = self.steps[self.current_step]
        self.get_logger().info(f"Executing: {self.step_names[self.current_step]}")
        
        for name, value in step_data.items():
            msg = Float64()
            msg.data = float(value)
            self.joint_pub[name].publish(msg)
            
        self.current_step += 1

def main():
    rclpy.init()
    node = PickActionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Stopped by user')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()