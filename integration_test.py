#!/usr/bin/env python
"""統合テスト - 実際の動画作成"""

import sys
import time
from pathlib import Path
import traceback

def test_video_mixer():
    """動画・画像ミックステスト"""
    print("=== 動画・画像ミックステスト ===")
    
    try:
        from video_mixer import mix_video_with_image
        from advanced_video_concatenator import get_video_duration
        
        samples_dir = Path("samples")
        output_dir = Path("tests/output")
        output_dir.mkdir(exist_ok=True)
        
        # テストケース
        background_video = str(samples_dir / "ball_bokeh_02_slyblue.mp4")
        overlay_image = str(samples_dir / "02-1.png")
        output_video = str(output_dir / "test_mix_short.mp4")
        duration = 3
        
        print(f"背景動画: {Path(background_video).name}")
        print(f"オーバーレイ画像: {Path(overlay_image).name}")
        print(f"出力時間: {duration}秒")
        
        # 既存ファイル削除
        if Path(output_video).exists():
            Path(output_video).unlink()
        
        # 実行時間測定
        start_time = time.time()
        mix_video_with_image(background_video, overlay_image, output_video, duration)
        processing_time = time.time() - start_time
        
        # 結果確認
        assert Path(output_video).exists(), "出力ファイルが作成されていません"
        
        file_size = Path(output_video).stat().st_size / (1024 * 1024)  # MB
        actual_duration = get_video_duration(output_video)
        
        print(f"✅ 動画ミックス成功")
        print(f"  処理時間: {processing_time:.1f}秒")
        print(f"  ファイルサイズ: {file_size:.1f}MB")
        print(f"  実際の長さ: {actual_duration:.2f}秒")
        print(f"  時間精度: {abs(actual_duration - duration):.2f}秒差")
        
        # 時間精度チェック（±0.3秒以内）
        assert abs(actual_duration - duration) <= 0.3, f"時間精度が悪い: {actual_duration}s vs {duration}s"
        
        return True
        
    except Exception as e:
        print(f"❌ 動画ミックステストエラー: {e}")
        traceback.print_exc()
        return False

def test_simple_concatenation():
    """単純動画連結テスト"""
    print("\n=== 単純動画連結テスト ===")
    
    try:
        from advanced_video_concatenator import (
            VideoSegment, Transition, TransitionMode, 
            concatenate_videos_advanced, get_video_duration
        )
        
        samples_dir = Path("samples")
        output_dir = Path("tests/output")
        
        # テストケース: 短い動画 + 長い動画（単純結合）
        short_video = str(samples_dir / "ball_bokeh_02_slyblue.mp4")
        long_video = str(samples_dir / "13523522_1920_1080_60fps.mp4")
        output_video = str(output_dir / "test_concat_simple.mp4")
        
        sequence = [
            VideoSegment(short_video),
            Transition(TransitionMode.NONE),
            VideoSegment(long_video)
        ]
        
        print(f"前動画: {Path(short_video).name}")
        print(f"後動画: {Path(long_video).name}")
        print("結合モード: 単純結合")
        
        # 予想時間計算
        duration1 = get_video_duration(short_video)
        duration2 = get_video_duration(long_video)
        expected_duration = duration1 + duration2
        
        print(f"予想時間: {duration1:.1f}s + {duration2:.1f}s = {expected_duration:.1f}s")
        
        # 既存ファイル削除
        if Path(output_video).exists():
            Path(output_video).unlink()
        
        # 実行時間測定
        start_time = time.time()
        concatenate_videos_advanced(sequence, output_video)
        processing_time = time.time() - start_time
        
        # 結果確認
        assert Path(output_video).exists(), "出力ファイルが作成されていません"
        
        file_size = Path(output_video).stat().st_size / (1024 * 1024)  # MB
        actual_duration = get_video_duration(output_video)
        
        print(f"✅ 単純連結成功")
        print(f"  処理時間: {processing_time:.1f}秒")
        print(f"  ファイルサイズ: {file_size:.1f}MB")
        print(f"  実際の長さ: {actual_duration:.2f}秒")
        print(f"  時間精度: {abs(actual_duration - expected_duration):.2f}秒差")
        
        # 時間精度チェック（±1秒以内）
        assert abs(actual_duration - expected_duration) <= 1.0, f"時間精度が悪い: {actual_duration}s vs {expected_duration}s"
        
        return True
        
    except Exception as e:
        print(f"❌ 単純連結テストエラー: {e}")
        traceback.print_exc()
        return False

