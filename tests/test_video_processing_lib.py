"""video_processing_lib（Python API）のテスト"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# テスト対象のインポート
from video_processing_lib import (
    VideoInfo,
    VideoProcessor,
    VideoSequenceBuilder,
    VideoProcessingError,
    quick_concatenate,
    quick_mix
)
from advanced_video_concatenator import TransitionMode, VideoSegment, Transition


class TestVideoInfo:
    """VideoInfoクラスのテスト"""
    
    @pytest.mark.requires_ffmpeg
    def test_video_info_from_path_short(self, test_video_short):
        """短い動画からのVideoInfo作成テスト"""
        info = VideoInfo.from_path(str(test_video_short))
        
        assert isinstance(info, VideoInfo)
        assert info.path == str(test_video_short)
        assert info.duration > 0
        assert info.width > 0
        assert info.height > 0
        assert info.fps is not None
        
        print(f"短い動画情報: {info.width}x{info.height}, {info.duration:.2f}s, {info.fps}fps")
    
    @pytest.mark.requires_ffmpeg
    def test_video_info_from_path_long(self, test_video_long):
        """長い動画からのVideoInfo作成テスト"""
        info = VideoInfo.from_path(str(test_video_long))
        
        assert isinstance(info, VideoInfo)
        assert info.duration > 0
        assert info.width == 1920  # ファイル名から推測
        assert info.height == 1080
        
        print(f"長い動画情報: {info.width}x{info.height}, {info.duration:.2f}s, {info.fps}fps")
    
    def test_video_info_from_path_nonexistent(self):
        """存在しない動画でのエラーテスト"""
        with pytest.raises(VideoProcessingError):
            VideoInfo.from_path("nonexistent_video.mp4")
    
    def test_video_info_manual_creation(self):
        """手動でのVideoInfo作成テスト"""
        info = VideoInfo(
            path="test.mp4",
            duration=30.0,
            width=1920,
            height=1080,
            fps=30.0
        )
        
        assert info.path == "test.mp4"
        assert info.duration == 30.0
        assert info.width == 1920
        assert info.height == 1080
        assert info.fps == 30.0


class TestVideoProcessor:
    """VideoProcessorクラスのテスト"""
    
    def test_video_processor_initialization_default(self):
        """デフォルト初期化テスト"""
        processor = VideoProcessor()
        
        assert processor.default_width == 1920
        assert processor.default_height == 1080
        assert processor.default_fps == 30
    
    def test_video_processor_initialization_custom(self):
        """カスタム初期化テスト"""
        processor = VideoProcessor(
            default_width=3840,
            default_height=2160,
            default_fps=60
        )
        
        assert processor.default_width == 3840
        assert processor.default_height == 2160
        assert processor.default_fps == 60
    
    @pytest.mark.requires_ffmpeg
    def test_get_video_info(self, test_video_short):
        """動画情報取得テスト"""
        processor = VideoProcessor()
        info = processor.get_video_info(str(test_video_short))
        
        assert isinstance(info, VideoInfo)
        assert info.duration > 0
    
    def test_create_simple_sequence_basic(self):
        """基本的なシーケンス作成テスト"""
        processor = VideoProcessor()
        
        video_paths = ["A.mp4", "B.mp4", "C.mp4"]
        
        with patch('pathlib.Path.exists', return_value=True):
            sequence = processor.create_simple_sequence(video_paths)
        
        # 期待される構造: Video - None - Video - None - Video
        assert len(sequence) == 5
        
        assert isinstance(sequence[0], VideoSegment)
        assert sequence[0].path == "A.mp4"
        
        assert isinstance(sequence[1], Transition)
        assert sequence[1].mode == TransitionMode.NONE
        
        assert isinstance(sequence[2], VideoSegment)
        assert sequence[2].path == "B.mp4"
    
    def test_create_simple_sequence_with_crossfade(self):
        """クロスフェイド付きシーケンス作成テスト"""
        processor = VideoProcessor()
        
        video_paths = ["A.mp4", "B.mp4"]
        crossfade_durations = [2.0]
        crossfade_modes = [TransitionMode.CROSSFADE_NO_INCREASE]
        
        with patch('pathlib.Path.exists', return_value=True):
            sequence = processor.create_simple_sequence(
                video_paths, crossfade_durations, crossfade_modes
            )
        
        assert len(sequence) == 3  # Video - Transition - Video
        
        transition = sequence[1]
        assert isinstance(transition, Transition)
        assert transition.mode == TransitionMode.CROSSFADE_NO_INCREASE
        assert transition.duration == 2.0
    
    def test_create_simple_sequence_nonexistent_file(self):
        """存在しないファイルでのエラーテスト"""
        processor = VideoProcessor()
        
        video_paths = ["nonexistent.mp4"]
        
        with pytest.raises(FileNotFoundError):
            processor.create_simple_sequence(video_paths)
    
    def test_create_simple_sequence_empty_list(self):
        """空リストでのエラーテスト"""
        processor = VideoProcessor()
        
        with pytest.raises(ValueError):
            processor.create_simple_sequence([])
    
    @patch('video_processing_lib.calculate_sequence_duration')
    def test_calculate_total_duration(self, mock_calc):
        """合計時間計算テスト"""
        mock_calc.return_value = 45.0
        
        processor = VideoProcessor()
        sequence = [VideoSegment("test.mp4")]
        
        duration = processor.calculate_total_duration(sequence)
        assert duration == 45.0
        mock_calc.assert_called_once_with(sequence)
    
    @pytest.mark.slow
    @pytest.mark.requires_ffmpeg
    def test_mix_video_with_image_integration(self, test_video_short, samples_dir, 
                                            temp_output_file):
        """動画・画像ミックスの統合テスト"""
        processor = VideoProcessor()
        
        result_info = processor.mix_video_with_image(
            str(test_video_short),
            str(samples_dir / "02-1.png"),
            str(temp_output_file),
            duration=3
        )
        
        assert isinstance(result_info, VideoInfo)
        assert temp_output_file.exists()
        assert abs(result_info.duration - 3.0) <= 0.2


class TestVideoSequenceBuilder:
    """VideoSequenceBuilderクラスのテスト"""
    
    def test_builder_empty_initialization(self):
        """空の初期化テスト"""
        builder = VideoSequenceBuilder()
        sequence = builder.build()
        
        assert len(sequence) == 0
    
    def test_builder_add_video(self):
        """動画追加テスト"""
        builder = VideoSequenceBuilder()
        result = builder.add_video("test.mp4")
        
        # メソッドチェーンの確認
        assert result is builder
        
        sequence = builder.build()
        assert len(sequence) == 1
        assert isinstance(sequence[0], VideoSegment)
        assert sequence[0].path == "test.mp4"
    
    def test_builder_add_simple_transition(self):
        """単純トランジション追加テスト"""
        builder = VideoSequenceBuilder()
        result = builder.add_simple_transition()
        
        assert result is builder
        
        sequence = builder.build()
        assert len(sequence) == 1
        assert isinstance(sequence[0], Transition)
        assert sequence[0].mode == TransitionMode.NONE
    
    def test_builder_add_crossfade_default(self):
        """デフォルトクロスフェード追加テスト"""
        builder = VideoSequenceBuilder()
        result = builder.add_crossfade()
        
        assert result is builder
        
        sequence = builder.build()
        assert len(sequence) == 1
        assert isinstance(sequence[0], Transition)
        assert sequence[0].mode == TransitionMode.CROSSFADE_INCREASE
        assert sequence[0].duration == 1.0
    
    def test_builder_add_crossfade_custom(self):
        """カスタムクロスフェード追加テスト"""
        builder = VideoSequenceBuilder()
        result = builder.add_crossfade(2.5, TransitionMode.CROSSFADE_NO_INCREASE)
        
        assert result is builder
        
        sequence = builder.build()
        assert len(sequence) == 1
        transition = sequence[0]
        assert transition.mode == TransitionMode.CROSSFADE_NO_INCREASE
        assert transition.duration == 2.5
    
    def test_builder_method_chaining(self):
        """メソッドチェーンテスト"""
        builder = VideoSequenceBuilder()
        
        sequence = (builder
                   .add_video("A.mp4")
                   .add_crossfade(1.0, TransitionMode.CROSSFADE_NO_INCREASE)
                   .add_video("B.mp4")
                   .add_simple_transition()
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
        assert sequence[3].mode == TransitionMode.NONE
        
        assert isinstance(sequence[4], VideoSegment)
        assert sequence[4].path == "C.mp4"
    
    def test_builder_clear(self):
        """クリア機能テスト"""
        builder = VideoSequenceBuilder()
        
        # データを追加
        builder.add_video("A.mp4").add_crossfade().add_video("B.mp4")
        assert len(builder.build()) == 3
        
        # クリア
        result = builder.clear()
        assert result is builder  # メソッドチェーン確認
        assert len(builder.build()) == 0
    
    def test_builder_build_isolation(self):
        """build結果の独立性テスト"""
        builder = VideoSequenceBuilder()
        builder.add_video("A.mp4").add_video("B.mp4")
        
        sequence1 = builder.build()
        sequence2 = builder.build()
        
        # 異なるオブジェクトであることを確認
        assert sequence1 is not sequence2
        assert sequence1 == sequence2  # 内容は同じ


class TestQuickFunctions:
    """便利関数のテスト"""
    
    @patch('video_processing_lib.VideoProcessor')
    def test_quick_concatenate_basic(self, mock_processor_class):
        """クイック連結の基本テスト"""
        mock_processor = MagicMock()
        mock_processor.create_simple_sequence.return_value = [VideoSegment("test.mp4")]
        mock_processor.concatenate_videos.return_value = VideoInfo("output.mp4", 10.0)
        mock_processor_class.return_value = mock_processor
        
        result = quick_concatenate(
            ["A.mp4", "B.mp4"],
            "output.mp4",
            crossfade_duration=1.5,
            crossfade_mode=TransitionMode.CROSSFADE_NO_INCREASE
        )
        
        # VideoProcessorが正しく初期化されたか
        mock_processor_class.assert_called_once()
        
        # create_simple_sequenceが正しい引数で呼ばれたか
        mock_processor.create_simple_sequence.assert_called_once_with(
            ["A.mp4", "B.mp4"],
            [1.5],  # 動画数-1の長さ
            [TransitionMode.CROSSFADE_NO_INCREASE]
        )
        
        # concatenate_videosが呼ばれたか
        mock_processor.concatenate_videos.assert_called_once()
        
        # 戻り値の確認
        assert isinstance(result, VideoInfo)
        assert result.duration == 10.0
    
    @patch('video_processing_lib.VideoProcessor')
    def test_quick_mix_basic(self, mock_processor_class):
        """クイックミックスの基本テスト"""
        mock_processor = MagicMock()
        mock_processor.mix_video_with_image.return_value = VideoInfo("output.mp4", 30.0)
        mock_processor_class.return_value = mock_processor
        
        result = quick_mix(
            "background.mp4",
            "overlay.png", 
            "output.mp4",
            duration=30
        )
        
        # VideoProcessorが正しく初期化されたか
        mock_processor_class.assert_called_once()
        
        # mix_video_with_imageが正しい引数で呼ばれたか
        mock_processor.mix_video_with_image.assert_called_once_with(
            "background.mp4",
            "overlay.png",
            "output.mp4",
            30
        )
        
        # 戻り値の確認
        assert isinstance(result, VideoInfo)
        assert result.duration == 30.0


class TestVideoProcessingError:
    """VideoProcessingError例外のテスト"""
    
    def test_video_processing_error_creation(self):
        """VideoProcessingError作成テスト"""
        error = VideoProcessingError("テストエラー")
        assert str(error) == "テストエラー"
        assert isinstance(error, Exception)
    
    def test_video_processing_error_raising(self):
        """VideoProcessingError発生テスト"""
        with pytest.raises(VideoProcessingError) as exc_info:
            raise VideoProcessingError("処理に失敗しました")
        
        assert str(exc_info.value) == "処理に失敗しました"


class TestIntegrationScenarios:
    """統合シナリオテスト"""
    
    @pytest.mark.integration
    def test_end_to_end_builder_workflow(self):
        """エンドツーエンドのビルダーワークフローテスト"""
        # 実際の使用パターンをテスト
        processor = VideoProcessor(default_width=1280, default_height=720)
        
        # ビルダーでシーケンス作成
        sequence = (VideoSequenceBuilder()
                   .add_video("intro.mp4")
                   .add_crossfade(1.0, TransitionMode.CROSSFADE_NO_INCREASE)
                   .add_video("main.mp4")
                   .add_crossfade(2.0, TransitionMode.CROSSFADE_INCREASE)
                   .add_video("outro.mp4")
                   .build())
        
        # シーケンス構造の確認
        assert len(sequence) == 5
        
        # 時間計算（モック使用）
        with patch('video_processing_lib.calculate_sequence_duration') as mock_calc:
            mock_calc.return_value = 120.0
            
            total_duration = processor.calculate_total_duration(sequence)
            assert total_duration == 120.0
        
        print("✅ エンドツーエンドワークフローテスト成功")
    
    @pytest.mark.integration
    def test_complex_sequence_scenarios(self):
        """複雑なシーケンスシナリオテスト"""
        scenarios = [
            {
                "name": "alternating_crossfade_modes",
                "sequence_builder": lambda: (
                    VideoSequenceBuilder()
                    .add_video("A.mp4")
                    .add_crossfade(1.0, TransitionMode.CROSSFADE_NO_INCREASE)
                    .add_video("B.mp4")
                    .add_crossfade(1.0, TransitionMode.CROSSFADE_INCREASE)
                    .add_video("C.mp4")
                    .add_crossfade(1.0, TransitionMode.CROSSFADE_NO_INCREASE)
                    .add_video("D.mp4")
                ),
                "expected_length": 7
            },
            {
                "name": "only_simple_transitions",
                "sequence_builder": lambda: (
                    VideoSequenceBuilder()
                    .add_video("A.mp4")
                    .add_simple_transition()
                    .add_video("B.mp4")
                    .add_simple_transition()
                    .add_video("C.mp4")
                ),
                "expected_length": 5
            },
            {
                "name": "mixed_transition_durations",
                "sequence_builder": lambda: (
                    VideoSequenceBuilder()
                    .add_video("A.mp4")
                    .add_crossfade(0.5, TransitionMode.CROSSFADE_INCREASE)
                    .add_video("B.mp4")
                    .add_crossfade(2.5, TransitionMode.CROSSFADE_NO_INCREASE)
                    .add_video("C.mp4")
                ),
                "expected_length": 5
            }
        ]
        
        for scenario in scenarios:
            print(f"\n--- {scenario['name']} ---")
            sequence = scenario['sequence_builder']().build()
            
            assert len(sequence) == scenario['expected_length']
            
            # シーケンスの構造確認（VideoとTransitionが交互に配置）
            for i, item in enumerate(sequence):
                if i % 2 == 0:  # 偶数インデックス
                    assert isinstance(item, VideoSegment), f"Index {i} should be VideoSegment"
                else:  # 奇数インデックス
                    assert isinstance(item, Transition), f"Index {i} should be Transition"
        
        print("✅ 複雑なシーケンスシナリオテスト成功")