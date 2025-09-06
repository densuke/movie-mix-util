# mix-sample - 動画処理ライブラリ

動画の合成・連結・画像オーバーレイを行うPythonライブラリです。

## 特徴

- **動画連結**: 複数動画を様々な結合モードで連結
- **画像合成**: 背景動画に画像をオーバーレイ
- **3つの結合モード**:
  - 単純結合: そのまま連結
  - クロスフェード(増加無し): 前動画短縮、総時間変化なし
  - クロスフェード(増加あり): フェイド時間分総時間増加
- **Python API**: プログラムから利用可能
- **コマンドライン**: 直接実行可能

## インストール

```bash
# 開発環境
uv add --dev pytest pytest-cov black ruff

# FFmpegが必要
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
```

## 使い方

### コマンドライン使用

#### 1. 高度な動画連結

```bash
# 単純結合
python advanced_video_concatenator.py A.mp4 B.mp4 C.mp4 --output result.mp4

# クロスフェイド結合
python advanced_video_concatenator.py A.mp4 B.mp4 C.mp4 \
  --crossfade "1.0:no_increase,1.5:increase" --output result.mp4
```

#### 2. 動画・画像ミックス

```bash
python video_mixer.py background.mp4 overlay.png 30 output.mp4
```

### Python API使用

#### 基本的な使い方

```python
from mix_sample import VideoProcessor, TransitionMode, VideoSequenceBuilder

# プロセッサ初期化
processor = VideoProcessor()

# シーケンス作成（ビルダーパターン）
sequence = (VideoSequenceBuilder()
           .add_video("A.mp4")
           .add_crossfade(1.0, TransitionMode.CROSSFADE_NO_INCREASE)
           .add_video("B.mp4")
           .add_crossfade(1.5, TransitionMode.CROSSFADE_INCREASE) 
           .add_video("C.mp4")
           .build())

# 実行
result = processor.concatenate_videos(sequence, "output.mp4")
print(f"生成動画: {result.duration:.1f}秒")
```

#### クイック関数

```python
from mix_sample import quick_concatenate, quick_mix, TransitionMode

# すべて同じ設定で連結
result = quick_concatenate(
    ["A.mp4", "B.mp4", "C.mp4"],
    "output.mp4", 
    crossfade_duration=2.0,
    crossfade_mode=TransitionMode.CROSSFADE_NO_INCREASE
)

# 動画・画像ミックス
result = quick_mix("background.mp4", "overlay.png", "mixed.mp4", duration=30)
```

## 結合モード詳細

| モード | 説明 | 時間計算例 |
|-------|------|-----------|
| `none` | 単純結合 | A(15s) + B(15s) = 30s |
| `no_increase` | 前動画短縮 | A(14s) + fade(1s) + B(15s) = 30s |  
| `increase` | フェイド時間追加 | A(15s) + fade(1s) + B(15s) = 31s |

## 時間計算例

```
入力: A(15s), クロス(無し,1s), B(15s), クロス(有り,1s), C(15s)
結果: A(14s) + 1s + B(15s) + 1s + C(15s) = 46s
```

## API Reference

### クラス

- `VideoProcessor`: メイン処理クラス
- `VideoSequenceBuilder`: シーケンス構築ビルダー
- `VideoInfo`: 動画情報
- `VideoSegment`: 動画セグメント
- `Transition`: トランジション設定

### Enum

- `TransitionMode.NONE`: 単純結合
- `TransitionMode.CROSSFADE_NO_INCREASE`: クロスフェード(増加無し)
- `TransitionMode.CROSSFADE_INCREASE`: クロスフェード(増加あり)

### 便利関数

- `quick_concatenate()`: クイック動画連結
- `quick_mix()`: クイック動画・画像ミックス

## 開発

```bash
# テスト実行
uv run pytest

# コード整形
uv run black .
uv run ruff --fix .

# パッケージビルド
uv build
```

## 要件

- Python 3.12+
- FFmpeg
- ffmpeg-python
- Pillow

## ライセンス

MIT License