#!/usr/bin/env python
"""
動画処理ライブラリ

動画の合成・連結を行うためのPython APIライブラリ
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import ffmpeg
import sys
from pathlib import Path
from typing import Any, Tuple
import platform
import os

# 定数定義
DEFAULT_VIDEO_WIDTH = 1920
DEFAULT_VIDEO_HEIGHT = 1080
DEFAULT_FPS = 30
DEFAULT_PIXEL_FORMAT = 'yuv420p'

# ハードウェアアクセラレーションの検出と設定
def _get_hw_codec_and_accel() -> Tuple[str, str | None]:
    """OSとFFmpegのビルド情報に基づいて最適なハードウェアコーデックとアクセラレータを検出する"""
    hw_codec = 'libx264'  # デフォルトはソフトウェアエンコーダ
    hw_accel = None

    # 環境変数でハードウェアアクセラレーションを無効化
    if os.getenv('MOVIE_MIX_DISABLE_HWACCEL', '0') == '1':
        print("環境変数 MOVIE_MIX_DISABLE_HWACCEL=1 が設定されているため、ハードウェアアクセラレーションを無効にします。")
        return hw_codec, hw_accel

    try:
        import subprocess
        
        # FFmpegの利用可能なエンコーダを取得
        encoders_result = subprocess.run(['ffmpeg', '-encoders'], 
                                       capture_output=True, text=True, check=False)
        available_encoders = []
        if encoders_result.returncode == 0:
            for line in encoders_result.stdout.split('\n'):
                if 'h264' in line and ('libx264' in line or 'videotoolbox' in line or 'nvenc' in line or 'qsv' in line or 'vaapi' in line):
                    if 'libx264' in line:
                        available_encoders.append('libx264')
                    if 'h264_videotoolbox' in line:
                        available_encoders.append('h264_videotoolbox')
                    if 'h264_nvenc' in line:
                        available_encoders.append('h264_nvenc')
                    if 'h264_qsv' in line:
                        available_encoders.append('h264_qsv')
                    if 'h264_vaapi' in line:
                        available_encoders.append('h264_vaapi')
        
        # FFmpegの利用可能なハードウェアアクセラレーションを取得
        hwaccels_result = subprocess.run(['ffmpeg', '-hwaccels'], 
                                       capture_output=True, text=True, check=False)
        available_hwaccels = []
        if hwaccels_result.returncode == 0:
            for line in hwaccels_result.stdout.split('\n'):
                line = line.strip()
                if line and line not in ['Hardware acceleration methods:', '']:
                    available_hwaccels.append(line)
        
        sys.stderr.write(f"DEBUG: Available encoders: {available_encoders}\n")
        sys.stderr.write(f"DEBUG: Available hwaccels: {available_hwaccels}\n")

        system = platform.system()

        if system == 'Darwin':  # macOS
            if 'h264_videotoolbox' in available_encoders:
                hw_codec = 'h264_videotoolbox'
                hw_accel = 'videotoolbox'
                print(f"macOS: VideoToolboxハードウェアアクセラレーションを有効化します ({hw_codec})")
            else:
                print("macOS: h264_videotoolboxが見つかりません。ソフトウェアエンコーダを使用します。")
        elif system == 'Windows':
            # NVIDIA NVENC
            if 'h264_nvenc' in available_encoders:
                hw_codec = 'h264_nvenc'
                hw_accel = 'cuda' # または 'd3d11va', 'dxva2'
                print(f"Windows: NVIDIA NVENCハードウェアアクセラレーションを有効化します ({hw_codec})")
            # Intel Quick Sync Video (QSV)
            elif 'h264_qsv' in available_encoders:
                hw_codec = 'h264_qsv'
                hw_accel = 'qsv'
                print(f"Windows: Intel QSVハードウェアアクセラレーションを有効化します ({hw_codec})")
            else:
                print("Windows: NVIDIA NVENCまたはIntel QSVが見つかりません。ソフトウェアエンコーダを使用します。")
        elif system == 'Linux':
            # NVIDIA NVENC
            if 'h264_nvenc' in available_encoders:
                hw_codec = 'h264_nvenc'
                hw_accel = 'cuda'
                print(f"Linux: NVIDIA NVENCハードウェアアクセラレーションを有効化します ({hw_codec})")
            # Intel Quick Sync Video (QSV)
            elif 'h264_qsv' in available_encoders:
                hw_codec = 'h264_qsv'
                hw_accel = 'qsv'
                print(f"Linux: Intel QSVハードウェアアクセラレーションを有効化します ({hw_codec})")
            # VAAPI (Intel, AMD, etc.)
            elif 'h264_vaapi' in available_encoders and 'vaapi' in available_hwaccels:
                hw_codec = 'h264_vaapi'
                hw_accel = 'vaapi'
                print(f"Linux: VAAPIハードウェアアクセラレーションを有効化します ({hw_codec})")
            else:
                print("Linux: ハードウェアエンコーダが見つかりません。ソフトウェアエンコーダを使用します。")
        else:
            print(f"不明なOS ({system}): ソフトウェアエンコーダを使用します。")

    except Exception as e:
        print(f"FFmpegビルド情報の取得中にエラーが発生しました: {e}。ソフトウェアエンコーダを使用します。")

    return hw_codec, hw_accel

DEFAULT_VIDEO_CODEC, DEFAULT_HWACCEL = _get_hw_codec_and_accel()
print(f"DEBUG: Initialized with DEFAULT_VIDEO_CODEC: {DEFAULT_VIDEO_CODEC}, DEFAULT_HWACCEL: {DEFAULT_HWACCEL}")


# 既存の実装をインポート

# 既存の実装をインポート
from .advanced_video_concatenator import (
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
# from video_mixer import mix_video_with_image  # TODO: 実装が必要


class VideoProcessingError(Exception):
    """動画処理固有の例外"""
    pass


@dataclass
class VideoInfo:
    """動画ファイル情報を格納するデータクラス
    
    Attributes:
        path: 動画ファイルのパス
        duration: 動画の長さ（秒）
        width: 動画の幅（ピクセル）
        height: 動画の高さ（ピクセル）
        fps: フレームレート（fps）
    """
    path: str
    duration: float
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    size_mb: float | None = None

    @classmethod
    def from_path(cls, path: str) -> VideoInfo:
        """ファイルパスから動画情報を取得する
        
        Args:
            path: 動画ファイルのパス
            
        Returns:
            VideoInfo: 動画情報オブジェクト
            
        Raises:
            VideoProcessingError: 動画情報の取得に失敗した場合
            
        Examples:
            >>> info = VideoInfo.from_path("sample.mp4")
            >>> print(f"Duration: {info.duration}s, Resolution: {info.width}x{info.height}")
        """
        try:
            probe = ffmpeg.probe(path)
            video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
            
            # フレームレートを安全に解析
            frame_rate_str = video_stream['r_frame_rate']
            if '/' in frame_rate_str:
                num, den = frame_rate_str.split('/')
                fps = float(num) / float(den) if float(den) != 0 else None
            else:
                fps = float(frame_rate_str)
            
            return cls(
                path=path,
                duration=float(probe['format']['duration']),
                width=int(video_stream['width']),
                height=int(video_stream['height']),
                fps=fps
            )
        except Exception as e:
            raise VideoProcessingError(f"動画情報の取得に失敗しました: {path} - {e}")


class VideoProcessor:
    """動画処理の統合APIクラス
    
    動画の連結、ミックス、クロスフェード生成などの動画処理機能を提供する
    統合インターフェースクラス。
    
    Attributes:
        default_width: デフォルト出力幅（ピクセル）
        default_height: デフォルト出力高さ（ピクセル）
        default_fps: デフォルトフレームレート（fps）
    """
    
    def __init__(self, 
                 default_width: int = 1920,
                 default_height: int = 1080,
                 default_fps: int = 30) -> None:
        """VideoProcessorを初期化する
        
        Args:
            default_width: デフォルト出力幅（ピクセル）
            default_height: デフォルト出力高さ（ピクセル）
            default_fps: デフォルトフレームレート（fps）
        
        Examples:
            >>> processor = VideoProcessor(default_width=3840, default_height=2160)
            >>> processor.default_width
            3840
        """
        self.default_width = default_width
        self.default_height = default_height
        self.default_fps = default_fps
    
    def get_video_info(self, path: str) -> VideoInfo:
        """動画ファイルの情報を取得する
        
        Args:
            path: 動画ファイルのパス
            
        Returns:
            VideoInfo: 動画情報オブジェクト
        
        Raises:
            VideoProcessingError: 動画情報の取得に失敗した場合
        
        Examples:
            >>> processor = VideoProcessor()
            >>> info = processor.get_video_info("sample.mp4")
            >>> print(f"Duration: {info.duration}s")
        """
        return VideoInfo.from_path(path)
    
    def concatenate_videos(self, 
                          sequence: list[VideoSegment | Transition], 
                          output_path: str) -> VideoInfo:
        """動画を連結する
        
        Args:
            sequence: 動画セグメントとトランジションのリスト
            output_path: 出力ファイルパス
            
        Returns:
            VideoInfo: 生成された動画の情報
            
        Raises:
            VideoProcessingError: 処理が失敗した場合
            
        Examples:
            >>> processor = VideoProcessor()
            >>> sequence = [VideoSegment("A.mp4"), Transition(TransitionMode.NONE), VideoSegment("B.mp4")]
            >>> result = processor.concatenate_videos(sequence, "output.mp4")
            >>> print(f"Output duration: {result.duration}s")
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
                           duration: float = 30.0) -> VideoInfo:
        """動画と画像をミックスして新しい動画を生成する
        
        背景動画の上に画像をオーバーレイして、指定した長さの動画を生成する。
        
        Args:
            background_video: 背景動画のファイルパス
            overlay_image: オーバーレイする画像のファイルパス
            output_path: 出力動画ファイルのパス
            duration: 出力動画の長さ（秒）
            
        Returns:
            VideoInfo: 生成された動画の情報
            
        Raises:
            VideoProcessingError: 処理が失敗した場合
            
        Examples:
            >>> processor = VideoProcessor()
            >>> result = processor.mix_video_with_image(
            ...     "background.mp4", "overlay.png", "output.mp4", duration=10
            ... )
            >>> print(f"Mixed video created: {result.path}")
        """
        try:
            # 静止画のサイズを取得
            from PIL import Image
            with Image.open(overlay_image) as img:
                img_width, img_height = img.size
            
            # スケーリング後のサイズを計算
            aspect_ratio = img_width / img_height
            target_aspect = 1920 / 1080
            
            if aspect_ratio > target_aspect:
                scaled_width = 1920
                scaled_height = int(1920 / aspect_ratio)
            else:
                scaled_height = 1080
                scaled_width = int(1080 * aspect_ratio)
            
            # 中央配置のオフセット計算
            x_offset = (1920 - scaled_width) // 2
            y_offset = (1080 - scaled_height) // 2
            
            # FFmpegでの処理
            import ffmpeg
            
            # 背景動画のストリーム作成
            input_kwargs = {'stream_loop': -1, 't': duration}
            if DEFAULT_HWACCEL:
                input_kwargs['hwaccel'] = DEFAULT_HWACCEL
            background = ffmpeg.input(background_video, **input_kwargs).video
            
            # オーバーレイ画像のストリーム作成
            overlay = ffmpeg.input(overlay_image, loop=1, t=duration).filter('scale', scaled_width, scaled_height)
            
            # オーバーレイ合成
            combined = ffmpeg.overlay(background, overlay, x=x_offset, y=y_offset)
            
            # 出力設定
            out = ffmpeg.output(combined, output_path, 
                               vcodec=DEFAULT_VIDEO_CODEC, 
                               pix_fmt='yuv420p',
                               r=30)
            
            # 既存ファイルがあれば上書き
            out = ffmpeg.overwrite_output(out)
            
            # 実行
            ffmpeg.run(out, quiet=False)
            
            # 結果情報を作成
            import os
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            
            return VideoInfo(
                path=output_path,
                duration=float(duration),
                width=1920,
                height=1080,
                fps=30.0,
                size_mb=file_size_mb
            )
        except Exception as e:
            raise VideoProcessingError(f"動画・画像ミックスに失敗しました: {e}")
    
    def create_crossfade_video(self,
                              video1_path: str,
                              video2_path: str,
                              fade_duration: float,
                              output_path: str,
                              effect: CrossfadeEffect = CrossfadeEffect.FADE,
                              output_mode: CrossfadeOutputMode = CrossfadeOutputMode.FADE_ONLY,
                              custom_duration: float | None = None) -> dict[str, Any]:
        """2つの動画間でクロスフェード動画を生成する
        
        2つの動画間に様々な効果でクロスフェード遷移を適用し、
        新しい動画を生成する。
        
        Args:
            video1_path: 最初の動画ファイルパス
            video2_path: 2番目の動画ファイルパス
            fade_duration: フェード時間（秒）
            output_path: 出力ファイルパス
            effect: クロスフェード効果の種類
            output_mode: 出力モード（フェード部分のみ/完全版/カスタム）
            custom_duration: カスタム時間（CUSTOM モード時に必要）
            
        Returns:
            dict[str, Any]: 処理結果の詳細情報（出力パス、効果、時間等）
            
        Raises:
            VideoProcessingError: 処理が失敗した場合
            ValueError: パラメータが不正な場合
            
        Examples:
            >>> processor = VideoProcessor()
            >>> result = processor.create_crossfade_video(
            ...     "video1.mp4", "video2.mp4", 2.0, "crossfade.mp4",
            ...     effect=CrossfadeEffect.DISSOLVE
            ... )
            >>> print(f"Crossfade created: {result['actual_duration']}s")
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
                             video_paths: list[str],
                             crossfade_durations: list[float] | None = None,
                             crossfade_modes: list[TransitionMode] | None = None) -> list[VideoSegment | Transition]:
        """シンプルな動画シーケンスを作成するヘルパーメソッド
        
        動画ファイルのリストから、指定されたクロスフェイド設定で
        動画シーケンスを自動生成する。
        
        Args:
            video_paths: 動画ファイルパスのリスト
            crossfade_durations: 各トランジションのクロスフェイド時間のリスト（省略可）
            crossfade_modes: 各トランジションのクロスフェイドモードのリスト（省略可）
            
        Returns:
            list[VideoSegment | Transition]: 動画セグメントとトランジションのシーケンス
        
        Raises:
            ValueError: 動画ファイルが1つも指定されていない場合
            FileNotFoundError: 指定された動画ファイルが存在しない場合
            
        Examples:
            >>> processor = VideoProcessor()
            >>> sequence = processor.create_simple_sequence(
            ...     ["A.mp4", "B.mp4", "C.mp4"],
            ...     crossfade_durations=[1.0, 2.0],
            ...     crossfade_modes=[TransitionMode.CROSSFADE_NO_INCREASE, TransitionMode.CROSSFADE_INCREASE]
            ... )
            >>> len(sequence)  # Video + Transition + Video + Transition + Video
            5
        """
        if len(video_paths) < 1:
            raise ValueError("少なくとも1つの動画ファイルが必要です")
        
        sequence: list[VideoSegment | Transition] = []
        
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
    
    def calculate_total_duration(self, sequence: list[VideoSegment | Transition]) -> float:
        """シーケンスの合計時間を計算する
        
        動画セグメントとトランジションから構成されるシーケンスの
        合計再生時間を計算する。
        
        Args:
            sequence: 動画セグメントとトランジションのシーケンス
            
        Returns:
            float: 合計時間（秒）
        
        Examples:
            >>> processor = VideoProcessor()
            >>> sequence = [VideoSegment("A.mp4"), Transition(TransitionMode.NONE), VideoSegment("B.mp4")]
            >>> total_time = processor.calculate_total_duration(sequence)
            >>> print(f"Total duration: {total_time}s")
        """
        return calculate_sequence_duration(sequence)


class VideoSequenceBuilder:
    """動画シーケンス構築用のビルダークラス
    
    メソッドチェーンパターンを使用して、動画セグメントとトランジションから
    構成される動画シーケンスを直感的に構築するためのクラス。
    
    Attributes:
        _sequence: 構築中の動画シーケンス
        
    Examples:
        >>> builder = VideoSequenceBuilder()
        >>> sequence = (builder
        ...     .add_video("A.mp4")
        ...     .add_crossfade(1.0, TransitionMode.CROSSFADE_NO_INCREASE)
        ...     .add_video("B.mp4")
        ...     .build())
    """
    
    def __init__(self) -> None:
        """VideoSequenceBuilderを初期化する"""
        self._sequence: list[VideoSegment | Transition] = []
    
    def add_video(self, path: str) -> VideoSequenceBuilder:
        """動画をシーケンスに追加する
        
        Args:
            path: 動画ファイルのパス
            
        Returns:
            VideoSequenceBuilder: メソッドチェーン用の自身のインスタンス
        
        Examples:
            >>> builder = VideoSequenceBuilder()
            >>> builder.add_video("sample.mp4")
            <VideoSequenceBuilder object>
        """
        self._sequence.append(VideoSegment(path))
        return self
    
    def add_simple_transition(self) -> VideoSequenceBuilder:
        """単純結合トランジションをシーケンスに追加する
        
        動画間に特別な効果を適用しない、単純な結合トランジションを追加する。
        
        Returns:
            VideoSequenceBuilder: メソッドチェーン用の自身のインスタンス
        
        Examples:
            >>> builder = VideoSequenceBuilder()
            >>> builder.add_video("A.mp4").add_simple_transition().add_video("B.mp4")
            <VideoSequenceBuilder object>
        """
        self._sequence.append(Transition(TransitionMode.NONE))
        return self
    
    def add_crossfade(self, 
                     duration: float = 1.0, 
                     mode: TransitionMode = TransitionMode.CROSSFADE_INCREASE) -> VideoSequenceBuilder:
        """クロスフェードトランジションをシーケンスに追加する
        
        動画間にクロスフェード効果を適用するトランジションを追加する。
        
        Args:
            duration: フェイド時間（秒）
            mode: フェイドモード（増加あり/なし）
            
        Returns:
            VideoSequenceBuilder: メソッドチェーン用の自身のインスタンス
        
        Examples:
            >>> builder = VideoSequenceBuilder()
            >>> builder.add_crossfade(2.0, TransitionMode.CROSSFADE_NO_INCREASE)
            <VideoSequenceBuilder object>
        """
        self._sequence.append(Transition(mode, duration))
        return self
    
    def build(self) -> list[VideoSegment | Transition]:
        """構築したシーケンスを取得する
        
        これまでに追加された動画セグメントとトランジションのシーケンスの
        コピーを返す。
        
        Returns:
            list[VideoSegment | Transition]: 構築されたシーケンス
        
        Examples:
            >>> builder = VideoSequenceBuilder()
            >>> builder.add_video("A.mp4").add_crossfade()
            >>> sequence = builder.build()
            >>> len(sequence)
            2
        """
        return self._sequence.copy()
    
    def clear(self) -> VideoSequenceBuilder:
        """シーケンスをクリアする
        
        これまでに追加されたすべての動画セグメントとトランジションを削除し、
        空の状態に戻す。
        
        Returns:
            VideoSequenceBuilder: メソッドチェーン用の自身のインスタンス
        
        Examples:
            >>> builder = VideoSequenceBuilder()
            >>> builder.add_video("A.mp4").clear()
            >>> len(builder.build())
            0
        """
        self._sequence.clear()
        return self


# 便利関数
def quick_concatenate(video_paths: list[str], 
                     output_path: str,
                     crossfade_duration: float = 1.0,
                     crossfade_mode: TransitionMode = TransitionMode.CROSSFADE_INCREASE) -> VideoInfo:
    """複数の動画を同じクロスフェイド設定で素早く連結する便利関数
    
    すべてのトランジションに同じクロスフェイド設定を適用して、
    複数の動画を連結する。
    
    Args:
        video_paths: 動画ファイルパスのリスト（2つ以上）
        output_path: 出力ファイルパス
        crossfade_duration: 各クロスフェイドの時間（秒）
        crossfade_mode: 各クロスフェイドのモード
        
    Returns:
        VideoInfo: 生成された動画の情報
    
    Raises:
        ValueError: 動画ファイルが2つ未満の場合
        FileNotFoundError: 指定された動画ファイルが存在しない場合
        VideoProcessingError: 処理が失敗した場合
    
    Examples:
        >>> result = quick_concatenate(
        ...     ["A.mp4", "B.mp4", "C.mp4"],
        ...     "output.mp4",
        ...     crossfade_duration=2.0,
        ...     crossfade_mode=TransitionMode.CROSSFADE_NO_INCREASE
        ... )
        >>> print(f"Generated video: {result.duration}s")
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
              duration: float = 30.0) -> VideoInfo:
    """動画と画像を素早くミックスする便利関数
    
    背景動画の上に画像をオーバーレイして、指定した長さの動画を生成する。
    
    Args:
        background_video: 背景動画のファイルパス
        overlay_image: オーバーレイする画像のファイルパス
        output_path: 出力動画ファイルのパス
        duration: 動画の長さ（秒）
        
    Returns:
        VideoInfo: 生成された動画の情報
    
    Raises:
        FileNotFoundError: 指定されたファイルが存在しない場合
        VideoProcessingError: 処理が失敗した場合
    
    Examples:
        >>> result = quick_mix("background.mp4", "overlay.png", "mixed.mp4", duration=60)
        >>> print(f"Mixed video duration: {result.duration}s")
    """
    processor = VideoProcessor()
    return processor.mix_video_with_image(background_video, overlay_image, output_path, duration)