def test_crossfade_concatenation():
    """クロスフェード連結テスト"""
    print("\n=== クロスフェード連結テスト ===")
    
    try:
        from advanced_video_concatenator import (
            VideoSegment, Transition, TransitionMode,
            concatenate_videos_advanced, get_video_duration
        )
        
        samples_dir = Path("samples")
        output_dir = Path("tests/output")
        
        # テストケース: クロスフェード(増加あり)
        short_video = str(samples_dir / "ball_bokeh_02_slyblue.mp4")
        long_video = str(samples_dir / "13523522_1920_1080_60fps.mp4")
        output_video = str(output_dir / "test_concat_crossfade.mp4")
        fade_duration = 1.0
        
        sequence = [
            VideoSegment(short_video),
            Transition(TransitionMode.CROSSFADE_INCREASE, fade_duration),
            VideoSegment(long_video)
        ]
        
        print(f"前動画: {Path(short_video).name}")
        print(f"後動画: {Path(long_video).name}")
        print(f"結合モード: クロスフェード(増加あり) {fade_duration}秒")
        
        # 予想時間計算
        duration1 = get_video_duration(short_video)
        duration2 = get_video_duration(long_video)
        expected_duration = duration1 + duration2 + fade_duration
        
        print(f"予想時間: {duration1:.1f}s + {duration2:.1f}s + {fade_duration}s = {expected_duration:.1f}s")
        
        # 既存ファイル削除
        if Path(output_video).exists():
            Path(output_video).unlink()
        
        # 実行時間測定
        start_time = time.time()
        concatenate_videos_advanced(sequence, output_video)
        processing_time = time.time() - start_time
        
        # 結果確認
        assert Path(output_video).exists(), "出力ファイルが作成されていません"
        
        file_size = Path(output_video).stat().st_size / (1024 * 1024)  # MB
        actual_duration = get_video_duration(output_video)
        
        print(f"✅ クロスフェード連結成功")
        print(f"  処理時間: {processing_time:.1f}秒")
        print(f"  ファイルサイズ: {file_size:.1f}MB")
        print(f"  実際の長さ: {actual_duration:.2f}秒")
        print(f"  時間精度: {abs(actual_duration - expected_duration):.2f}秒差")
        
        # 時間精度チェック（±1.5秒以内、クロスフェード処理で誤差が大きめ）
        assert abs(actual_duration - expected_duration) <= 1.5, f"時間精度が悪い: {actual_duration}s vs {expected_duration}s"
        
        return True
        
    except Exception as e:
        print(f"❌ クロスフェード連結テストエラー: {e}")
        traceback.print_exc()
        return False

