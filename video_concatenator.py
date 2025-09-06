#!/usr/bin/env python
"""
動画連結スクリプト

2つの動画を1秒間隔でクロスフェイド効果付きで連結する
"""

import ffmpeg
import sys
import os
import argparse
from typing import Union

# 定数定義
DEFAULT_VIDEO_WIDTH = 1920
DEFAULT_VIDEO_HEIGHT = 1080
DEFAULT_FPS = 30
DEFAULT_VIDEO_CODEC = 'libx264'
DEFAULT_PIXEL_FORMAT = 'yuv420p'
FRAME_DURATION = 0.033  # 1フレーム分の時間


def get_video_duration(video_path: str) -> float:
    """動画の長さを取得する
    
    Args:
        video_path: 動画ファイルのパス
        
    Returns:
        動画の長さ（秒）
    """
    try:
        probe = ffmpeg.probe(video_path)
        duration = float(probe['streams'][0]['duration'])
        return duration
    except Exception as e:
        print(f"エラー: 動画情報の取得に失敗しました: {e}")
        sys.exit(1)


def create_static_frame_background(duration: float) -> 'ffmpeg.Stream':
    """静止画背景用のカラーストリームを作成する
    
    Args:
        duration: 継続時間（秒）
        
    Returns:
        ffmpegのカラーストリーム
    """
    color_filter = f"color=black:size={DEFAULT_VIDEO_WIDTH}x{DEFAULT_VIDEO_HEIGHT}:duration={duration}:rate={DEFAULT_FPS}"
    return ffmpeg.input(color_filter, f='lavfi')


def extract_frame(video_path: str, timestamp: float, duration: float = FRAME_DURATION) -> 'ffmpeg.Stream':
    """動画からフレームを抽出する
    
    Args:
        video_path: 動画ファイルのパス
        timestamp: 抽出するフレームのタイムスタンプ（秒）
        duration: フレームの継続時間（秒）
        
    Returns:
        抽出されたフレームのストリーム
    """
    return ffmpeg.input(video_path, ss=timestamp, t=duration).video.filter('scale', DEFAULT_VIDEO_WIDTH, DEFAULT_VIDEO_HEIGHT)


def create_crossfade_segment(video1: str, video2: str, video1_duration: float, fade_duration: float) -> 'ffmpeg.Stream':
    """クロスフェイドセグメントを作成する
    
    Args:
        video1: 前の動画ファイルのパス
        video2: 後の動画ファイルのパス
        video1_duration: 前の動画の長さ（秒）
        fade_duration: フェイド時間（秒）
        
    Returns:
        クロスフェイドセグメントのストリーム
    """
    # 前動画の最後のフレームを静止画として作成
    last_frame_bg = create_static_frame_background(fade_duration)
    last_frame = extract_frame(video1, video1_duration - FRAME_DURATION, FRAME_DURATION)
    last_frame_static = ffmpeg.overlay(last_frame_bg, last_frame)
    
    # 後動画の最初のフレームを静止画として作成
    first_frame_bg = create_static_frame_background(fade_duration)
    first_frame = extract_frame(video2, 0, FRAME_DURATION)
    first_frame_static = ffmpeg.overlay(first_frame_bg, first_frame)
    
    # フェード効果を適用
    last_frame_fadeout = last_frame_static.filter('fade', type='out', start_time=0, duration=fade_duration)
    first_frame_fadein = first_frame_static.filter('fade', type='in', start_time=0, duration=fade_duration)
    
    # クロスフェイドセグメントを合成
    return ffmpeg.overlay(last_frame_fadeout, first_frame_fadein)


