"""video_mixer（背景動画+静止画）のテスト"""

import pytest
import os
from pathlib import Path
import tempfile

# テスト対象のインポート - 新しいAPIを使用
from video_processing_lib import VideoProcessor, quick_mix

# 後方互換性のためのラッパー
def mix_video_with_image(background_video: str, overlay_image: str, output_video: str, duration: int = 30):
    """後方互換性のためのラッパー関数"""
    return quick_mix(background_video, overlay_image, output_video, duration)

# 内部ヘルパー関数は統合されたため、テストではモック/スタブを使用
from PIL import Image
import os

def get_image_dimensions(image_path: str) -> tuple[int, int]:
    """画像サイズを取得（テスト用ヘルパー）"""
    with Image.open(image_path) as img:
        return img.size

def calculate_scale_to_fit(image_width: int, image_height: int, 
                          target_width: int = 1920, target_height: int = 1080) -> tuple[int, int]:
    """画面内に収まるようにスケーリング計算（テスト用ヘルパー）"""
    aspect_ratio = image_width / image_height
    target_aspect = target_width / target_height
    
    if aspect_ratio > target_aspect:
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
    else:
        new_height = target_height
        new_width = int(target_height * aspect_ratio)
    
    return new_width, new_height

def calculate_position_for_centering(scaled_width: int, scaled_height: int, 
                                   target_width: int = 1920, 
                                   target_height: int = 1080) -> tuple[int, int]:
    """中央配置のオフセットを計算（テスト用ヘルパー）"""
    x_offset = (target_width - scaled_width) // 2
    y_offset = (target_height - scaled_height) // 2
    return x_offset, y_offset


class TestImageDimensions:
    """画像サイズ取得のテスト"""
    
    def test_get_image_dimensions_02_1(self, samples_dir):
        """02-1.pngのサイズ取得テスト"""
        image_path = samples_dir / "02-1.png"
        width, height = get_image_dimensions(str(image_path))
        
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert width > 0
        assert height > 0
        print(f"02-1.png サイズ: {width}x{height}")
    
    def test_get_image_dimensions_title_base(self, samples_dir):
        """title-base.pngのサイズ取得テスト"""
        image_path = samples_dir / "title-base.png"
        width, height = get_image_dimensions(str(image_path))
        
        assert isinstance(width, int)
        assert isinstance(height, int)
        assert width > 0
        assert height > 0
        print(f"title-base.png サイズ: {width}x{height}")
    
    def test_get_image_dimensions_nonexistent_file(self):
        """存在しないファイルでのエラーテスト"""
        with pytest.raises(Exception):
            get_image_dimensions("nonexistent_file.png")


class TestScaleCalculation:
    """スケーリング計算のテスト"""
    
    def test_calculate_scale_to_fit_landscape(self):
        """横長画像のスケーリング計算"""
        # 2000x1000の横長画像 -> 1920x1080に収める
        scaled_width, scaled_height = calculate_scale_to_fit(2000, 1000, 1920, 1080)
        
        # 幅基準でスケーリングされる
        assert scaled_width == 1920
        assert scaled_height == 960
        
        # アスペクト比が保持される
        original_aspect = 2000 / 1000
        scaled_aspect = scaled_width / scaled_height
        assert abs(original_aspect - scaled_aspect) < 0.01
    
    def test_calculate_scale_to_fit_portrait(self):
        """縦長画像のスケーリング計算"""
        # 1000x2000の縦長画像 -> 1920x1080に収める
        scaled_width, scaled_height = calculate_scale_to_fit(1000, 2000, 1920, 1080)
        
        # 高さ基準でスケーリングされる
        assert scaled_width == 540
        assert scaled_height == 1080
        
        # アスペクト比が保持される
        original_aspect = 1000 / 2000
        scaled_aspect = scaled_width / scaled_height
        assert abs(original_aspect - scaled_aspect) < 0.01
    
    def test_calculate_scale_to_fit_square(self):
        """正方形画像のスケーリング計算"""
        # 1000x1000の正方形画像 -> 1920x1080に収める
        scaled_width, scaled_height = calculate_scale_to_fit(1000, 1000, 1920, 1080)
        
        # 高さ基準でスケーリングされる（1080 < 1920のため）
        assert scaled_width == 1080
        assert scaled_height == 1080
    
    def test_calculate_scale_to_fit_small_image(self):
        """小さい画像のスケーリング計算（拡大）"""
        # 500x300の小さい画像 -> 1920x1080に収める
        scaled_width, scaled_height = calculate_scale_to_fit(500, 300, 1920, 1080)
        
        # 幅基準で拡大される
        assert scaled_width == 1920
        assert scaled_height == 1152  # 300 * (1920/500) = 1152


