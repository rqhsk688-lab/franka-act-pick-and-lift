# Franka Emika Panda ACT Pick-and-Lift in Gazebo

Hugging Face **LeRobot (Action Chunking with Transformers: ACT)** を用いて、Gazebo Harmonic シミュレーション環境上の Franka Emika Panda ロボットによる自律 Pick-and-Lift（物体の把持・持ち上げ）タスクを実現したプロジェクトです。

---

## 1. システム概要
- **ロボット**: Franka Emika Panda (7軸アーム + 2軸平行グリッパー)
- **環境**: ROS 2 Jazzy + Gazebo Harmonic (Dockerコンテナ)
- **アルゴリズム**: ACT (Action Chunking with Transformers)
- **状態空間 (9次元)**:
  - アーム関節角度 (7軸): `panda_joint1` 〜 `panda_joint7`
  - グリッパー位置 (2軸): `panda_finger_joint1`, `panda_finger_joint2`
- **アクション空間 (9次元)**: 各関節の目標位置指令 (`std_msgs/Float64`)
- **制御周波数**: 20 Hz (`timer_period = 0.05s`)

---

## 2. 環境構築

### 2.1 リポジトリのクローンとDockerコンテナの起動

```bash
# 1. リポジトリのクローン
git clone https://github.com/rqhsk688-lab/franka-act-pick-and-lift.git
cd franka-act-pick-and-lift

# 2. Dockerイメージのビルド
docker build -t franka-act:latest -f docker/Dockerfile .

# 3. コンテナの起動
docker run --rm -it \
  --name franka-act-container \
  -p 127.0.0.1:6080:6080 \
  --shm-size=1g \
  -v "$(pwd):/root/franka_project" \
  franka-act:latest
```
ブラウザで `http://localhost:6080` を開き、VNCデスクトップに接続します。

---

### 2.2 Gazeboワールドおよびロボットモデルのシンボリックリンク設定

コンテナ内のターミナルを開き、Gazeboの公式モデルをダウンロードし、こちらで用意したワールドおよびロボットモデルに書き換えます：

```bash
# ① 公式モデル（メッシュ含む一式）を先にダウンロード
gz fuel download -u "https://fuel.ignitionrobotics.org/1.0/openrobotics/models/panda with ignition position controller model"

# ② 改造済み panda_model.sdf で上書きコピー（実ファイルとして配置）
cp /root/franka_project/panda_model.sdf "/root/.gz/fuel/fuel.ignitionrobotics.org/openrobotics/models/panda with ignition position controller model/5/model.sdf"

# ③ ワールドファイル（panda_world.sdf）のコピー配置（ディレクトリ名が大文字と小文字の場合があり、両方に対応するため、２つコピーします
mkdir -p "/root/.gz/fuel/fuel.gazebosim.org/OpenRobotics/worlds/Panda joint control world/2" && \
cp /root/franka_project/panda_world.sdf "/root/.gz/fuel/fuel.gazebosim.org/OpenRobotics/worlds/Panda joint control world/2/panda_world.sdf"

mkdir -p "/root/.gz/fuel/fuel.gazebosim.org/openrobotics/worlds/panda joint control world/2" && \
cp /root/franka_project/panda_world.sdf "/root/.gz/fuel/fuel.gazebosim.org/openrobotics/worlds/panda joint control world/2/panda_world.sdf"
```

---

### 2.3 Python依存ライブラリのインストール

推論に必要なライブラリをコンテナ内にインストールします（CPU版PyTorchおよびLeRobotが超軽量・依存衝突なしに導入されます）：

```bash
# 1. pipのインストール（初回のみ）
apt-get update && apt-get install -y --no-install-recommends python3-pip

# 2. requirements.txt からライブラリを一括インストール
pip install --no-cache-dir --break-system-packages --ignore-installed -r /root/franka_project/requirements.txt
```

---

### 2.4 ROS 2 パッケージのビルド

```bash
cd /root/franka_project/ros2_ws
colcon build --packages-select panda_control1
source install/setup.bash
```

---

## 3. 実行手順

推論・シミュレーションの実行には **3つのターミナル** を使用します。

### ターミナル 1: Gazebo シミュレーションの起動
```bash
gz sim
```
※起動後、表示されたメニューからPandaを選んでください。その後、画面右上の **再生ボタン（▶）** をクリックしてシミュレーションを開始します。

### ターミナル 2: ROS-Gazebo ブリッジの起動
GazeboとROS 2間で関節状態（`/joint_states`）および制御コマンドを中継します：
```bash
ros2 run ros_gz_bridge parameter_bridge \
  --ros-args \
  -p config_file:=/root/franka_project/panda_joint1_bridge.yaml
```

### ターミナル 3: ACT ポリシーによる自律推論の実行
学習済みモデル（`franka_act_policy`）をロードし、物体の自律把持・持ち上げを実行します：
```bash
cd /root/franka_project/ros2_ws
source install/setup.bash
ros2 run panda_control1 act_eval_node --model-path /root/franka_project/franka_act_policy
```

---

## 4. デモ収集 & 学習パイプライン (Google Colab)

### 4.1 高品質デモの収集
```bash
# ターミナル 1 (Gazebo) と ターミナル 2 (ブリッジ) が動いている状態で：
cd /root/franka_project/ros2_ws
source install/setup.bash

# C1連続コサイン補間による滑らかな把持デモの実行
ros2 run panda_control1 pick_smooth_node
```

### 4.2 LeRobot形式への変換

```bash
cd /root/franka_project
python3 convert_to_lerobot.py
zip -r lerobot_dataset.zip lerobot_dataset
```

### 4.3 Google Colab での学習
1. `lerobot_dataset.zip`, `train.py`を Google Colab（GPU環境: T4推奨）にアップロードします。
2. zipファイルはgoogle driveへアップロードしてから解凍する想定ですが、このあたりは自由に変更してください
3. 出力された `franka_act_policy` をダウンロードし、リポジトリ直下に配置して推論に使用します。
