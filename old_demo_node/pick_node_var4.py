import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

class PickActionNodeVar4(Node):
    def __init__(self):
        super().__init__('pick_node_var4')
        
        self.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7',
            'panda_finger_joint1', 'panda_finger_joint2'
        ]
        
        self.joint_pub = {}
        for name in self.joint_names:
            self.joint_pub[name] = self.create_publisher(Float64, f'/{name}_cmd', 10)
            
        # バリエーション4: 真上までゆっくり展開 ＋ ソフトランディング下降
        self.steps = [
            # 1. ★スローテイクオフ (初期位置から真上へ向けて、ゆっくり中間まで腕を伸ばす)
            {
                'panda_joint1': 0.0,
                'panda_joint2': 0.10,  # 緩やかに前傾
                'panda_joint3': 0.0,
                'panda_joint4': -0.90, # 肘を半分だけ曲げてゆっくり前進
                'panda_joint5': 0.0,
                'panda_joint6': 1.10,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.04,
                'panda_finger_joint2': 0.04
            },
            # 2. 高めアプローチ (真上約20cmにゆっくり到着)
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
            # 3. 減速下降 (直上5cmでブレーキ)
            {
                'panda_joint1': 0.0,
                'panda_joint2': 0.33,
                'panda_joint3': 0.0,
                'panda_joint4': -1.97,
                'panda_joint5': 0.0,
                'panda_joint6': 2.30,
                'panda_joint7': 0.785,
                'panda_finger_joint1': 0.04,
                'panda_finger_joint2': 0.04
            },
            # 4. 静かに把持位置へ着地
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
            # 5. 把持 (Grasp)
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
            # 6. 中間リフト
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
            # 7. High Lift
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
            "1. slowly", "2.high approch", "3.down",
            "4.down2", "5.Grasp", "6.lift", "7. High Lift"
        ]
        
        self.timer = self.create_timer(2.5, self.execute_step)
        self.get_logger().info("var4 (slow++softlanding) ...")

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
    node = PickActionNodeVar4()
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