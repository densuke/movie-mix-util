# ハードウェアアクセラレーション実装推奨事項

## 調査結果サマリー

### 現状分析
- **現在の実装**: プラットフォーム別自動検出ロジック実装済み
- **検証結果**: macOS環境でVideoToolbox正常動作確認（1.6倍速度向上）
- **課題**: 実際のハードウェア使用状況の可視化と動的検証が不十分

### 主な発見
1. **FFmpegライブラリ制限**: `ffmpeg-python`には`get_build_info()`メソッドが存在しない
2. **検証方法**: コマンドライン実行とログ解析による検証が有効
3. **プラットフォーム差異**: 各プラットフォームで異なる最適化アプローチが必要

## 実装推奨事項

### 1. 動的検証機能の統合

**実装場所**: `src/movie_mix_util/video_processing_lib.py`

```python
# 推奨追加機能
from .hwaccel_validator import HardwareAccelValidator, create_optimized_ffmpeg_options

def validate_current_hwaccel_setup():
    """現在のハードウェアアクセラレーション設定を検証"""
    with HardwareAccelValidator() as validator:
        test_video = validator.create_test_content(duration=3)
        result = validator.validate_hwaccel_usage(
            test_video, DEFAULT_VIDEO_CODEC, DEFAULT_HWACCEL
        )
        return result
```

### 2. 実行時検証とフォールバック

**目的**: ハードウェアアクセラレーション失敗時の自動フォールバック

```python
def encode_with_validation(input_path, output_path, **kwargs):
    """検証付きエンコード実行"""
    
    # 1. ハードウェアアクセラレーション試行
    try:
        result = encode_with_hardware(input_path, output_path, **kwargs)
        if result.success and result.performance_gain > 1.2:
            return result
    except Exception as e:
        print(f"ハードウェアエンコード失敗: {e}")
    
    # 2. ソフトウェアフォールバック
    print("ソフトウェアエンコードにフォールバック")
    return encode_with_software(input_path, output_path, **kwargs)
```

### 3. 詳細ログ出力の実装

**環境変数での制御**:
```python
DEBUG_HWACCEL = os.getenv('MOVIE_MIX_DEBUG_HWACCEL', '0') == '1'
HWACCEL_LOG_LEVEL = os.getenv('MOVIE_MIX_HWACCEL_LOG', 'info')

if DEBUG_HWACCEL:
    # 詳細ログ出力
    print(f"[HWACCEL] Using encoder: {codec}")
    print(f"[HWACCEL] Using acceleration: {hwaccel}")
    print(f"[HWACCEL] FFmpeg command: {' '.join(cmd)}")
```

### 4. パフォーマンス監視の統合

**リアルタイム監視**:
```python
import threading
import time

class PerformanceMonitor:
    def __init__(self):
        self.is_monitoring = False
        self.cpu_usage = []
        self.gpu_usage = []
    
    def start_monitoring(self):
        self.is_monitoring = True
        thread = threading.Thread(target=self._monitor_loop, daemon=True)
        thread.start()
    
    def stop_monitoring(self):
        self.is_monitoring = False
        return {
            'avg_cpu': sum(self.cpu_usage) / len(self.cpu_usage),
            'avg_gpu': sum(self.gpu_usage) / len(self.gpu_usage)
        }
```

### 5. 設定最適化API

**プリセット別設定**:
```python
HWACCEL_PRESETS = {
    'speed': {
        'priority': 'encoding_speed',
        'quality_tolerance': 'high',
        'resource_usage': 'high'
    },
    'quality': {
        'priority': 'output_quality', 
        'quality_tolerance': 'low',
        'resource_usage': 'medium'
    },
    'balanced': {
        'priority': 'both',
        'quality_tolerance': 'medium',
        'resource_usage': 'medium'
    }
}

def get_optimized_settings(preset='balanced'):
    return create_optimized_ffmpeg_options(
        DEFAULT_VIDEO_CODEC, DEFAULT_HWACCEL, preset
    )
```

## 環境変数制御の拡張

### 新しい環境変数

```bash
# 既存
MOVIE_MIX_DISABLE_HWACCEL=1  # ハードウェアアクセラレーション無効

# 推奨追加
MOVIE_MIX_DEBUG_HWACCEL=1       # デバッグログ有効
MOVIE_MIX_HWACCEL_LOG=debug     # ログレベル (quiet/info/debug)
MOVIE_MIX_HWACCEL_PRESET=speed  # 品質プリセット (speed/balanced/quality)
MOVIE_MIX_VALIDATE_HWACCEL=1    # 実行前検証有効
MOVIE_MIX_MONITOR_RESOURCES=1   # リソース監視有効
MOVIE_MIX_FALLBACK_THRESHOLD=1.2 # フォールバック判定閾値
```

## 実装優先順位

### Phase 1: 基本検証機能
1. `hwaccel_validator.py`の統合
2. 実行時検証ロジックの追加
3. 環境変数による制御拡張

### Phase 2: 監視・最適化
1. パフォーマンス監視機能
2. 自動フォールバック機能
3. プリセット別最適化

### Phase 3: 高度な機能
1. マルチGPU対応
2. 動的品質調整
3. ベンチマーク結果のキャッシュ

## テスト戦略

### 単体テスト
```python
def test_hwaccel_detection():
    """ハードウェアアクセラレーション検出テスト"""
    codec, hwaccel = _get_hw_codec_and_accel()
    assert codec in SUPPORTED_ENCODERS
    if hwaccel:
        assert hwaccel in SUPPORTED_HWACCELS

def test_fallback_mechanism():
    """フォールバック機構テスト"""
    with mock.patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, 'ffmpeg')
        result = encode_with_validation('input.mp4', 'output.mp4')
        assert result.encoder == 'libx264'  # ソフトウェアフォールバック
```

### 統合テスト
```python
def test_end_to_end_hwaccel():
    """エンドツーエンドハードウェアアクセラレーションテスト"""
    with HardwareAccelValidator() as validator:
        test_video = validator.create_test_content()
        result = validator.validate_hwaccel_usage(
            test_video, DEFAULT_VIDEO_CODEC, DEFAULT_HWACCEL
        )
        assert result.is_using_hwaccel
        assert result.performance_gain > 1.0
```

## プラットフォーム別実装注意事項

### macOS (VideoToolbox)
- **特徴**: Apple Siliconで最適化、低電力消費
- **注意**: プロファイル設定重要、リアルタイムモード対応
- **監視**: Activity Monitor連携、GPU使用率間接測定

### Windows (NVENC/QSV/AMF)
- **特徴**: GPU種別による最適化、DirectX統合
- **注意**: ドライバーバージョン依存、マルチGPU考慮
- **監視**: nvidia-smi、Intel GPU監視ツール使用

### Linux (VAAPI/NVENC/QSV)
- **特徴**: オープンソースドライバー、コンテナ対応
- **注意**: 権限設定、カーネルモジュール依存
- **監視**: intel_gpu_top、radeontop、nvidia-smi

## まとめ

1. **現在の実装は基本的に正常動作**している
2. **検証・監視機能の追加**でユーザビリティ向上が期待できる
3. **段階的実装**により安全に機能拡張可能
4. **環境変数による柔軟な制御**でデバッグ・最適化が容易になる

これらの実装により、ハードウェアアクセラレーションの透明性と信頼性が大幅に向上し、問題発生時の迅速な原因特定が可能になります。