# テストガイド

mix-sampleライブラリのテストスイートです。

## テストの種類

### 📦 単体テスト
- **test_video_mixer.py**: 背景動画+静止画合成のテスト
- **test_advanced_concatenator.py**: 動画連結機能のテスト
- **test_video_processing_lib.py**: Python APIのテスト

### 🔗 統合テスト
- **test_integration_real_videos.py**: 実際の動画作成を伴う統合テスト

## テストの実行方法

### 基本的な実行

```bash
# 高速テスト（FFmpeg不要）
python run_tests.py --quick

# 全テスト実行
python run_tests.py --all

# 統合テストのみ
python run_tests.py --integration

# 特定ファイルのみ
python run_tests.py --file test_video_mixer.py

# 詳細出力付き
python run_tests.py --all --verbose
```

### pytest直接実行

```bash
# 基本実行
uv run pytest

# マーカー別実行
uv run pytest -m "not slow"              # 高速テストのみ
uv run pytest -m "integration"           # 統合テストのみ
uv run pytest -m "requires_ffmpeg"       # FFmpeg必要テストのみ

# 特定ファイル
uv run pytest tests/test_video_mixer.py

# 詳細出力
uv run pytest -v -s
```

## テストマーカー

- `@pytest.mark.slow`: 時間のかかるテスト
- `@pytest.mark.integration`: 統合テスト
- `@pytest.mark.requires_ffmpeg`: FFmpegが必要なテスト

## 必要な環境

### 必須
- Python 3.12+
- uv（パッケージマネージャー）

### テスト用サンプルファイル
`samples/` ディレクトリに以下のファイルが必要:
- `ball_bokeh_02_slyblue.mp4` (短い動画)
- `13523522_1920_1080_60fps.mp4` (長い動画)
- `02-1.png` (画像ファイル)
- `title-base.png` (画像ファイル)

### FFmpeg（統合テスト用）
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# https://ffmpeg.org/download.html から入手
```

## テスト結果の確認

### 出力ファイル
テスト実行時に `tests/output/` ディレクトリに動画ファイルが作成されます:
- `temp_test_*.mp4`: 一時テストファイル（自動削除）
- `test_*.mp4`: 統合テスト結果ファイル
- `mix_*.mp4`: 動画ミックステスト結果
- `concat_*.mp4`: 動画連結テスト結果

### パフォーマンス情報
統合テストでは以下の情報が表示されます:
- 処理時間
- ファイルサイズ
- 動画長の精度
- スループット

## トラブルシューティング

### FFmpegエラー
```
FFmpegが見つかりません
```
→ FFmpegをインストールしてPATHに追加してください

### ファイル不足エラー
```
samplesディレクトリが見つかりません
```
→ `samples/` ディレクトリにサンプルファイルを配置してください

### メモリ不足
長時間のテストでメモリ不足が発生する場合:
```bash
# 統合テストを除外
python run_tests.py --unit
```

### 権限エラー
出力ディレクトリの権限を確認:
```bash
chmod 755 tests/output/
```

## テストケースの詳細

### 時間計算テスト
動画連結時の時間計算精度をテスト:
- 単純結合: A + B = A時間 + B時間
- 増加あり: A + フェイド + B = A時間 + フェイド時間 + B時間
- 増加無し: A短縮 + フェイド + B = (A時間 - フェイド時間) + フェイド時間 + B時間

### パフォーマンステスト
- 動画ミックス: 3秒、5秒、10秒動画での処理時間測定
- 動画連結: 各結合モードでの処理時間測定
- スループット基準: 0.05x以上（処理時間が出力動画時間の20倍以下）

### エラーハンドリングテスト
- 存在しないファイル
- 不正な引数
- フォーマットエラー
- 権限エラー

## CIでの実行

GitHub Actionsなど CI環境での実行例:
```yaml
- name: テスト実行
  run: |
    uv install --dev
    python run_tests.py --quick  # 高速テストのみ

# FFmpegが利用可能な環境では
- name: 統合テスト実行
  run: |
    sudo apt install ffmpeg
    python run_tests.py --all
```