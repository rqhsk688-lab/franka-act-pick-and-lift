import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

class PickActionNodeVar1(Node):
    def __init__(self):
        super().__init__('pick_node_var2')
        
        self.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7',
            'panda_finger_joint1', 'panda_finger_joint2'
        ]
        
        self.joint_pub = {}
        for name in self.joint_names:
            self.joint_pub[name] = self.create_publisher(Float64, f'/{name}_cmd', 10)
            
        # 改良版: 机の手前でフワッと減速するソフトランディング軌道
        self.steps = [
            # 1. 高めアプローチ（上空約20cmで指を開く）
            {
                'panda_joint1': 0.0,
                'panda_joint2': 0.18,
                'panda_joint3': 0.0,
                'panda_joint4': -1.75,
                'panda_joint5': 0.0,
                'panda_joint6': 1.93,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.04,
                'panda_finger_joint2': 0.04
            },
            # 2. ★減速アプローチ（ブロック直上 5cm までスッと降りてブレーキをかける）
            {
                'panda_joint1': 0.0,
                'panda_joint2': 0.33,  # 0.18 と 0.45 の中間
                'panda_joint3': 0.0,
                'panda_joint4': -1.97, # -1.75 と -2.15 の中間
                'panda_joint5': 0.0,
                'panda_joint6': 2.30,  # 1.93 と 2.60 の中間
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.04,
                'panda_finger_joint2': 0.04
            },
            # 3. 静かに把持位置へ着地（わずかな移動量なので机に激突しない）
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
            # 4. 把持（指を0.0にしてガッチリ挟む）
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
            # 5. 中間リフト（衝撃吸収・少しだけ浮かせる）
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
            # 6. 高めリフト（通常より高く持ち上げてキープ）
            {
                'panda_joint1': 0.0,
                'panda_joint2': 0.15,
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
            "1.high approch", "2.down", "3.down2",
            "4.Grasp", "5.pick", "6.High Lift"
        ]
        
        # 2.5秒ごとに次の動作へ進む
        self.timer = self.create_timer(2.5, self.execute_step)
        self.get_logger().info("safety Pick...")

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
    node = PickActionNodeVar1()
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