def test_python_api():
    """Python APIテスト"""
    print("\n=== Python APIテスト ===")
    
    try:
        from video_processing_lib import VideoSequenceBuilder, VideoProcessor, quick_mix
        from advanced_video_concatenator import TransitionMode
        
        samples_dir = Path("samples")
        output_dir = Path("tests/output")
        
        # ビルダーパターンテスト
        print("--- ビルダーパターンテスト ---")
        
        short_video = str(samples_dir / "ball_bokeh_02_slyblue.mp4")
        long_video = str(samples_dir / "13523522_1920_1080_60fps.mp4")
        output_video = str(output_dir / "test_api_builder.mp4")
        
        sequence = (VideoSequenceBuilder()
                   .add_video(short_video)
                   .add_crossfade(0.5, TransitionMode.CROSSFADE_INCREASE)
                   .add_video(long_video)
                   .build())
        
        print(f"シーケンス長: {len(sequence)}")
        
        # 既存ファイル削除
        if Path(output_video).exists():
            Path(output_video).unlink()
        
        # プロセッサで実行
        processor = VideoProcessor()
        start_time = time.time()
        result_info = processor.concatenate_videos(sequence, output_video)
        processing_time = time.time() - start_time
        
        assert Path(output_video).exists()
        
        print(f"✅ ビルダーパターン成功")
        print(f"  処理時間: {processing_time:.1f}秒")
        print(f"  出力情報: {result_info.duration:.1f}秒")
        
        # クイック関数テスト
        print("--- クイック関数テスト ---")
        
        output_quick = str(output_dir / "test_api_quick_mix.mp4")
        if Path(output_quick).exists():
            Path(output_quick).unlink()
        
        start_time = time.time()
        result_info = quick_mix(
            short_video,
            str(samples_dir / "title-base.png"),
            output_quick,
            duration=4
        )
        processing_time = time.time() - start_time
        
        assert Path(output_quick).exists()
        
        print(f"✅ クイック関数成功") 
        print(f"  処理時間: {processing_time:.1f}秒")
        print(f"  出力情報: {result_info.duration:.1f}秒")
        
        return True
        
    except Exception as e:
        print(f"❌ Python APIテストエラー: {e}")
        traceback.print_exc()
        return False

