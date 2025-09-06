#!/usr/bin/env python
"""手動テスト実行スクリプト"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """インポートテスト"""
    print("=== インポートテスト ===")
    
    try:
        # 基本インポート
        import video_mixer
        import advanced_video_concatenator
        import video_processing_lib
        print("✅ 全モジュールのインポート成功")
        return True
    except Exception as e:
        print(f"❌ インポートエラー: {e}")
        traceback.print_exc()
        return False

def test_data_classes():
    """データクラステスト"""
    print("\n=== データクラステスト ===")
    
    try:
        from advanced_video_concatenator import VideoSegment, Transition, TransitionMode
        
        # VideoSegment
        segment = VideoSegment("test.mp4")
        assert segment.path == "test.mp4"
        print("✅ VideoSegment作成成功")
        
        # Transition
        transition = Transition(TransitionMode.CROSSFADE_INCREASE, 2.0)
        assert transition.mode == TransitionMode.CROSSFADE_INCREASE
        assert transition.duration == 2.0
        print("✅ Transition作成成功")
        
        # TransitionMode
        assert TransitionMode.NONE.value == "none"
        assert TransitionMode.CROSSFADE_NO_INCREASE.value == "no_increase"
        assert TransitionMode.CROSSFADE_INCREASE.value == "increase"
        print("✅ TransitionMode値確認成功")
        
        return True
        
    except Exception as e:
        print(f"❌ データクラステストエラー: {e}")
        traceback.print_exc()
        return False

def test_calculation_functions():
    """計算関数テスト"""
    print("\n=== 計算関数テスト ===")
    
    try:
        from video_mixer import calculate_scale_to_fit, calculate_position_for_centering
        
        # スケーリング計算（横長画像）
        width, height = calculate_scale_to_fit(2000, 1000, 1920, 1080)
        assert width == 1920
        assert height == 960
        print("✅ 横長画像スケーリング計算成功")
        
        # スケーリング計算（縦長画像）
        width, height = calculate_scale_to_fit(1000, 2000, 1920, 1080)
        assert width == 540
        assert height == 1080
        print("✅ 縦長画像スケーリング計算成功")
        
        # 位置計算
        x, y = calculate_position_for_centering(1000, 600, 1920, 1080)
        assert x == (1920 - 1000) // 2
        assert y == (1080 - 600) // 2
        print("✅ 中央位置計算成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 計算関数テストエラー: {e}")
        traceback.print_exc()
        return False

def test_sequence_duration_calculation():
    """シーケンス時間計算テスト"""
    print("\n=== シーケンス時間計算テスト ===")
    
    try:
        from advanced_video_concatenator import (
            VideoSegment, Transition, TransitionMode, calculate_sequence_duration
        )
        from unittest.mock import patch
        
        # 質問例の時間計算テスト: A(15s) + クロス(無し,1s) + B(15s) + クロス(有り,1s) + C(15s) = 46s
        sequence = [
            VideoSegment("A.mp4"),
            Transition(TransitionMode.CROSSFADE_NO_INCREASE, 1.0),
            VideoSegment("B.mp4"),
            Transition(TransitionMode.CROSSFADE_INCREASE, 1.0), 
            VideoSegment("C.mp4")
        ]
        
        with patch('advanced_video_concatenator.get_video_duration') as mock_duration:
            mock_duration.side_effect = [15.0, 15.0, 15.0]
            
            total_duration = calculate_sequence_duration(sequence)
            expected = 15.0 + 15.0 + 15.0 - 1.0 + 1.0  # = 45.0
            
            print(f"計算結果: {total_duration}秒")
            print(f"期待値: {expected}秒")
            
            assert total_duration == expected
            print("✅ 混合モード時間計算成功")
        
        return True
        
    except Exception as e:
        print(f"❌ シーケンス時間計算テストエラー: {e}")
        traceback.print_exc()
        return False

def test_video_info():
    """VideoInfo機能テスト"""
    print("\n=== VideoInfo機能テスト ===")
    
    try:
        from video_processing_lib import VideoInfo
        
        # 手動作成
        info = VideoInfo("test.mp4", 30.0, 1920, 1080, 30.0)
        assert info.path == "test.mp4"
        assert info.duration == 30.0
        assert info.width == 1920
        assert info.height == 1080
        assert info.fps == 30.0
        print("✅ VideoInfo手動作成成功")
        
        return True
        
    except Exception as e:
        print(f"❌ VideoInfo機能テストエラー: {e}")
        traceback.print_exc()
        return False

def test_builder_pattern():
    """ビルダーパターンテスト"""
    print("\n=== ビルダーパターンテスト ===")
    
    try:
        from video_processing_lib import VideoSequenceBuilder
        from advanced_video_concatenator import TransitionMode, VideoSegment, Transition
        
        sequence = (VideoSequenceBuilder()
                   .add_video("A.mp4")
                   .add_crossfade(1.0, TransitionMode.CROSSFADE_NO_INCREASE)
                   .add_video("B.mp4") 
                   .add_crossfade(1.5, TransitionMode.CROSSFADE_INCREASE)
                   .add_video("C.mp4")
                   .build())
        
        assert len(sequence) == 5
        
        # 構造確認
        assert isinstance(sequence[0], VideoSegment)
        assert sequence[0].path == "A.mp4"
        
        assert isinstance(sequence[1], Transition)
        assert sequence[1].mode == TransitionMode.CROSSFADE_NO_INCREASE
        assert sequence[1].duration == 1.0
        
        assert isinstance(sequence[2], VideoSegment)
        assert sequence[2].path == "B.mp4"
        
        assert isinstance(sequence[3], Transition)
        assert sequence[3].mode == TransitionMode.CROSSFADE_INCREASE
        assert sequence[3].duration == 1.5
        
        assert isinstance(sequence[4], VideoSegment)
        assert sequence[4].path == "C.mp4"
        
        print("✅ ビルダーパターン作成成功")
        
        return True
        
    except Exception as e:
        print(f"❌ ビルダーパターンテストエラー: {e}")
        traceback.print_exc()
        return False

def test_real_video_info():
    """実動画ファイルのVideoInfo取得テスト"""
    print("\n=== 実動画ファイル情報取得テスト ===")
    
    try:
        from video_processing_lib import VideoInfo
        
        samples_dir = Path("samples")
        
        if not samples_dir.exists():
            print("⚠️ samplesディレクトリが見つかりません。スキップします。")
            return True
        
        # 短い動画
        short_video = samples_dir / "ball_bokeh_02_slyblue.mp4"
        if short_video.exists():
            info = VideoInfo.from_path(str(short_video))
            print(f"短い動画情報: {info.width}x{info.height}, {info.duration:.2f}s, {info.fps}fps")
            assert info.duration > 0
            assert info.width > 0
            assert info.height > 0
            print("✅ 短い動画情報取得成功")
        
        # 長い動画
        long_video = samples_dir / "13523522_1920_1080_60fps.mp4"
        if long_video.exists():
            info = VideoInfo.from_path(str(long_video))
            print(f"長い動画情報: {info.width}x{info.height}, {info.duration:.2f}s, {info.fps}fps")
            assert info.duration > 0
            assert info.width == 1920
            assert info.height == 1080
            print("✅ 長い動画情報取得成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 実動画ファイル情報取得テストエラー: {e}")
        traceback.print_exc()
        return False

def main():
    """メインテスト実行"""
    print("🧪 手動機能テスト実行開始")
    
    tests = [
        test_imports,
        test_data_classes, 
        test_calculation_functions,
        test_sequence_duration_calculation,
        test_video_info,
        test_builder_pattern,
        test_real_video_info,
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
    
    print(f"\n📊 テスト結果サマリー")
    print(f"成功: {passed}/{total}")
    print(f"失敗: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 全てのテストが成功しました！")
        return 0
    else:
        print("⚠️ 一部のテストが失敗しました")
        return 1

if __name__ == "__main__":
    sys.exit(main())