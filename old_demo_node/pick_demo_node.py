import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

class PickDemoNode(Node):
    def __init__(self):
        super().__init__('pick_demo_node')
        
        self.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7',
            'panda_finger_joint1', 'panda_finger_joint2'
        ]
        
        self.joint_pub = {}
        for name in self.joint_names:
            self.joint_pub[name] = self.create_publisher(Float64, f'/{name}_cmd', 10)
            
        # 実績のある姿勢リスト
        self.steps = [
            # 1. 高めアプローチ（上空約20cmで指を開く）
            {
                'panda_joint1': 0.0, 'panda_joint2': 0.18, 'panda_joint3': 0.0,
                'panda_joint4': -1.75, 'panda_joint5': 0.0, 'panda_joint6': 1.93,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.04, 'panda_finger_joint2': 0.04
            },
            # 2. 減速アプローチ（ブロック直上 5cm までスッと降りる）
            {
                'panda_joint1': 0.0, 'panda_joint2': 0.33, 'panda_joint3': 0.0,
                'panda_joint4': -1.97, 'panda_joint5': 0.0, 'panda_joint6': 2.30,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.04, 'panda_finger_joint2': 0.04
            },
            # 3. 把持位置へ着地
            {
                'panda_joint1': 0.0, 'panda_joint2': 0.45, 'panda_joint3': 0.0,
                'panda_joint4': -2.15, 'panda_joint5': 0.0, 'panda_joint6': 2.60,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.04, 'panda_finger_joint2': 0.04
            },
            # 4. 把持（指を閉じる）
            {
                'panda_joint1': 0.0, 'panda_joint2': 0.45, 'panda_joint3': 0.0,
                'panda_joint4': -2.15, 'panda_joint5': 0.0, 'panda_joint6': 2.60,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.0, 'panda_finger_joint2': 0.0
            },
            # 5. 少し浮かす
            {
                'panda_joint1': 0.0, 'panda_joint2': 0.35, 'panda_joint3': 0.0,
                'panda_joint4': -2.00, 'panda_joint5': 0.0, 'panda_joint6': 2.35,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.0, 'panda_finger_joint2': 0.0
            },
            # 6. 高く持ち上げる（完了）
            {
                'panda_joint1': 0.0, 'panda_joint2': 0.15, 'panda_joint3': 0.0,
                'panda_joint4': -1.70, 'panda_joint5': 0.0, 'panda_joint6': 1.85,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.0, 'panda_finger_joint2': 0.0
            }
        ]
        
        self.current_step = 0
        self.step_names = [
            "1. High Approach", "2. Down", "3. Land",
            "4. Grasp", "5. Pick", "6. High Lift"
        ]
        
        # 0.4秒（静止時間を排除）
        self.timer = self.create_timer(0.4, self.execute_step)
        self.get_logger().info("PickDemoNode started (1.2s interval)...")

    def execute_step(self):
        if self.current_step >= len(self.steps):
            self.get_logger().info("Demo sequence completed successfully!")
            self.timer.cancel()
            return
            
        step_data = self.steps[self.current_step]
        self.get_logger().info(f"Step {self.current_step + 1}: {self.step_names[self.current_step]}")
        
        for name, value in step_data.items():
            msg = Float64()
            msg.data = float(value)
            self.joint_pub[name].publish(msg)
            
        self.current_step += 1

def main():
    rclpy.init()
    node = PickDemoNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Interrupted')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()