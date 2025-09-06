"""
mix-sample: 動画処理・合成・連結ライブラリ

動画の合成、連結、画像オーバーレイなどの処理を提供する。
"""

try:
    # パッケージとして使用される場合の相対インポート
    from .video_processing_lib import (
        VideoProcessor, VideoSequenceBuilder, VideoInfo, VideoSegment, 
        Transition, TransitionMode, VideoProcessingError,
        quick_concatenate, quick_mix, quick_crossfade
    )
    from .video_mixer import mix_video_with_image
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
    from video_mixer import mix_video_with_image
    from advanced_video_concatenator import (
        concatenate_videos_advanced, create_crossfade_video,
        CrossfadeEffect, CrossfadeOutputMode
    )

__version__ = "0.2.0"
__author__ = "mix-sample project"

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
    "mix_video_with_image",
    "concatenate_videos_advanced",
    "create_crossfade_video",
]