def quick_crossfade(video1_path: str,
                   video2_path: str,
                   output_path: str, 
                   fade_duration: float = 2.0,
                   effect: CrossfadeEffect = CrossfadeEffect.FADE,
                   output_mode: CrossfadeOutputMode = CrossfadeOutputMode.FADE_ONLY) -> dict[str, Any]:
    """2つの動画間でクロスフェード動画を素早く生成する便利関数
    
    2つの動画間に指定した効果でクロスフェード遷移を適用し、
    新しい動画を生成する。
    
    Args:
        video1_path: 最初の動画ファイルパス
        video2_path: 2番目の動画ファイルパス
        output_path: 出力動画ファイルパス
        fade_duration: フェード時間（秒）
        effect: クロスフェード効果の種類
        output_mode: 出力モード（フェード部分のみ/完全版/カスタム）
        
    Returns:
        dict[str, Any]: 処理結果の詳細情報（出力パス、効果、時間等）
    
    Raises:
        FileNotFoundError: 指定された動画ファイルが存在しない場合
        ValueError: パラメータが不正な場合
        ffmpeg.Error: FFmpeg処理でエラーが発生した場合
    
    Examples:
        >>> result = quick_crossfade(
        ...     "video1.mp4", "video2.mp4", "crossfade.mp4",
        ...     fade_duration=3.0, effect=CrossfadeEffect.DISSOLVE
        ... )
        >>> print(f"Crossfade duration: {result['actual_duration']}s")
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
