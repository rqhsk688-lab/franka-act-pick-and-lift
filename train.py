from google.colab import drive
drive.mount('/content/drive')

# 必要なライブラリのインストール
!pip install -q 'lerobot[dataset]' torch

!cp /content/drive/MyDrive/ROS2/lerobot_dataset.zip .
# データの解凍
!unzip -o -q lerobot_dataset.zip
print("解凍完了！")

!pip install -q -U torchao

import os
import shutil
from pathlib import Path
import torch
from torch.utils.data import DataLoader

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.act.configuration_act import ACTConfig
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.configs.types import FeatureType, PolicyFeature

# ==========================================
# 1. ハイパーパラメータ設定
# ==========================================
DATASET_ROOT = Path("/content/lerobot_dataset").resolve()          # カレントディレクトリ
REPO_ID = "lerobot_dataset"                        # 解凍されたフォルダ名
OUTPUT_DIRECTORY = Path("/content/outputs/franka_act_policy").resolve()
DRIVE_SAVE_DIRECTORY = Path("/content/drive/MyDrive/ROS2/franka_act_policy")

FPS = 20                  # 1秒あたり20ステップ
CHUNK_SIZE = 50           # 一度に予測する未来のステップ数（2.5秒分）
N_ACTION_STEPS = 10       # 1推論で実行するアクション数（0.5秒分）
BATCH_SIZE = 16           # バッチサイズ
LEARNING_RATE = 1e-4      # 学習率
TRAINING_STEPS = 3000     # 学習ステップ数（約3〜5分で完了）
LOG_FREQ = 100            # ログ表示頻度
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"Using device: {DEVICE}")

# ==========================================
# 2. データセットと統計情報の読み込み
# ==========================================
delta_timestamps = {
    "action": [t / FPS for t in range(CHUNK_SIZE)]
}

dataset = LeRobotDataset(
    repo_id=REPO_ID,
    root=DATASET_ROOT,
    delta_timestamps=delta_timestamps
)
print(f"データセット読み込み完了: {len(dataset)} サンプル")

# 統計情報（正規化用）を取得
dataset_stats = getattr(dataset.meta, "stats", None) if hasattr(dataset, "meta") else getattr(dataset, "stats", None)

OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

# PolicyFeature を定義
input_features = {
    "observation.state": PolicyFeature(type=FeatureType.STATE, shape=(9,)),
    "observation.environment_state": PolicyFeature(type=FeatureType.ENV, shape=(9,)),
}

output_features = {
    "action": PolicyFeature(type=FeatureType.ACTION, shape=(9,)),
}

cfg = ACTConfig(
    input_features=input_features,
    output_features=output_features,
    chunk_size=CHUNK_SIZE,
    n_action_steps=N_ACTION_STEPS,
    dim_model=256,
    n_heads=8,
    n_encoder_layers=4,
    n_decoder_layers=4,
    use_vae=True,
    kl_weight=10.0,
)

try:
    policy = ACTPolicy(cfg, dataset_stats=dataset_stats)
except TypeError:
    policy = ACTPolicy(cfg)

policy.train()
policy.to(DEVICE)
print("ACT Policy initialized successfully!")

# ==========================================
# 4. データローダー & オプティマイザの準備
# ==========================================

dataloader = DataLoader(
    dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=2,
    drop_last=True
)

optimizer = torch.optim.AdamW(policy.parameters(), lr=LEARNING_RATE, weight_decay=1e-4)

# ==========================================
# 5. 学習ループ (3000 Steps)
# ==========================================
print(f"\n--- 学習開始 (Total Steps: {TRAINING_STEPS}) ---")
step = 0
done = False

while not done:
    for batch in dataloader:
        batch = {k: (v.to(DEVICE) if isinstance(v, torch.Tensor) else v) for k, v in batch.items()}

        #3次元テンソルが来た場合に最新フレームを抽出
        if batch["observation.state"].ndim == 3:
            batch["observation.state"] = batch["observation.state"][:, -1, :]

        # バッチ内の関節データをそのまま環境状態としても渡す
        batch["observation.environment_state"] = batch["observation.state"]

        # 損失計算 (L1 Loss + CVAEのKLダイバージェンス)
        loss, loss_dict = policy.forward(batch)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if step % LOG_FREQ == 0:
            l1_loss = loss_dict.get('l1_loss', 0.0)
            kld_loss = loss_dict.get('kld_loss', 0.0)
            print(f"Step {step:4d} | Total Loss: {loss.item():.4f} (L1: {l1_loss:.4f}, KL: {kld_loss:.4f})")

        step += 1
        if step >= TRAINING_STEPS:
            done = True
            break

# ==========================================
# 6. モデルの保存 & Google Drive への自動同期
# ==========================================
policy.save_pretrained(OUTPUT_DIRECTORY)

# WSLでの推論・正規化用に stats.json も同封
stats_src = DATASET_ROOT / REPO_ID / "meta" / "stats.json"
if stats_src.exists():
    shutil.copy(stats_src, OUTPUT_DIRECTORY / "stats.json")

print(f"\n★ 学習完了！Colabローカルに保存: {OUTPUT_DIRECTORY}")

# Google Drive へ同期
shutil.copytree(OUTPUT_DIRECTORY, DRIVE_SAVE_DIRECTORY, dirs_exist_ok=True)
print(f"Google Drive へのバックアップ完了: {DRIVE_SAVE_DIRECTORY}")