def concatenate_videos_with_crossfade(video1: str, video2: str, 
                                     fade_duration: float, output: str) -> None:
    """2つの動画をクロスフェイド効果で連結する
    
    構成: 前動画(完全) + クロスフェイド区間(最後フレーム→最初フレーム) + 後動画(完全)
    合計時間 = 前動画時間 + クロスフェイド時間 + 後動画時間
    
    Args:
        video1: 前の動画ファイルのパス
        video2: 後の動画ファイルのパス
        fade_duration: クロスフェイド時間（秒）
        output: 出力動画ファイルのパス
    """
    
    # 各動画の長さを取得
    duration1 = get_video_duration(video1)
    duration2 = get_video_duration(video2)
    
    print(f"前の動画の長さ: {duration1:.2f}秒")
    print(f"後の動画の長さ: {duration2:.2f}秒")
    print(f"クロスフェイド時間: {fade_duration}秒")
    
    # 合計時間 = 前動画 + クロスフェイド + 後動画
    total_duration = duration1 + fade_duration + duration2
    
    try:
        # 前の動画を読み込み（そのまま）
        input1 = ffmpeg.input(video1)
        video1_segment = input1.video
        
        # 後の動画を読み込み（そのまま）
        input2 = ffmpeg.input(video2)
        video2_segment = input2.video
        
        print("セグメント作成中...")
        print(f"- 前動画セグメント: {duration1:.1f}秒")
        
        # クロスフェイド区間を作成
        crossfade_segment = create_crossfade_segment(video1, video2, duration1, fade_duration)
        
        print(f"- クロスフェイドセグメント: {fade_duration:.1f}秒")
        print(f"- 後動画セグメント: {duration2:.1f}秒")
        
        # 3つのセグメントを連結
        segments = [
            video1_segment,      # 前の動画（完全版）
            crossfade_segment,   # クロスフェイド区間
            video2_segment       # 後の動画（完全版）
        ]
        
        # concatフィルターで連結（unsafe=1で強制連結）
        concatenated = ffmpeg.concat(*segments, v=1, a=0, unsafe=1)
        
        # 出力設定
        out = ffmpeg.output(concatenated, output,
                          vcodec=DEFAULT_VIDEO_CODEC,
                          pix_fmt=DEFAULT_PIXEL_FORMAT,
                          r=DEFAULT_FPS)
        
        # 既存ファイルがあれば上書き
        out = ffmpeg.overwrite_output(out)
        
        print("動画連結処理開始...")
        print(f"前の動画: {video1}")
        print(f"後の動画: {video2}")
        print(f"出力: {output}")
        print(f"構成: 前動画({duration1:.1f}s) + クロスフェイド({fade_duration:.1f}s) + 後動画({duration2:.1f}s)")
        print(f"合計時間: {total_duration:.1f}秒")
        
        # 実行
        ffmpeg.run(out, quiet=False)
        print("動画連結完了!")
        
    except ffmpeg.Error as e:
        print(f"FFmpegエラー: {e}")
        if e.stderr:
            print(f"詳細: {e.stderr.decode()}")
        sys.exit(1)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


def parse_arguments():
    """コマンドライン引数をパースする
    
    Returns:
        argparse.Namespace: パースされた引数
    """
    parser = argparse.ArgumentParser(
        description="2つの動画をクロスフェイド効果付きで連結",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python video_concatenator.py video1.mp4 video2.mp4 2.0 output.mp4
  python video_concatenator.py part1.mp4 part2.mp4 1.5 combined.mp4
        """
    )
    
    parser.add_argument(
        "video1",
        help="前の動画ファイルのパス"
    )
    
    parser.add_argument(
        "video2",
        help="後の動画ファイルのパス"
    )
    
    parser.add_argument(
        "fade_duration",
        type=float,
        help="フェイド時間（秒）"
    )
    
    parser.add_argument(
        "output",
        help="出力動画ファイルのパス"
    )
    
    return parser.parse_args()


def main():
    """メイン関数"""
    # コマンドライン引数をパース
    args = parse_arguments()
    
    # ファイルの存在チェック
    if not os.path.exists(args.video1):
        print(f"エラー: 前の動画ファイルが見つかりません: {args.video1}")
        sys.exit(1)
        
    if not os.path.exists(args.video2):
        print(f"エラー: 後の動画ファイルが見つかりません: {args.video2}")
        sys.exit(1)
    
    # フェイド時間をチェック
    if args.fade_duration <= 0:
        print(f"エラー: フェイド時間は0より大きい値である必要があります: {args.fade_duration}")
        sys.exit(1)
    
    if args.fade_duration > 10:
        print(f"警告: フェイド時間が長すぎます: {args.fade_duration}秒")
    
    # 動画を連結
    concatenate_videos_with_crossfade(args.video1, args.video2, 
                                    args.fade_duration, args.output)


if __name__ == "__main__":
    main()