def test_crossfade_effects():
    """クロスフェード効果テスト"""
    print("\n=== クロスフェード効果テスト ===")
    
    try:
        from advanced_video_concatenator import (
            create_crossfade_video, CrossfadeEffect, CrossfadeOutputMode
        )
        from video_processing_lib import quick_crossfade
        
        samples_dir = Path("samples")
        output_dir = Path("tests/output")
        
        # 基本的な動画ファイル
        video1 = str(samples_dir / "ball_bokeh_02_slyblue.mp4")
        video2 = str(samples_dir / "13523522_1920_1080_60fps.mp4")
        
        # テストケース1: FADE_ONLY モード
        print("--- フェード部分のみ出力テスト ---")
        output_fade_only = str(output_dir / "test_crossfade_fade_only.mp4")
        
        if Path(output_fade_only).exists():
            Path(output_fade_only).unlink()
        
        start_time = time.time()
        result = create_crossfade_video(
            video1, video2,
            fade_duration=2.0,
            output_path=output_fade_only,
            effect=CrossfadeEffect.FADE,
            output_mode=CrossfadeOutputMode.FADE_ONLY
        )
        processing_time = time.time() - start_time
        
        assert Path(output_fade_only).exists(), "フェード部分のみファイルが作成されていません"
        assert abs(result['actual_duration'] - 2.0) <= 0.1, f"時間精度が悪い: {result['actual_duration']}s vs 2.0s"
        
        print(f"✅ フェード部分のみ成功")
        print(f"  処理時間: {processing_time:.1f}秒")
        print(f"  ファイルサイズ: {result['file_size_mb']:.1f}MB")
        print(f"  実際の長さ: {result['actual_duration']:.2f}秒")
        
        # テストケース2: FULL_SEQUENCE モード
        print("\n--- 完全版出力テスト ---")
        output_full = str(output_dir / "test_crossfade_full.mp4")
        
        if Path(output_full).exists():
            Path(output_full).unlink()
        
        start_time = time.time()
        result = create_crossfade_video(
            video1, video2,
            fade_duration=1.5,
            output_path=output_full,
            effect=CrossfadeEffect.DISSOLVE,
            output_mode=CrossfadeOutputMode.FULL_SEQUENCE
        )
        processing_time = time.time() - start_time
        
        # 期待時間: 10.0 + 14.5 - 1.5 = 23.0秒
        expected_duration = 23.0
        assert Path(output_full).exists(), "完全版ファイルが作成されていません"
        assert abs(result['actual_duration'] - expected_duration) <= 0.5, f"時間精度が悪い: {result['actual_duration']}s vs {expected_duration}s"
        
        print(f"✅ 完全版出力成功")
        print(f"  処理時間: {processing_time:.1f}秒")
        print(f"  ファイルサイズ: {result['file_size_mb']:.1f}MB")
        print(f"  実際の長さ: {result['actual_duration']:.2f}秒")
        print(f"  期待時間: {expected_duration}秒")
        
        # テストケース3: 様々なエフェクトテスト
        print("\n--- 様々なエフェクトテスト ---")
        effects_to_test = [
            (CrossfadeEffect.WIPELEFT, "wipe_left"),
            (CrossfadeEffect.SLIDERIGHT, "slide_right"),
            (CrossfadeEffect.CIRCLECROP, "circle_crop")
        ]
        
        for effect, suffix in effects_to_test:
            output_effect = str(output_dir / f"test_crossfade_{suffix}.mp4")
            
            if Path(output_effect).exists():
                Path(output_effect).unlink()
            
            start_time = time.time()
            result = create_crossfade_video(
                video1, video2,
                fade_duration=1.0,
                output_path=output_effect,
                effect=effect,
                output_mode=CrossfadeOutputMode.FADE_ONLY
            )
            processing_time = time.time() - start_time
            
            assert Path(output_effect).exists(), f"{effect.value}エフェクトファイルが作成されていません"
            
            print(f"  ✅ {effect.value}エフェクト成功 ({processing_time:.1f}秒, {result['file_size_mb']:.1f}MB)")
        
        # テストケース4: quick_crossfade関数テスト
        print("\n--- クイック関数テスト ---")
        output_quick = str(output_dir / "test_crossfade_quick.mp4")
        
        if Path(output_quick).exists():
            Path(output_quick).unlink()
        
        start_time = time.time()
        result = quick_crossfade(
            video1, video2,
            output_quick,
            fade_duration=1.0,
            effect=CrossfadeEffect.FADEBLACK
        )
        processing_time = time.time() - start_time
        
        assert Path(output_quick).exists(), "クイック関数ファイルが作成されていません"
        
        print(f"✅ クイック関数成功")
        print(f"  処理時間: {processing_time:.1f}秒")
        print(f"  ファイルサイズ: {result['file_size_mb']:.1f}MB")
        print(f"  エフェクト: {result['effect']}")
        
        return True
        
    except Exception as e:
        print(f"❌ クロスフェード効果テストエラー: {e}")
        traceback.print_exc()
        return False

def main():
    """メイン統合テスト実行"""
    print("🎬 統合テスト実行開始")
    
    # samplesディレクトリチェック
    samples_dir = Path("samples")
    if not samples_dir.exists():
        print("❌ samplesディレクトリが見つかりません")
        return 1
    
    # 出力ディレクトリ作成
    output_dir = Path("tests/output")
    output_dir.mkdir(exist_ok=True)
    
    tests = [
        test_video_mixer,
        test_simple_concatenation,
        test_crossfade_concatenation, 
        test_python_api,
        test_crossfade_effects,
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            results.append(False)
    
    # 結果サマリー
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 統合テスト結果サマリー")
    print(f"成功: {passed}/{total}")
    print(f"失敗: {total - passed}/{total}")
    
    # 出力ファイル一覧
    output_files = list(output_dir.glob("test_*.mp4"))
    print(f"\n📁 作成された動画ファイル: {len(output_files)}個")
    for file in output_files:
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"  - {file.name}: {size_mb:.1f}MB")
    
    if passed == total:
        print("🎉 全ての統合テストが成功しました！")
        return 0
    else:
        print("⚠️ 一部の統合テストが失敗しました")
        return 1

if __name__ == "__main__":
    sys.exit(main())