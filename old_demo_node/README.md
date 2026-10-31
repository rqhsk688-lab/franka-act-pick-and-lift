# Legacy Demo Collection Scripts (Archive)

本ディレクトリは、初期のデモ動作用のスクリプトを保管するアーカイブです。

現在、ROS 2パッケージ（`ros2_ws/src/panda_control1`）内には、本番用のデモ `pick_smooth_node.py`** が保存されています。

---

## 格納スクリプト一覧

| ファイル名 | 概要 |
| :--- | :--- |
| `pick_node.py` | 初期のステップ制御・直線補間による動作プロトタイプ |
| `pick_node_var1.py` 〜 `var4.py` | プロトタイプから軌道を変えたもの |
| `pick_demo_node.py` | フェーズ間の停止状態を解消しようとしたノード |
| `pick_demo2_node.py` | フェーズ間の停止状態を解消しようとしたノード２ |

---

## 備考
- 本ディレクトリ内のスクリプトは、軌道生成アルゴリズムの比較・履歴参照用として保存されています。
- 最新の学習用データセット作成には、メインの `ros2 run panda_control1 pick_smooth_node` をご使用ください。
