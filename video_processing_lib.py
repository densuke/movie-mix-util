#!/usr/bin/env python
"""
動画処理ライブラリ

動画の合成・連結を行うためのPython APIライブラリ
"""

from typing import List, Union, Optional
from dataclasses import dataclass
from enum import Enum
import ffmpeg
import sys
from pathlib import Path

# 既存の実装をインポート
from advanced_video_concatenator import (
    TransitionMode,
    VideoSegment, 
    Transition,
    concatenate_videos_advanced,
    get_video_duration,
    calculate_sequence_duration,
    CrossfadeEffect,
    CrossfadeOutputMode,
    create_crossfade_video
)
from video_mixer import mix_video_with_image


class VideoProcessingError(Exception):
    """動画処理固有の例外"""
    pass


@dataclass
class VideoInfo:
    """動画ファイル情報"""
    path: str
    duration: float
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None

    @classmethod
    def from_path(cls, path: str) -> 'VideoInfo':
        """ファイルパスから動画情報を取得"""
        try:
            probe = ffmpeg.probe(path)
            video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            return cls(
                path=path,
                duration=float(probe['format']['duration']),
                width=int(video_stream['width']),
                height=int(video_stream['height']),
                fps=eval(video_stream['r_frame_rate'])  # "30/1" -> 30.0
            )
        except Exception as e:
            raise VideoProcessingError(f"動画情報の取得に失敗しました: {path} - {e}")


class VideoProcessor:
    """動画処理の統合API"""
    
    def __init__(self, 
                 default_width: int = 1920,
                 default_height: int = 1080,
                 default_fps: int = 30):
        """初期化
        
        Args:
            default_width: デフォルト出力幅
            default_height: デフォルト出力高さ
            default_fps: デフォルトFPS
        """
        self.default_width = default_width
        self.default_height = default_height
        self.default_fps = default_fps
    
    def get_video_info(self, path: str) -> VideoInfo:
        """動画情報を取得
        
        Args:
            path: 動画ファイルのパス
            
        Returns:
            VideoInfo: 動画情報
        """
        return VideoInfo.from_path(path)
    
    def concatenate_videos(self, 
                          sequence: List[Union[VideoSegment, Transition]], 
                          output_path: str) -> VideoInfo:
        """動画を連結
        
        Args:
            sequence: 動画セグメントとトランジションのリスト
            output_path: 出力ファイルパス
            
        Returns:
            VideoInfo: 生成された動画の情報
            
        Raises:
            VideoProcessingError: 処理が失敗した場合
        """
        try:
            concatenate_videos_advanced(sequence, output_path)
            return self.get_video_info(output_path)
        except Exception as e:
            raise VideoProcessingError(f"動画連結に失敗しました: {e}")
    
    def mix_video_with_image(self,
                           background_video: str,
                           overlay_image: str, 
                           output_path: str,
                           duration: int = 30) -> VideoInfo:
        """動画と画像をミックス
        
        Args:
            background_video: 背景動画パス
            overlay_image: オーバーレイ画像パス
            output_path: 出力ファイルパス
            duration: 出力動画の長さ（秒）
            
        Returns:
            VideoInfo: 生成された動画の情報
            
        Raises:
            VideoProcessingError: 処理が失敗した場合
        """
        try:
            mix_video_with_image(background_video, overlay_image, output_path, duration)
            return self.get_video_info(output_path)
        except Exception as e:
            raise VideoProcessingError(f"動画・画像ミックスに失敗しました: {e}")
    
    def create_crossfade_video(self,
                              video1_path: str,
                              video2_path: str,
                              fade_duration: float,
                              output_path: str,
                              effect: CrossfadeEffect = CrossfadeEffect.FADE,
                              output_mode: CrossfadeOutputMode = CrossfadeOutputMode.FADE_ONLY,
                              custom_duration: Optional[float] = None) -> dict:
        """クロスフェード動画を生成
        
        Args:
            video1_path: 最初の動画ファイルパス
            video2_path: 2番目の動画ファイルパス
            fade_duration: フェード時間（秒）
            output_path: 出力ファイルパス
            effect: クロスフェード効果
            output_mode: 出力モード
            custom_duration: カスタム時間（CUSTOM モード時）
            
        Returns:
            dict: 処理結果の詳細情報
            
        Raises:
            VideoProcessingError: 処理が失敗した場合
        """
        try:
            return create_crossfade_video(
                video1_path=video1_path,
                video2_path=video2_path,
                fade_duration=fade_duration,
                output_path=output_path,
                effect=effect,
                output_mode=output_mode,
                custom_duration=custom_duration
            )
        except Exception as e:
            raise VideoProcessingError(f"クロスフェード動画生成に失敗しました: {e}")
    
    def create_simple_sequence(self, 
                             video_paths: List[str],
                             crossfade_durations: Optional[List[float]] = None,
                             crossfade_modes: Optional[List[TransitionMode]] = None) -> List[Union[VideoSegment, Transition]]:
        """シンプルなシーケンス作成ヘルパー
        
        Args:
            video_paths: 動画ファイルパスのリスト
            crossfade_durations: クロスフェイド時間のリスト（省略可）
            crossfade_modes: クロスフェイドモードのリスト（省略可）
            
        Returns:
            動画セグメントとトランジションのシーケンス
        """
        if len(video_paths) < 1:
            raise ValueError("少なくとも1つの動画ファイルが必要です")
        
        sequence = []
        
        for i, video_path in enumerate(video_paths):
            # ファイル存在チェック
            if not Path(video_path).exists():
                raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")
            
            sequence.append(VideoSegment(video_path))
            
            # 最後の動画でなければトランジション追加
            if i < len(video_paths) - 1:
                duration = 1.0  # デフォルト
                mode = TransitionMode.NONE  # デフォルト
                
                if crossfade_durations and i < len(crossfade_durations):
                    duration = crossfade_durations[i]
                    mode = TransitionMode.CROSSFADE_INCREASE  # デフォルトはincreaseモード
                
                if crossfade_modes and i < len(crossfade_modes):
                    mode = crossfade_modes[i]
                
                sequence.append(Transition(mode, duration))
        
        return sequence
    
    def calculate_total_duration(self, sequence: List[Union[VideoSegment, Transition]]) -> float:
        """シーケンスの合計時間を計算
        
        Args:
            sequence: 動画セグメントとトランジションのシーケンス
            
        Returns:
            合計時間（秒）
        """
        return calculate_sequence_duration(sequence)