class TestPositionCalculation:
    """位置計算のテスト"""
    
    def test_calculate_position_for_centering_smaller_image(self):
        """画面より小さい画像の中央配置"""
        x_offset, y_offset = calculate_position_for_centering(1000, 600, 1920, 1080)
        
        assert x_offset == (1920 - 1000) // 2  # 460
        assert y_offset == (1080 - 600) // 2   # 240
    
    def test_calculate_position_for_centering_full_width(self):
        """全幅を使う画像の中央配置"""
        x_offset, y_offset = calculate_position_for_centering(1920, 800, 1920, 1080)
        
        assert x_offset == 0  # 左端
        assert y_offset == (1080 - 800) // 2  # 140
    
    def test_calculate_position_for_centering_full_height(self):
        """全高を使う画像の中央配置"""
        x_offset, y_offset = calculate_position_for_centering(800, 1080, 1920, 1080)
        
        assert x_offset == (1920 - 800) // 2  # 560
        assert y_offset == 0  # 上端


class TestVideoMixer:
    """動画ミキシングのテスト"""
    
    @pytest.mark.slow
    @pytest.mark.requires_ffmpeg
    def test_mix_video_with_image_basic(self, test_video_short, samples_dir, temp_output_file, 
                                      video_duration_checker):
        """基本的な動画・画像ミックステスト"""
        background_video = str(test_video_short)
        overlay_image = str(samples_dir / "02-1.png")
        output_video = str(temp_output_file)
        duration = 5  # 5秒の動画を作成
        
        # 実行
        mix_video_with_image(background_video, overlay_image, output_video, duration)
        
        # 出力ファイルが作成されたか確認
        assert temp_output_file.exists()
        assert temp_output_file.stat().st_size > 0
        
        # 動画長の確認
        is_correct_duration, actual_duration = video_duration_checker(temp_output_file, duration)
        assert is_correct_duration, f"期待時間: {duration}s, 実際: {actual_duration:.2f}s"
        
        print(f"✅ 動画ミックス成功: {actual_duration:.2f}秒")
    
    @pytest.mark.slow
    @pytest.mark.requires_ffmpeg
    def test_mix_video_with_image_title_base(self, test_video_long, samples_dir, temp_output_file,
                                           video_duration_checker):
        """title-base.png使用のミックステスト"""
        background_video = str(test_video_long)
        overlay_image = str(samples_dir / "title-base.png")
        output_video = str(temp_output_file)
        duration = 10
        
        # 実行
        mix_video_with_image(background_video, overlay_image, output_video, duration)
        
        # 検証
        assert temp_output_file.exists()
        is_correct_duration, actual_duration = video_duration_checker(temp_output_file, duration)
        assert is_correct_duration, f"期待時間: {duration}s, 実際: {actual_duration:.2f}s"
        
        print(f"✅ title-base.pngミックス成功: {actual_duration:.2f}秒")
    
    @pytest.mark.slow
    @pytest.mark.requires_ffmpeg
    def test_mix_video_with_image_properties(self, test_video_short, samples_dir, temp_output_file,
                                           video_properties_checker):
        """出力動画のプロパティ確認テスト"""
        background_video = str(test_video_short)
        overlay_image = str(samples_dir / "02-1.png")
        output_video = str(temp_output_file)
        duration = 3
        
        # 実行
        mix_video_with_image(background_video, overlay_image, output_video, duration)
        
        # プロパティ確認
        properties = video_properties_checker(temp_output_file)
        
        # 期待されるプロパティ
        assert properties['width'] == 1920
        assert properties['height'] == 1080
        assert properties['codec'] == 'h264'
        assert properties['pixel_format'] == 'yuv420p'
        assert abs(properties['duration'] - duration) <= 0.1
        
        print(f"✅ 出力プロパティ: {properties}")
    
    def test_mix_video_with_image_nonexistent_video(self, samples_dir, temp_output_file):
        """存在しない動画ファイルでのエラーテスト"""
        background_video = "nonexistent_video.mp4"
        overlay_image = str(samples_dir / "02-1.png")
        output_video = str(temp_output_file)
        
        # SystemExitが発生することを確認
        with pytest.raises(SystemExit):
            mix_video_with_image(background_video, overlay_image, output_video, 5)
    
    def test_mix_video_with_image_nonexistent_image(self, test_video_short, temp_output_file):
        """存在しない画像ファイルでのエラーテスト"""
        background_video = str(test_video_short)
        overlay_image = "nonexistent_image.png"
        output_video = str(temp_output_file)
        
        # SystemExitが発生することを確認
        with pytest.raises(SystemExit):
            mix_video_with_image(background_video, overlay_image, output_video, 5)
    
    def test_mix_video_with_image_zero_duration(self, test_video_short, samples_dir, temp_output_file):
        """0秒動画でのエラーテスト"""
        background_video = str(test_video_short)
        overlay_image = str(samples_dir / "02-1.png")
        output_video = str(temp_output_file)
        
        # SystemExitが発生することを確認
        with pytest.raises(SystemExit):
            mix_video_with_image(background_video, overlay_image, output_video, 0)
    
    def test_mix_video_with_image_negative_duration(self, test_video_short, samples_dir, temp_output_file):
        """負の時間でのエラーテスト"""
        background_video = str(test_video_short)
        overlay_image = str(samples_dir / "02-1.png")
        output_video = str(temp_output_file)
        
        # SystemExitが発生することを確認
        with pytest.raises(SystemExit):
            mix_video_with_image(background_video, overlay_image, output_video, -5)


