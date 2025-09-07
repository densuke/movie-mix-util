"""
movie-mix-util: Modern video processing, composition, and concatenation library

Provides advanced video processing capabilities including composition, concatenation,
crossfade effects, and image overlay operations using FFmpeg.

Features:
- Video concatenation with crossfade transitions
- Image overlay on video backgrounds
- Multiple crossfade effects (fade, dissolve, wipe, slide, etc.)
- Flexible output modes and duration control
- Type-safe API with comprehensive documentation
"""

try:
    # パッケージとして使用される場合の相対インポート
    from .video_processing_lib import (
        VideoProcessor, VideoSequenceBuilder, VideoInfo, VideoSegment, 
        Transition, TransitionMode, VideoProcessingError,
        quick_concatenate, quick_mix, quick_crossfade
    )
    from .advanced_video_concatenator import (
        concatenate_videos_advanced, create_crossfade_video,
        CrossfadeEffect, CrossfadeOutputMode
    )
except ImportError:
    # 直接実行される場合の絶対インポート
    from video_processing_lib import (
        VideoProcessor, VideoSequenceBuilder, VideoInfo, VideoSegment,
        Transition, TransitionMode, VideoProcessingError,
        quick_concatenate, quick_mix, quick_crossfade
    )
    from advanced_video_concatenator import (
        concatenate_videos_advanced, create_crossfade_video,
        CrossfadeEffect, CrossfadeOutputMode
    )

__version__ = "1.0.0"
__author__ = "movie-mix-util project"
__license__ = "MIT"
__homepage__ = "https://github.com/densuke/movie-mix-util"

__all__ = [
    # クラス
    "VideoProcessor",
    "VideoSequenceBuilder", 
    "VideoInfo",
    "VideoSegment",
    "Transition",
    "TransitionMode",
    "VideoProcessingError",
    "CrossfadeEffect",
    "CrossfadeOutputMode",
    
    # 関数
    "quick_concatenate",
    "quick_mix",
    "quick_crossfade",
    "concatenate_videos_advanced",
    "create_crossfade_video",
]