class VideoSequenceBuilder:
    """動画シーケンス構築用のビルダークラス"""
    
    def __init__(self):
        self._sequence: List[Union[VideoSegment, Transition]] = []
    
    def add_video(self, path: str) -> 'VideoSequenceBuilder':
        """動画を追加
        
        Args:
            path: 動画ファイルのパス
            
        Returns:
            self: メソッドチェーン用
        """
        self._sequence.append(VideoSegment(path))
        return self
    
    def add_simple_transition(self) -> 'VideoSequenceBuilder':
        """単純結合を追加
        
        Returns:
            self: メソッドチェーン用
        """
        self._sequence.append(Transition(TransitionMode.NONE))
        return self
    
    def add_crossfade(self, 
                     duration: float = 1.0, 
                     mode: TransitionMode = TransitionMode.CROSSFADE_INCREASE) -> 'VideoSequenceBuilder':
        """クロスフェイドを追加
        
        Args:
            duration: フェイド時間
            mode: フェイドモード
            
        Returns:
            self: メソッドチェーン用
        """
        self._sequence.append(Transition(mode, duration))
        return self
    
    def build(self) -> List[Union[VideoSegment, Transition]]:
        """シーケンスを構築
        
        Returns:
            構築されたシーケンス
        """
        return self._sequence.copy()
    
    def clear(self) -> 'VideoSequenceBuilder':
        """シーケンスをクリア
        
        Returns:
            self: メソッドチェーン用
        """
        self._sequence.clear()
        return self


# 便利関数
def quick_concatenate(video_paths: List[str], 
                     output_path: str,
                     crossfade_duration: float = 1.0,
                     crossfade_mode: TransitionMode = TransitionMode.CROSSFADE_INCREASE) -> VideoInfo:
    """クイック動画連結（すべて同じクロスフェイド設定）
    
    Args:
        video_paths: 動画ファイルパスのリスト
        output_path: 出力ファイルパス
        crossfade_duration: クロスフェイド時間
        crossfade_mode: クロスフェイドモード
        
    Returns:
        VideoInfo: 生成された動画の情報
    """
    processor = VideoProcessor()
    
    # 全て同じ設定でシーケンス作成
    crossfade_durations = [crossfade_duration] * (len(video_paths) - 1)
    crossfade_modes = [crossfade_mode] * (len(video_paths) - 1)
    
    sequence = processor.create_simple_sequence(
        video_paths, crossfade_durations, crossfade_modes
    )
    
    return processor.concatenate_videos(sequence, output_path)


def quick_mix(background_video: str,
              overlay_image: str, 
              output_path: str,
              duration: int = 30) -> VideoInfo:
    """クイック動画・画像ミックス
    
    Args:
        background_video: 背景動画パス
        overlay_image: オーバーレイ画像パス
        output_path: 出力ファイルパス
        duration: 動画長（秒）
        
    Returns:
        VideoInfo: 生成された動画の情報
    """
    processor = VideoProcessor()
    return processor.mix_video_with_image(background_video, overlay_image, output_path, duration)


def quick_crossfade(video1_path: str,
                   video2_path: str,
                   output_path: str, 
                   fade_duration: float = 2.0,
                   effect: CrossfadeEffect = CrossfadeEffect.FADE,
                   output_mode: CrossfadeOutputMode = CrossfadeOutputMode.FADE_ONLY) -> dict:
    """クイッククロスフェード動画生成
    
    Args:
        video1_path: 最初の動画ファイルパス
        video2_path: 2番目の動画ファイルパス
        output_path: 出力ファイルパス
        fade_duration: フェード時間（秒）
        effect: クロスフェード効果
        output_mode: 出力モード
        
    Returns:
        dict: 処理結果の詳細情報
    """
    return create_crossfade_video(
        video1_path=video1_path,
        video2_path=video2_path,
        fade_duration=fade_duration,
        output_path=output_path,
        effect=effect,
        output_mode=output_mode
    )


# 使用例
if __name__ == "__main__":
    # 例1: ビルダーパターンでシーケンス作成
    builder = VideoSequenceBuilder()
    sequence = (builder
                .add_video("A.mp4")
                .add_crossfade(1.0, TransitionMode.CROSSFADE_NO_INCREASE)
                .add_video("B.mp4") 
                .add_crossfade(1.5, TransitionMode.CROSSFADE_INCREASE)
                .add_video("C.mp4")
                .build())
    
    # 例2: プロセッサで実行
    processor = VideoProcessor()
    result = processor.concatenate_videos(sequence, "output.mp4")
    print(f"生成された動画: {result.duration:.1f}秒")
    
    # 例3: クイック連結
    result = quick_concatenate(
        ["A.mp4", "B.mp4", "C.mp4"], 
        "quick_output.mp4",
        crossfade_duration=2.0,
        crossfade_mode=TransitionMode.CROSSFADE_NO_INCREASE
    )
    print(f"クイック連結: {result.duration:.1f}秒")