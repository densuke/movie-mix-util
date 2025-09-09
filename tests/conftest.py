"""pytest設定とフィクスチャ"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch
from pathlib import Path
import ffmpeg


@pytest.fixture
def samples_dir():
    """サンプルファイルディレクトリのパス"""
    return Path(__file__).parent.parent / "samples"


@pytest.fixture
def test_video_short(samples_dir):
    """短い動画ファイル（ball_bokeh_02_slyblue.mp4）"""
    return samples_dir / "02_ball_bokeh_02_slyblue.mp4"


@pytest.fixture  
def test_video_long(samples_dir):
    """長い動画ファイル（13523522_1920_1080_60fps.mp4）"""
    return samples_dir / "01_13523522_1920_1080_60fps.mp4"


@pytest.fixture
def test_image(samples_dir):
    """テスト用画像ファイル（02-1.png）"""
    return samples_dir / "02-1.png"


@pytest.fixture
def output_dir():
    """テスト出力用ディレクトリ"""
    output_path = Path(__file__).parent / "output"
    output_path.mkdir(exist_ok=True)
    return output_path


@pytest.fixture
def temp_output_file(output_dir):
    """一時的な出力ファイル（テスト後自動削除）"""
    temp_file = output_dir / f"temp_test_{os.getpid()}.mp4"
    
    yield temp_file
    
    # テスト終了後にクリーンアップ
    if temp_file.exists():
        temp_file.unlink()


@pytest.fixture
def video_duration_checker():
    """動画の長さをチェックする関数"""
    def check_duration(video_path: Path, expected_duration: float, tolerance: float = 0.1):
        """動画の長さを検証
        
        Args:
            video_path: 動画ファイルのパス
            expected_duration: 期待する動画長（秒）
            tolerance: 許容誤差（秒）
        
        Returns:
            bool: 期待時間内かどうか
        """
        try:
            probe = ffmpeg.probe(str(video_path))
            actual_duration = float(probe['format']['duration'])
            
            difference = abs(actual_duration - expected_duration)
            return difference <= tolerance, actual_duration
            
        except Exception as e:
            pytest.fail(f"動画情報の取得に失敗: {e}")
    
    return check_duration


@pytest.fixture
def video_properties_checker():
    """動画プロパティ（解像度、フレームレートなど）をチェックする関数"""
    def check_properties(video_path: Path):
        """動画のプロパティを取得・検証
        
        Args:
            video_path: 動画ファイルのパス
            
        Returns:
            dict: 動画のプロパティ情報
        """
        try:
            probe = ffmpeg.probe(str(video_path))
            video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            return {
                'duration': float(probe['format']['duration']),
                'width': int(video_stream['width']),
                'height': int(video_stream['height']),
                'fps': eval(video_stream['r_frame_rate']) if 'r_frame_rate' in video_stream else None,
                'codec': video_stream['codec_name'],
                'pixel_format': video_stream.get('pix_fmt', 'unknown')
            }
            
        except Exception as e:
            pytest.fail(f"動画プロパティの取得に失敗: {e}")
    
    return check_properties


@pytest.fixture
def sample_video_durations():
    """サンプル動画の長さ情報（テスト用参考値）"""
    return {
        "02_ball_bokeh_02_slyblue.mp4": 5.0,  # 5秒に短縮したため
        "01_13523522_1920_1080_60fps.mp4": 5.0  # 5秒に短縮したため
    }


@pytest.fixture
def mock_ffmpeg_probe(monkeypatch, samples_dir):
    """ffmpeg.probeをモックし、ダミーの動画情報を返す"""
    def mock_probe(filename):
        filename_str = str(Path(filename).name)
        
        if filename_str == "01_13523522_1920_1080_60fps.mp4":
            return {
                "format": {"duration": "5.0", "size": "1000000"},
                "streams": [
                    {"codec_type": "video", "width": 1920, "height": 1080, "r_frame_rate": "60/1"}
                ]
            }
        elif filename_str == "02_ball_bokeh_02_slyblue.mp4":
            return {
                "format": {"duration": "5.0", "size": "500000"},
                "streams": [
                    {"codec_type": "video", "width": 1920, "height": 1080, "r_frame_rate": "30/1"}
                ]
            }
        elif filename_str == "nonexistent_video.mp4":
            raise ffmpeg.Error(cmd="ffprobe", stdout=b"", stderr=b"No such file or directory")
        else:
            # その他の動画ファイルは、実際のprobeを呼び出すか、エラーを発生させる
            # ここでは、テストで使われる可能性のある他の動画ファイルも考慮
            # 必要に応じて追加
            return {
                "format": {"duration": "10.0", "size": "2000000"},
                "streams": [
                    {"codec_type": "video", "width": 1920, "height": 1080, "r_frame_rate": "30/1"}
                ]
            }

    monkeypatch.setattr(ffmpeg, "probe", mock_probe)


@pytest.fixture
def mock_ffmpeg_run(monkeypatch):
    """ffmpeg.runをモックし、実際のFFmpeg実行をスキップする"""
    def mock_run(stream_spec, cmd="ffmpeg", capture_stdout=False, capture_stderr=False, input=None, quiet=False, overwrite_output=False):
        # output_pathが指定されていれば、ダミーのファイルを作成
        output_path = None
        if isinstance(stream_spec, ffmpeg.nodes.FilterNode):
            # フィルターノードの場合、出力パスはstream_specには含まれない
            # ここでは簡易的に、テストで使われるであろうoutput_pathを推測
            # 実際のコードでは、outputノードからパスを取得する
            pass
        elif isinstance(stream_spec, ffmpeg.nodes.OutputNode):
            output_path = stream_spec.args[-1] # 最後の引数が出力パスと仮定
        
        if output_path and not Path(output_path).parent.exists():
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        if output_path:
            with open(output_path, "w") as f:
                f.write("dummy video content") # ダミーコンテンツ
        
        # 成功したかのように振る舞う
        return b"", b"" # stdout, stderr

    monkeypatch.setattr(ffmpeg, "run", mock_run)


@pytest.fixture
def cleanup_output_files(output_dir):
    """テスト前後の出力ディレクトリクリーンアップ"""
    # テスト前は何もしない
    yield
    
    # テスト終了後、temp_で始まるファイルをクリーンアップ
    for temp_file in output_dir.glob("temp_*"):
        if temp_file.is_file():
            try:
                temp_file.unlink()
            except Exception:
                pass  # クリーンアップエラーは無視


# テストスキップ条件
def pytest_configure(config):
    """pytest設定"""
    config.addinivalue_line("markers", "slow: 時間のかかるテスト")
    config.addinivalue_line("markers", "integration: 統合テスト")
    config.addinivalue_line("markers", "requires_ffmpeg: FFmpegが必要なテスト")


@pytest.fixture(scope="session", autouse=True)
def check_ffmpeg_availability():
    """FFmpegが利用可能かチェック（セッション開始時）"""
    try:
        # FFmpegのバージョンチェックのみ行う（ファイル依存なし）
        import subprocess
        result = subprocess.run(["ffmpeg", "-version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpegが利用可能です")
        else:
            print("⚠️ FFmpegの実行で問題があります")
    except Exception as e:
        print(f"⚠️ FFmpegが利用できません: {e}")
        # pytestスキップしない（高速テストを実行可能にするため）