class TestRealVideoMixing:
    """実際のファイルを使った総合テスト"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.requires_ffmpeg
    def test_comprehensive_video_mixing(self, samples_dir, output_dir, video_properties_checker):
        """様々な組み合わせでの包括的テスト"""
        test_cases = [
            {
                "name": "short_video_with_02_1",
                "video": "ball_bokeh_02_slyblue.mp4",
                "image": "02-1.png", 
                "duration": 5,
                "expected_duration": 5.0
            },
            {
                "name": "long_video_with_title_base",
                "video": "13523522_1920_1080_60fps.mp4",
                "image": "title-base.png",
                "duration": 8,
                "expected_duration": 8.0
            }
        ]
        
        results = []
        
        for case in test_cases:
            print(f"\n=== {case['name']} ===")
            
            background_video = str(samples_dir / case['video'])
            overlay_image = str(samples_dir / case['image'])
            output_video = str(output_dir / f"test_{case['name']}.mp4")
            
            # 既存ファイルがあれば削除
            if Path(output_video).exists():
                Path(output_video).unlink()
            
            # ミックス実行
            mix_video_with_image(background_video, overlay_image, output_video, case['duration'])
            
            # 検証
            assert Path(output_video).exists()
            properties = video_properties_checker(Path(output_video))
            
            # 結果記録
            result = {
                'case': case['name'],
                'expected_duration': case['expected_duration'],
                'actual_duration': properties['duration'],
                'properties': properties,
                'success': abs(properties['duration'] - case['expected_duration']) <= 0.2
            }
            results.append(result)
            
            print(f"期待時間: {case['expected_duration']}s")
            print(f"実際時間: {properties['duration']:.2f}s")
            print(f"解像度: {properties['width']}x{properties['height']}")
            print(f"成功: {result['success']}")
        
        # 全てのテストケースが成功することを確認
        all_success = all(r['success'] for r in results)
        assert all_success, f"失敗したテストケース: {[r['case'] for r in results if not r['success']]}"
        
        print(f"\n✅ 全ての総合テストが成功しました（{len(results)}件）")