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

### 2.1 コンテナの起動
リポジトリをホスト側の `~/franka_project` にクローンし、Dockerコンテナを起動します：
```bash
docker run --rm -it \
  --name franka-gz-vnc \
  -p 127.0.0.1:6080:6080 \
  --shm-size=1g \
  -v "$HOME/franka_project:/root/franka_project" \
  franka-jazzy-gz:dev
```
ブラウザで `http://localhost:6080` を開き、VNCデスクトップに接続します。

### 2.2 Gazeboワールドのシンボリックリンク設定
新規コンテナでは Gazebo のキャッシュディレクトリにワールドファイルのリンクを貼る必要があります。コンテナ内のターミナルで以下を1行実行してください：
```bash
mkdir -p "/root/.gz/fuel/fuel.gazebosim.org/openrobotics/worlds/panda joint control world/2" && \
ln -sf /root/franka_project/panda_world.sdf "/root/.gz/fuel/fuel.gazebosim.org/openrobotics/worlds/panda joint control world/2/panda_world.sdf"
```

### 2.3 Python依存ライブラリのインストール
推論ノードの実行に必要なライブラリをコンテナ内にインストールします：
```bash
cd /root/franka_project
pip install -r requirements.txt
```

### 2.4 ROS 2 パッケージのビルド
```bash
cd /root/franka_project/ros2_ws
colcon build --packages-select panda_control1
source install/setup.bash
```

---

## 3. 実行手順

### 3.1 Gazebo シミュレーションの起動
コンテナ内のターミナルで Gazebo を起動します：
```bash
gz sim
```
画面右上の再生ボタン（▶）を押し、シミュレーションを開始します。

### 3.2 デモ動作の実行（軌道生成・データ収集）
C1連続コサイン補間による滑らかな実演ノードを実行します：
```bash
# 高品質デモ収集（本番用）
ros2 run panda_control1 pick_smooth_node

# ※参考: 開発過程で作成したデモノード
# ros2 run panda_control1 pick_demo_node
# ros2 run panda_control1 pick_demo2_node
```

### 3.3 ACT ポリシーによる自律推論の実行
学習済みモデル（`franka_act_policy`）を読み込み、自律把持・持ち上げを実行します：
```bash
ros2 run panda_control1 act_eval_node --model-path /root/franka_project/franka_act_policy
```

---

## 4. 学習パイプライン (Google Colab / GPU環境)

学習は Google Colab（GPU: T4）で実施しました。再学習の手順は以下の通りです：

1. **データ収集 & 変換**:
   ```bash
   # bag記録
   ros2 bag record -a -o bags/demo_ep1
   # LeRobot形式に変換
   python3 convert_to_lerobot.py
   zip -r lerobot_dataset.zip lerobot_dataset
   ```
2. **Google Colab での学習**:
   - `lerobot_dataset.zip` と `train.py`, `requirements.txt` を Colab にアップロードします。
   - 以下のコマンドで学習を実行します：
     ```bash
     pip install -r requirements.txt
     python train.py --dataset-path ./lerobot_dataset.zip --output-dir ./franka_act_policy --steps 3000
     ```
   - 学習完了後、出力された `franka_act_policy` フォルダをダウンロードし、プロジェクト直下に配置して使用します。