import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

class PickActionNodeVar1(Node):
    def __init__(self):
        super().__init__('pick_node_var1')
        
        self.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7',
            'panda_finger_joint1', 'panda_finger_joint2'
        ]
        
        self.joint_pub = {}
        for name in self.joint_names:
            self.joint_pub[name] = self.create_publisher(Float64, f'/{name}_cmd', 10)
            
        # バリエーション1: 高めからアプローチし、高く持ち上げる軌道
        self.steps = [
            # 1. 高めアプローチ（通常より肘を伸ばし、高所で指オープン）
            {
                'panda_joint1': 0.0,
                'panda_joint2': 0.18,  # 通常(0.25)より起こす
                'panda_joint3': 0.0,
                'panda_joint4': -1.75, # 通常(-1.90)より伸ばす
                'panda_joint5': 0.0,
                'panda_joint6': 1.93,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.04,
                'panda_finger_joint2': 0.04
            },
            # 2. 下降（確実に掴める黄金の把持位置へ降ろす）
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
            # 3. 把持（指を0.0にして全力で挟み込む）
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
            # 4. 中間リフト（衝撃吸収・少し浮かせる）
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
            # 5. 高めリフト（通常より高く堂々と持ち上げる）
            {
                'panda_joint1': 0.0,
                'panda_joint2': 0.15,  # 通常(0.25)より高く持ち上げる
                'panda_joint3': 0.0,
                'panda_joint4': -1.70, # より高く引き上げる
                'panda_joint5': 0.0,
                'panda_joint6': 1.85,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.0,
                'panda_finger_joint2': 0.0
            }
        ]
        
        self.current_step = 0
        self.step_names = [
            "1. 高めアプローチ", "2. 把持位置へ下降",
            "3. 把持 (Grasp)", "4. 中間浮かし", "5. 高く持ち上げ (High Lift)"
        ]
        
        self.timer = self.create_timer(3.0, self.execute_step)
        self.get_logger().info("Pickバリエーション1を開始します...")

    def execute_step(self):
        if self.current_step >= len(self.steps):
            self.get_logger().info("★ バリエーション1 完了！")
            self.timer.cancel()
            return
            
        step_data = self.steps[self.current_step]
        self.get_logger().info(f"実行中: {self.step_names[self.current_step]}")
        
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
        node.get_logger().info('停止しました')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()