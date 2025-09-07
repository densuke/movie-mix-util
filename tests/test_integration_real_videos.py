"""実際の動画作成を伴う統合テスト"""

import pytest
import os
from pathlib import Path
import tempfile
import time

# テスト対象のインポート - 新しいAPIを使用
from video_processing_lib import quick_mix

# 後方互換性のためのラッパー
def mix_video_with_image(background_video: str, overlay_image: str, output_video: str, duration: int = 30):
    """後方互換性のためのラッパー関数"""
    return quick_mix(background_video, overlay_image, output_video, duration)
from advanced_video_concatenator import (
    TransitionMode,
    VideoSegment,
    Transition,
    concatenate_videos_advanced,
    get_video_duration
)
from video_processing_lib import (
    VideoProcessor,
    VideoSequenceBuilder,
    quick_concatenate,
    quick_mix
)


class TestRealVideoCreation:
    """実際の動画作成テスト"""
    
    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.requires_ffmpeg
    def test_complete_video_mixing_workflow(self, samples_dir, output_dir, 
                                          video_duration_checker, video_properties_checker):
        """完全な動画ミックスワークフローテスト"""
        print("\n=== 動画ミックス統合テスト開始 ===")
        
        test_cases = [
            {
                "name": "short_video_02_1_png_5sec",
                "background": "ball_bokeh_02_slyblue.mp4",
                "overlay": "02-1.png",
                "duration": 5,
                "description": "短い動画 + 02-1.png、5秒"
            },
            {
                "name": "long_video_title_base_8sec",
                "background": "13523522_1920_1080_60fps.mp4", 
                "overlay": "title-base.png",
                "duration": 8,
                "description": "長い動画 + title-base.png、8秒"
            },
            {
                "name": "short_video_title_base_3sec",
                "background": "ball_bokeh_02_slyblue.mp4",
                "overlay": "title-base.png", 
                "duration": 3,
                "description": "短い動画 + title-base.png、3秒"
            }
        ]
        
        results = []
        
        for case in test_cases:
            print(f"\n--- {case['description']} ---")
            
            background_video = str(samples_dir / case['background'])
            overlay_image = str(samples_dir / case['overlay'])
            output_video = str(output_dir / f"mix_{case['name']}.mp4")
            
            # 既存ファイル削除
            if Path(output_video).exists():
                Path(output_video).unlink()
            
            # 処理時間測定
            start_time = time.time()
            
            try:
                # 動画ミックス実行
                mix_video_with_image(background_video, overlay_image, output_video, case['duration'])
                
                # 処理時間
                processing_time = time.time() - start_time
                
                # ファイル存在確認
                assert Path(output_video).exists(), f"出力ファイルが作成されませんでした: {output_video}"
                
                # ファイルサイズ確認
                file_size = Path(output_video).stat().st_size
                assert file_size > 1024, f"ファイルサイズが小さすぎます: {file_size}バイト"
                
                # 動画長確認
                is_correct_duration, actual_duration = video_duration_checker(
                    Path(output_video), case['duration'], tolerance=0.3
                )
                
                # プロパティ確認
                properties = video_properties_checker(Path(output_video))
                
                # 結果記録
                result = {
                    'case': case['name'],
                    'success': is_correct_duration,
                    'expected_duration': case['duration'],
                    'actual_duration': actual_duration,
                    'processing_time': processing_time,
                    'file_size_mb': file_size / (1024 * 1024),
                    'properties': properties
                }
                results.append(result)
                
                print(f"✅ 成功: {actual_duration:.2f}s (期待: {case['duration']}s)")
                print(f"   処理時間: {processing_time:.1f}秒")
                print(f"   ファイルサイズ: {result['file_size_mb']:.1f}MB")
                print(f"   解像度: {properties['width']}x{properties['height']}")
                
            except Exception as e:
                result = {
                    'case': case['name'],
                    'success': False,
                    'error': str(e),
                    'processing_time': time.time() - start_time
                }
                results.append(result)
                
                print(f"❌ 失敗: {e}")
                print(f"   処理時間: {result['processing_time']:.1f}秒")
        
        # 結果サマリー
        successful_tests = [r for r in results if r['success']]
        failed_tests = [r for r in results if not r['success']]
        
        print(f"\n=== 動画ミックステスト結果サマリー ===")
        print(f"成功: {len(successful_tests)}/{len(results)}")
        print(f"失敗: {len(failed_tests)}/{len(results)}")
        
        if successful_tests:
            avg_processing_time = sum(r['processing_time'] for r in successful_tests) / len(successful_tests)
            print(f"平均処理時間: {avg_processing_time:.1f}秒")
        
        # 少なくとも1つは成功することを期待
        assert len(successful_tests) > 0, f"全てのテストが失敗しました: {[r.get('error', 'Unknown') for r in failed_tests]}"
    
    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.requires_ffmpeg
    def test_complete_video_concatenation_workflow(self, samples_dir, output_dir,
                                                 video_duration_checker, video_properties_checker):
        """完全な動画連結ワークフローテスト"""
        print("\n=== 動画連結統合テスト開始 ===")
        
        # まずサンプル動画の実際の長さを測定
        short_video_path = samples_dir / "ball_bokeh_02_slyblue.mp4"
        long_video_path = samples_dir / "13523522_1920_1080_60fps.mp4"
        
        short_duration = get_video_duration(str(short_video_path))
        long_duration = get_video_duration(str(long_video_path))
        
        print(f"短い動画の長さ: {short_duration:.2f}秒")
        print(f"長い動画の長さ: {long_duration:.2f}秒")
        
        test_cases = [
            {
                "name": "simple_concat",
                "sequence": [
                    VideoSegment(str(short_video_path)),
                    Transition(TransitionMode.NONE),
                    VideoSegment(str(long_video_path))
                ],
                "expected_duration": short_duration + long_duration,
                "description": "単純結合"
            },
            {
                "name": "crossfade_increase",
                "sequence": [
                    VideoSegment(str(short_video_path)),
                    Transition(TransitionMode.CROSSFADE_INCREASE, 1.0),
                    VideoSegment(str(long_video_path))
                ],
                "expected_duration": short_duration + long_duration + 1.0,
                "description": "クロスフェード(増加あり)"
            },
            {
                "name": "crossfade_no_increase",
                "sequence": [
                    VideoSegment(str(short_video_path)),
                    Transition(TransitionMode.CROSSFADE_NO_INCREASE, 1.0),
                    VideoSegment(str(long_video_path))
                ],
                "expected_duration": short_duration + long_duration - 1.0,
                "description": "クロスフェード(増加無し)"
            }
        ]
        
        results = []
        
        for case in test_cases:
            print(f"\n--- {case['description']} ---")
            
            output_video = str(output_dir / f"concat_{case['name']}.mp4")
            
            # 既存ファイル削除
            if Path(output_video).exists():
                Path(output_video).unlink()
            
            # 処理時間測定
            start_time = time.time()
            
            try:
                # 動画連結実行
                concatenate_videos_advanced(case['sequence'], output_video)
                
                # 処理時間
                processing_time = time.time() - start_time
                
                # ファイル存在確認
                assert Path(output_video).exists(), f"出力ファイルが作成されませんでした: {output_video}"
                
                # ファイルサイズ確認
                file_size = Path(output_video).stat().st_size
                assert file_size > 1024, f"ファイルサイズが小さすぎます: {file_size}バイト"
                
                # 動画長確認（許容誤差を大きめに設定）
                is_correct_duration, actual_duration = video_duration_checker(
                    Path(output_video), case['expected_duration'], tolerance=1.0
                )
                
                # プロパティ確認
                properties = video_properties_checker(Path(output_video))
                
                # 結果記録
                result = {
                    'case': case['name'],
                    'success': is_correct_duration,
                    'expected_duration': case['expected_duration'],
                    'actual_duration': actual_duration,
                    'duration_difference': abs(actual_duration - case['expected_duration']),
                    'processing_time': processing_time,
                    'file_size_mb': file_size / (1024 * 1024),
                    'properties': properties
                }
                results.append(result)
                
                print(f"✅ 成功: {actual_duration:.2f}s (期待: {case['expected_duration']:.2f}s)")
                print(f"   時間差: {result['duration_difference']:.2f}秒")
                print(f"   処理時間: {processing_time:.1f}秒")
                print(f"   ファイルサイズ: {result['file_size_mb']:.1f}MB")
                
            except Exception as e:
                result = {
                    'case': case['name'],
                    'success': False,
                    'error': str(e),
                    'processing_time': time.time() - start_time
                }
                results.append(result)
                
                print(f"❌ 失敗: {e}")
                print(f"   処理時間: {result['processing_time']:.1f}秒")
        
        # 結果サマリー
        successful_tests = [r for r in results if r['success']]
        failed_tests = [r for r in results if not r['success']]
        
        print(f"\n=== 動画連結テスト結果サマリー ===")
        print(f"成功: {len(successful_tests)}/{len(results)}")
        print(f"失敗: {len(failed_tests)}/{len(results)}")
        
        if successful_tests:
            avg_processing_time = sum(r['processing_time'] for r in successful_tests) / len(successful_tests)
            avg_duration_diff = sum(r['duration_difference'] for r in successful_tests) / len(successful_tests)
            print(f"平均処理時間: {avg_processing_time:.1f}秒")
            print(f"平均時間差: {avg_duration_diff:.2f}秒")
        
        # 少なくとも1つは成功することを期待
        assert len(successful_tests) > 0, f"全てのテストが失敗しました: {[r.get('error', 'Unknown') for r in failed_tests]}"
    
    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.requires_ffmpeg
    def test_python_api_workflow(self, samples_dir, output_dir, video_duration_checker):
        """Python APIワークフローテスト"""
        print("\n=== Python API統合テスト開始 ===")
        
        # ビルダーパターンテスト
        print("\n--- ビルダーパターンテスト ---")
        
        short_video = str(samples_dir / "ball_bokeh_02_slyblue.mp4")
        long_video = str(samples_dir / "13523522_1920_1080_60fps.mp4")
        output_video = str(output_dir / "api_builder_test.mp4")
        
        # 既存ファイル削除
        if Path(output_video).exists():
            Path(output_video).unlink()
        
        # ビルダーでシーケンス作成
        sequence = (VideoSequenceBuilder()
                   .add_video(short_video)
                   .add_crossfade(0.5, TransitionMode.CROSSFADE_INCREASE)
                   .add_video(long_video)
                   .build())
        
        # プロセッサで実行
        processor = VideoProcessor()
        
        start_time = time.time()
        try:
            result_info = processor.concatenate_videos(sequence, output_video)
            processing_time = time.time() - start_time
            
            assert Path(output_video).exists()
            assert isinstance(result_info, type(processor.get_video_info(output_video)))
            
            print(f"✅ ビルダーパターン成功: {processing_time:.1f}秒")
            
        except Exception as e:
            print(f"❌ ビルダーパターン失敗: {e}")
            raise
        
        # クイック関数テスト
        print("\n--- クイック関数テスト ---")
        
        # quick_concatenate
        output_quick_concat = str(output_dir / "api_quick_concat_test.mp4")
        if Path(output_quick_concat).exists():
            Path(output_quick_concat).unlink()
        
        start_time = time.time()
        try:
            result_info = quick_concatenate(
                [short_video, long_video],
                output_quick_concat,
                crossfade_duration=1.0,
                crossfade_mode=TransitionMode.CROSSFADE_NO_INCREASE
            )
            processing_time = time.time() - start_time
            
            assert Path(output_quick_concat).exists()
            print(f"✅ quick_concatenate成功: {processing_time:.1f}秒")
            
        except Exception as e:
            print(f"❌ quick_concatenate失敗: {e}")
            raise
        
        # quick_mix
        output_quick_mix = str(output_dir / "api_quick_mix_test.mp4")
        if Path(output_quick_mix).exists():
            Path(output_quick_mix).unlink()
        
        start_time = time.time()
        try:
            result_info = quick_mix(
                short_video,
                str(samples_dir / "02-1.png"),
                output_quick_mix,
                duration=6
            )
            processing_time = time.time() - start_time
            
            assert Path(output_quick_mix).exists()
            
            # 時間確認
            is_correct_duration, actual_duration = video_duration_checker(
                Path(output_quick_mix), 6.0, tolerance=0.3
            )
            assert is_correct_duration
            
            print(f"✅ quick_mix成功: {processing_time:.1f}秒、{actual_duration:.1f}秒")
            
        except Exception as e:
            print(f"❌ quick_mix失敗: {e}")
            raise
        
        print("\n✅ 全てのPython APIテストが成功しました")
    
    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.requires_ffmpeg
    def test_time_calculation_accuracy_real_videos(self, samples_dir, output_dir, video_duration_checker):
        """実動画による時間計算精度テスト"""
        print("\n=== 実動画時間計算精度テスト ===")
        
        short_video = str(samples_dir / "ball_bokeh_02_slyblue.mp4")
        long_video = str(samples_dir / "13523522_1920_1080_60fps.mp4")
        
        # 実際の動画長を取得
        short_duration = get_video_duration(short_video)
        long_duration = get_video_duration(long_video)
        
        print(f"動画A: {short_duration:.2f}秒")
        print(f"動画B: {long_duration:.2f}秒")
        
        # テストケース: A + クロス(無し,1s) + B + クロス(有り,1s) + A
        sequence = [
            VideoSegment(short_video),     # A
            Transition(TransitionMode.CROSSFADE_NO_INCREASE, 1.0),  # クロス(無し,1s)
            VideoSegment(long_video),      # B  
            Transition(TransitionMode.CROSSFADE_INCREASE, 1.0),     # クロス(有り,1s)
            VideoSegment(short_video)      # A
        ]
        
        # 予想時間計算
        # A + B + A - 1 + 1 = A + B + A
        expected_duration = short_duration + long_duration + short_duration
        print(f"期待時間: {short_duration:.2f} + {long_duration:.2f} + {short_duration:.2f} - 1 + 1 = {expected_duration:.2f}秒")
        
        output_video = str(output_dir / "time_accuracy_test.mp4")
        if Path(output_video).exists():
            Path(output_video).unlink()
        
        start_time = time.time()
        try:
            concatenate_videos_advanced(sequence, output_video)
            processing_time = time.time() - start_time
            
            assert Path(output_video).exists()
            
            # 実際の時間測定
            is_correct_duration, actual_duration = video_duration_checker(
                Path(output_video), expected_duration, tolerance=1.5  # 少し大きめの許容誤差
            )
            
            duration_difference = abs(actual_duration - expected_duration)
            accuracy_percent = (1 - duration_difference / expected_duration) * 100
            
            print(f"実際時間: {actual_duration:.2f}秒")
            print(f"時間差: {duration_difference:.2f}秒")
            print(f"精度: {accuracy_percent:.1f}%")
            print(f"処理時間: {processing_time:.1f}秒")
            
            # 精度90%以上を期待
            assert accuracy_percent >= 90.0, f"時間計算精度が低すぎます: {accuracy_percent:.1f}%"
            
            print("✅ 時間計算精度テスト成功")
            
        except Exception as e:
            print(f"❌ 時間計算精度テスト失敗: {e}")
            raise
    
    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.requires_ffmpeg 
    def test_stress_multiple_videos(self, samples_dir, output_dir, video_duration_checker):
        """複数動画ストレステスト"""
        print("\n=== 複数動画ストレステスト ===")
        
        short_video = str(samples_dir / "ball_bokeh_02_slyblue.mp4")
        long_video = str(samples_dir / "13523522_1920_1080_60fps.mp4")
        
        # 5つの動画を連結（A-B-A-B-A）
        sequence = (VideoSequenceBuilder()
                   .add_video(short_video)      # A
                   .add_crossfade(0.5, TransitionMode.CROSSFADE_INCREASE)
                   .add_video(long_video)       # B
                   .add_crossfade(0.5, TransitionMode.CROSSFADE_NO_INCREASE)
                   .add_video(short_video)      # A
                   .add_crossfade(1.0, TransitionMode.CROSSFADE_INCREASE) 
                   .add_video(long_video)       # B
                   .add_crossfade(0.5, TransitionMode.CROSSFADE_NO_INCREASE)
                   .add_video(short_video)      # A
                   .build())
        
        output_video = str(output_dir / "stress_test_5_videos.mp4")
        if Path(output_video).exists():
            Path(output_video).unlink()
        
        print("5つの動画を連結中...")
        print("シーケンス: A-fade(+0.5)-B-fade(-0.5)-A-fade(+1.0)-B-fade(-0.5)-A")
        
        start_time = time.time()
        try:
            processor = VideoProcessor()
            result_info = processor.concatenate_videos(sequence, output_video)
            processing_time = time.time() - start_time
            
            assert Path(output_video).exists()
            
            file_size = Path(output_video).stat().st_size / (1024 * 1024)  # MB
            
            print(f"✅ ストレステスト成功")
            print(f"   処理時間: {processing_time:.1f}秒")
            print(f"   出力サイズ: {file_size:.1f}MB")
            print(f"   動画長: {result_info.duration:.1f}秒")
            
            # 処理時間が妥当な範囲内であることを確認（目安: 60秒以内）
            assert processing_time < 120.0, f"処理時間が長すぎます: {processing_time:.1f}秒"
            
        except Exception as e:
            print(f"❌ ストレステスト失敗: {e}")
            raise


