#!/usr/bin/env python3

import numpy as np
import torch
from pathlib import Path
from rosbags.rosbag2 import Reader
from rosbags.typesys import Stores, get_typestore

try:
    from lerobot.datasets import LeRobotDataset
except ImportError:
    try:
        from lerobot.datasets.lerobot_dataset import LeRobotDataset
    except ImportError:
        from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

class FrankaRosbagToLeRobot:
    def __init__(self, bag_dir, output_dir, target_freq=20, repo_id="franka_pick_dataset"):
        self.bag_path = Path(bag_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.target_freq = target_freq
        self.repo_id = repo_id

        # Frankaの関節順序（全9軸）
        self.joint_names = [
            'panda_joint1', 'panda_joint2', 'panda_joint3',
            'panda_joint4', 'panda_joint5', 'panda_joint6', 'panda_joint7',
            'panda_finger_joint1', 'panda_finger_joint2'
        ]
        self.cmd_topics = [f"/{name}_cmd" for name in self.joint_names]

        # MCAP形式のバッグディレクトリ（metadata.yamlを含むフォルダ）を検索
        if (self.bag_path / "metadata.yaml").exists():
            self.episode_dirs = [self.bag_path]
        else:
            self.episode_dirs = sorted(p.parent for p in self.bag_path.rglob('metadata.yaml'))

        if not self.episode_dirs:
            raise FileNotFoundError(f"No rosbag2 directories found in {bag_dir}")

        print(f"Found {len(self.episode_dirs)} episode(s):")
        for ep_dir in self.episode_dirs:
            print(f"  - {ep_dir.name}")

        # LeRobotの特徴量定義（Franka 9次元）
        features = {
            "observation.state": {
                "dtype": "float32",
                "shape": (9,),
                "names": self.joint_names,
            },
            "action": {
                "dtype": "float32",
                "shape": (9,),
                "names": self.joint_names,
            },
        }

        # データセット初期化
        if self.output_dir.exists():
            import shutil
            shutil.rmtree(self.output_dir)
            print(f"Cleared existing output dir: {self.output_dir}")

        self.dataset = LeRobotDataset.create(
            repo_id=self.repo_id,
            fps=self.target_freq,
            root=self.output_dir,
            robot_type="franka",
            features=features,
            use_videos=False,  # カメラ画像なし（関節データのみ）
        )

    def _get_messages(self, episode_dir):
        """bagから /joint_states と 各 /panda_*_cmd を抽出"""
        try:
            typestore = get_typestore(Stores.ROS2_JAZZY)
        except Exception:
            typestore = get_typestore(Stores.LATEST)

        messages = {'/joint_states': []}
        for top in self.cmd_topics:
            messages[top] = []

        with Reader(episode_dir) as reader:
            connections = [x for x in reader.connections if x.topic in messages]
            for connection, timestamp, rawdata in reader.messages(connections=connections):
                msg = typestore.deserialize_cdr(rawdata, connection.msgtype)
                messages[connection.topic].append((msg, timestamp))
        return messages

    def _sample_and_hold(self, times, values, target_times):
        """指定周波数の時間グリッドに合わせてサンプリング"""
        values = np.asarray(values)
        new_values = np.zeros((len(target_times), values.shape[1]), dtype=np.float32)
        for i, target_time in enumerate(target_times):
            idx = np.searchsorted(times, target_time, side='right') - 1
            if idx < 0:
                idx = 0
            new_values[i] = values[idx]
        return new_values

    def convert(self):
        for idx, episode_dir in enumerate(self.episode_dirs):
            print(f"\nProcessing episode {idx}: {episode_dir.name}...")
            messages = self._get_messages(episode_dir)
            
            joint_states = messages['/joint_states']
            if not joint_states:
                print(f"Skip {episode_dir}: no /joint_states")
                continue

            # 1. 実測値（Observation）の整形
            j_times = []
            j_pos_list = []
            name_to_idx = {name: i for i, name in enumerate(self.joint_names)}
            
            for msg, ts in joint_states:
                vec = [0.0] * 9
                for name, pos in zip(msg.name, msg.position):
                    if name in name_to_idx:
                        vec[name_to_idx[name]] = pos
                j_times.append(ts)
                j_pos_list.append(vec)
                
            j_times = np.array(j_times)
            j_pos = np.array(j_pos_list, dtype=np.float32)

            # 2. 指令値（Action）の整形
            start_time = j_times[0]
            end_time = j_times[-1]

            action_traj = []
            for top in self.cmd_topics:
                t_list = [ts for _, ts in messages[top]]
                v_list = [[msg.data] for msg, _ in messages[top]]
                if not t_list:
                    t_list = [start_time]
                    v_list = [[0.0]]
                target_times = np.linspace(start_time, end_time, int((end_time - start_time) * self.target_freq / 1e9))
                res = self._sample_and_hold(np.array(t_list), np.array(v_list), target_times)
                action_traj.append(res)

            a_pos_sampled = np.hstack(action_traj)
            num_frames = len(target_times)

            j_pos_sampled = self._sample_and_hold(j_times, j_pos, target_times)

            # 3. LeRobotDatasetへ1フレームずつ追加
            for i in range(num_frames):
                self.dataset.add_frame({
                    "observation.state": torch.tensor(j_pos_sampled[i], dtype=torch.float32),
                    "action": torch.tensor(a_pos_sampled[i], dtype=torch.float32),
                    "task": "pick_and_place",
                })

            self.dataset.save_episode()
            print(f"★ Episode {idx} saved ({num_frames} frames)")

        # データセットのメタデータ保存・確定処理
        if hasattr(self.dataset, "finalize"):
            self.dataset.finalize()
        elif hasattr(self.dataset, "consolidate"):
            self.dataset.consolidate()

        return str(self.dataset.root)

if __name__ == '__main__':
    # 基準パス（スクリプトと同じディレクトリ）
    base_dir = Path(__file__).resolve().parent
    
    # bags/franka_pick_run2 を対象に変換
    BAG_DIR = base_dir / "bags"
    OUTPUT_DIR = base_dir / "lerobot_dataset"

    converter = FrankaRosbagToLeRobot(
        bag_dir=BAG_DIR,
        output_dir=OUTPUT_DIR,
        target_freq=20,  # 20Hz
        repo_id="franka_pick_dataset"
    )
    saved_path = converter.convert()
    print(f"\nSuccessfully converted! Dataset saved at: {saved_path}")
