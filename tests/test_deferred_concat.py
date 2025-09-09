#!/usr/bin/env python
"""
DeferredVideoSequence の単体テスト
"""

import pytest
import os
import sys
from pathlib import Path

# テスト対象のモジュールをインポート
# プロジェクトルートをパスに追加
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from deferred_concat import movie, DeferredVideoSequence
from advanced_video_concatenator import CrossfadeEffect


SAMPLES_DIR = project_root / 'samples'
OUTPUT_DIR = current_dir / 'output'


@pytest.fixture(scope="session", autouse=True)
def setup_output_directory():
    """テスト用の出力ディレクトリを作成するフィクスチャ"""
    OUTPUT_DIR.mkdir(exist_ok=True)


@pytest.fixture
def sample_videos() -> list[str]:
    """サンプル動画ファイルのリストを提供するフィクスチャ"""
    videos = [
        str(SAMPLES_DIR / '01_13523522_1920_1080_60fps.mp4'),
        str(SAMPLES_DIR / '02_ball_bokeh_02_slyblue.mp4'),
        str(SAMPLES_DIR / '03_intensive_line_02_color.mp4'),
    ]
    for v in videos:
        if not os.path.exists(v):
            pytest.skip(f"サンプル動画が見つかりません: {v}")
    return videos


def test_two_videos_concatenation(sample_videos):
    """2つの動画を正常に連結できるかテスト"""
    video1, video2 = sample_videos[:2]
    output_path = str(OUTPUT_DIR / "test_two_videos.mp4")

    result = (
        movie(video1)
        .append(video2, duration=1.0, effect=CrossfadeEffect.FADE, mode='overlap')
        .execute(output_path, quiet=True)
    )

    assert os.path.exists(output_path)
    assert result['output_path'] == output_path
    assert result['duration'] > 0
    assert result['file_size_mb'] > 0


def test_three_videos_concatenation(sample_videos):
    """3つの動画を正常に連結できるかテスト"""
    video1, video2, video3 = sample_videos
    output_path = str(OUTPUT_DIR / "test_three_videos.mp4")

    result = (
        movie(video1)
        .append(video2, duration=1.0, effect=CrossfadeEffect.WIPELEFT, mode='overlap')
        .append(video3, duration=1.5, effect=CrossfadeEffect.DISSOLVE, mode='overlap')
        .execute(output_path, quiet=True)
    )

    assert os.path.exists(output_path)
    assert result['duration'] > 0


def test_file_not_found_error():
    """存在しないファイルで初期化した場合にエラーが発生するかテスト"""
    with pytest.raises(FileNotFoundError):
        movie("non_existent_video.mp4")

    with pytest.raises(FileNotFoundError):
        m = movie(str(SAMPLES_DIR / '01_13523522_1920_1080_60fps.mp4'))
        m.append("non_existent_video.mp4")


def test_single_video_error():
    """動画が1つしか指定されていない場合にValueErrorが発生するかテスト"""
    video1 = str(SAMPLES_DIR / '01_13523522_1920_1080_60fps.mp4')
    output_path = str(OUTPUT_DIR / "test_single_video.mp4")

    with pytest.raises(ValueError, match="連結するには少なくとも2つの動画が必要です。"):
        movie(video1).execute(output_path)


def test_method_chaining_returns_self(sample_videos):
    """appendメソッドが自身のインスタンスを返すかテスト"""
    video1, video2 = sample_videos[:2]
    sequence = movie(video1)
    chained_sequence = sequence.append(video2, mode='overlap')
    assert sequence is chained_sequence

def test_increase_mode_raises_not_implemented_error(sample_videos):
    """increaseモードでNotImplementedErrorが発生するかテスト"""
    video1, video2 = sample_videos[:2]
    output_path = str(OUTPUT_DIR / "test_increase_mode.mp4")

    with pytest.raises(NotImplementedError, match="`increase`モードはまだ実装されていません。"):
        (
            movie(video1)
            .append(video2, duration=1.0, mode='increase')
            .execute(output_path, quiet=True)
        )