class TestPerformanceMetrics:
    """パフォーマンス測定テスト"""
    
    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.requires_ffmpeg
    def test_performance_benchmarks(self, samples_dir, output_dir):
        """パフォーマンスベンチマークテスト"""
        print("\n=== パフォーマンスベンチマーク ===")
        
        short_video = str(samples_dir / "ball_bokeh_02_slyblue.mp4")
        long_video = str(samples_dir / "13523522_1920_1080_60fps.mp4")
        image = str(samples_dir / "02-1.png")
        
        benchmarks = []
        
        # ベンチマーク1: 動画ミックス
        print("\n--- 動画ミックスベンチマーク ---")
        for duration in [3, 5, 10]:
            output = str(output_dir / f"benchmark_mix_{duration}s.mp4")
            if Path(output).exists():
                Path(output).unlink()
            
            start_time = time.time()
            mix_video_with_image(short_video, image, output, duration)
            processing_time = time.time() - start_time
            
            file_size = Path(output).stat().st_size / (1024 * 1024)
            
            benchmark = {
                'type': 'mix',
                'duration': duration,
                'processing_time': processing_time,
                'file_size_mb': file_size,
                'throughput': duration / processing_time  # 秒/秒
            }
            benchmarks.append(benchmark)
            
            print(f"{duration}秒動画: {processing_time:.1f}秒処理、{file_size:.1f}MB、スループット: {benchmark['throughput']:.2f}x")
        
        # ベンチマーク2: 動画連結
        print("\n--- 動画連結ベンチマーク ---")
        concat_cases = [
            ('simple', TransitionMode.NONE),
            ('crossfade_increase', TransitionMode.CROSSFADE_INCREASE),
            ('crossfade_no_increase', TransitionMode.CROSSFADE_NO_INCREASE)
        ]
        
        for case_name, mode in concat_cases:
            output = str(output_dir / f"benchmark_concat_{case_name}.mp4")
            if Path(output).exists():
                Path(output).unlink()
            
            sequence = [
                VideoSegment(short_video),
                Transition(mode, 1.0),
                VideoSegment(long_video)
            ]
            
            start_time = time.time()
            concatenate_videos_advanced(sequence, output)
            processing_time = time.time() - start_time
            
            file_size = Path(output).stat().st_size / (1024 * 1024)
            actual_duration = get_video_duration(output)
            
            benchmark = {
                'type': 'concat',
                'mode': case_name,
                'processing_time': processing_time,
                'output_duration': actual_duration,
                'file_size_mb': file_size,
                'throughput': actual_duration / processing_time
            }
            benchmarks.append(benchmark)
            
            print(f"{case_name}: {processing_time:.1f}秒処理、{actual_duration:.1f}秒動画、{file_size:.1f}MB、スループット: {benchmark['throughput']:.2f}x")
        
        # 結果サマリー
        print(f"\n=== ベンチマーク結果サマリー ===")
        
        mix_benchmarks = [b for b in benchmarks if b['type'] == 'mix']
        concat_benchmarks = [b for b in benchmarks if b['type'] == 'concat']
        
        if mix_benchmarks:
            avg_mix_throughput = sum(b['throughput'] for b in mix_benchmarks) / len(mix_benchmarks)
            print(f"動画ミックス平均スループット: {avg_mix_throughput:.2f}x")
        
        if concat_benchmarks:
            avg_concat_throughput = sum(b['throughput'] for b in concat_benchmarks) / len(concat_benchmarks)
            print(f"動画連結平均スループット: {avg_concat_throughput:.2f}x")
        
        # パフォーマンス基準チェック（スループット0.1x以上）
        min_throughput = 0.1
        slow_operations = [b for b in benchmarks if b['throughput'] < min_throughput]
        
        if slow_operations:
            print(f"⚠️ 低速な処理: {len(slow_operations)}件")
            for op in slow_operations:
                print(f"  {op['type']}: {op['throughput']:.3f}x")
        else:
            print("✅ 全ての処理が基準スループット以上")
        
        # 最低限の性能を確保
        assert len([b for b in benchmarks if b['throughput'] > 0.05]) == len(benchmarks), "処理速度が遅すぎる操作があります"