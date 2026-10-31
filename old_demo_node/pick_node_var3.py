import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

class PickActionNodeVar3(Node):
    def __init__(self):
        super().__init__('pick_node_var3')
        
        self.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7',
            'panda_finger_joint1', 'panda_finger_joint2'
        ]
        
        self.joint_pub = {}
        for name in self.joint_names:
            self.joint_pub[name] = self.create_publisher(Float64, f'/{name}_cmd', 10)
            
        # バリエーション3: 標準アプローチ ＋ 減速下降 ＋ ハイリフト
        self.steps = [
            # 1. 標準アプローチ (上空約15cm)
            {
                'panda_joint1': 0.0,
                'panda_joint2': 0.25,
                'panda_joint3': 0.0,
                'panda_joint4': -1.90,
                'panda_joint5': 0.0,
                'panda_joint6': 2.15,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.04,
                'panda_finger_joint2': 0.04
            },
            # 2. ★減速ステップ (直上約4cmで一旦スピードを緩める)
            {
                'panda_joint1': 0.0,
                'panda_joint2': 0.35,  # 0.25 と 0.45 の中間
                'panda_joint3': 0.0,
                'panda_joint4': -2.03, # -1.90 と -2.15 の中間
                'panda_joint5': 0.0,
                'panda_joint6': 2.38,  # 2.15 と 2.60 の中間
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.04,
                'panda_finger_joint2': 0.04
            },
            # 3. 静かに把持位置へ着地 (机にぶつからない)
            {
                'panda_joint1': 0.0,
                'panda_joint2': 0.45,
                'panda_joint3': 0.0,
                'panda_joint4': -2.15,
                'panda_joint5': 0.0,
                'panda_joint6': 2.60,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.04,
                'panda_finger_joint2': 0.04
            },
            # 4. 把持 (Grasp)
            {
                'panda_joint1': 0.0,
                'panda_joint2': 0.45,
                'panda_joint3': 0.0,
                'panda_joint4': -2.15,
                'panda_joint5': 0.0,
                'panda_joint6': 2.60,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.0,
                'panda_finger_joint2': 0.0
            },
            # 5. 中間リフト (衝撃緩和)
            {
                'panda_joint1': 0.0,
                'panda_joint2': 0.35,
                'panda_joint3': 0.0,
                'panda_joint4': -2.00,
                'panda_joint5': 0.0,
                'panda_joint6': 2.35,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.0,
                'panda_finger_joint2': 0.0
            },
            # 6. ★High Lift (通常より高く持ち上げる)
            {
                'panda_joint1': 0.0,
                'panda_joint2': 0.15,  # 高く持ち上げ
                'panda_joint3': 0.0,
                'panda_joint4': -1.70,
                'panda_joint5': 0.0,
                'panda_joint6': 1.85,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.0,
                'panda_finger_joint2': 0.0
            }
        ]
        
        self.current_step = 0
        self.step_names = [
            "1.basic", "2.down", "3.down2",
            "4.Grasp", "5.lift", "6. High Lift"
        ]
        
        self.timer = self.create_timer(2.5, self.execute_step)
        self.get_logger().info("var3 (down+High Lift)...")

    def execute_step(self):
        if self.current_step >= len(self.steps):
            self.get_logger().info("complete")
            self.timer.cancel()
            return
            
        step_data = self.steps[self.current_step]
        self.get_logger().info(f"running: {self.step_names[self.current_step]}")
        
        for name, value in step_data.items():
            msg = Float64()
            msg.data = float(value)
            self.joint_pub[name].publish(msg)
            
        self.current_step += 1

def main():
    rclpy.init()
    node = PickActionNodeVar3()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('stop')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()