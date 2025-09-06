#!/usr/bin/env python
"""
動画と静止画をミックスするプログラム

背景動画を30秒ループ再生し、静止画を中央にオーバーレイして出力する
"""

import ffmpeg
from PIL import Image
import sys
import os
import argparse
from pathlib import Path
from typing import Tuple

# 定数定義
DEFAULT_VIDEO_WIDTH = 1920
DEFAULT_VIDEO_HEIGHT = 1080
DEFAULT_FPS = 30
DEFAULT_VIDEO_CODEC = 'libx264'
DEFAULT_PIXEL_FORMAT = 'yuv420p'


def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """静止画のサイズを取得する
    
    Args:
        image_path: 画像ファイルのパス
        
    Returns:
        (幅, 高さ)のタプル
    """
    with Image.open(image_path) as img:
        return img.size


def calculate_scale_to_fit(image_width: int, image_height: int, 
                          target_width: int = DEFAULT_VIDEO_WIDTH, target_height: int = DEFAULT_VIDEO_HEIGHT) -> Tuple[int, int]:
    """画面内に収まるようにアスペクト比を保ってスケーリング計算
    
    Args:
        image_width: 元画像の幅
        image_height: 元画像の高さ
        target_width: ターゲット画面の幅
        target_height: ターゲット画面の高さ
        
    Returns:
        (新しい幅, 新しい高さ)のタプル
    """
    # アスペクト比を計算
    aspect_ratio = image_width / image_height
    target_aspect = target_width / target_height
    
    if aspect_ratio > target_aspect:
        # 横長の場合、幅を基準にスケーリング
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
    else:
        # 縦長の場合、高さを基準にスケーリング
        new_height = target_height
        new_width = int(target_height * aspect_ratio)
    
    return new_width, new_height


def calculate_position_for_centering(scaled_width: int, scaled_height: int, 
                                   target_width: int = DEFAULT_VIDEO_WIDTH, 
                                   target_height: int = DEFAULT_VIDEO_HEIGHT) -> Tuple[int, int]:
    """中央配置のオフセットを計算する
    
    Args:
        scaled_width: スケーリング後の画像の幅
        scaled_height: スケーリング後の画像の高さ
        target_width: ターゲット動画の幅
        target_height: ターゲット動画の高さ
        
    Returns:
        (x_offset, y_offset)のタプル
    """
    x_offset = (target_width - scaled_width) // 2
    y_offset = (target_height - scaled_height) // 2
    return x_offset, y_offset


def create_background_stream(background_video: str, duration: int):
    """背景動画のストリームを作成する
    
    Args:
        background_video: 背景動画のファイルパス
        duration: 動画の長さ（秒）
        
    Returns:
        ffmpegの背景動画ストリーム
    """
    return ffmpeg.input(background_video, stream_loop=-1, t=duration).video


def create_overlay_stream(overlay_image: str, duration: int, width: int, height: int):
    """オーバーレイ画像のストリームを作成する
    
    Args:
        overlay_image: オーバーレイ画像のファイルパス
        duration: 動画の長さ（秒）
        width: スケーリング後の幅
        height: スケーリング後の高さ
        
    Returns:
        ffmpegのオーバーレイストリーム
    """
    return ffmpeg.input(overlay_image, loop=1, t=duration).filter('scale', width, height)


def create_output_stream(combined_stream, output_video: str):
    """出力ストリームを作成する
    
    Args:
        combined_stream: 合成済みのストリーム
        output_video: 出力動画のファイルパス
        
    Returns:
        ffmpegの出力ストリーム
    """
    return ffmpeg.output(combined_stream, output_video, 
                       vcodec=DEFAULT_VIDEO_CODEC, 
                       pix_fmt=DEFAULT_PIXEL_FORMAT,
                       r=DEFAULT_FPS)


def mix_video_with_image(background_video: str, overlay_image: str, 
                        output_video: str, duration: int = 30) -> None:
    """背景動画と静止画をミックスして出力動画を作成
    
    Args:
        background_video: 背景動画のファイルパス
        overlay_image: オーバーレイする静止画のファイルパス
        output_video: 出力動画のファイルパス
        duration: 出力動画の長さ（秒）
    """
    
    # 静止画のサイズを取得
    img_width, img_height = get_image_dimensions(overlay_image)
    print(f"静止画サイズ: {img_width}x{img_height}")
    
    # スケーリング後のサイズを計算
    scaled_width, scaled_height = calculate_scale_to_fit(img_width, img_height)
    print(f"スケーリング後サイズ: {scaled_width}x{scaled_height}")
    
    # 中央配置のオフセット計算
    x_offset, y_offset = calculate_position_for_centering(scaled_width, scaled_height)
    print(f"配置位置: ({x_offset}, {y_offset})")
    
    try:
        # 背景動画のストリーム作成
        background = create_background_stream(background_video, duration)
        
        # オーバーレイ画像のストリーム作成
        overlay = create_overlay_stream(overlay_image, duration, scaled_width, scaled_height)
        
        # オーバーレイ合成
        combined = ffmpeg.overlay(background, overlay, x=x_offset, y=y_offset)
        
        # 出力設定
        out = create_output_stream(combined, output_video)
        
        # 既存ファイルがあれば上書き
        out = ffmpeg.overwrite_output(out)
        
        print(f"動画処理開始...")
        print(f"背景動画: {background_video}")
        print(f"オーバーレイ画像: {overlay_image}")
        print(f"出力: {output_video}")
        print(f"動画長: {duration}秒")
        
        # 実行
        ffmpeg.run(out, quiet=False)
        print("動画処理完了!")
        
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
        description="背景動画と静止画をミックスして動画を作成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python video_mixer.py background.mp4 image.png 30 output.mp4
  python video_mixer.py video.mp4 logo.png 15 result.mp4
        """
    )
    
    parser.add_argument(
        "background_video",
        help="背景動画ファイルのパス"
    )
    
    parser.add_argument(
        "overlay_image", 
        help="オーバーレイする静止画ファイルのパス"
    )
    
    parser.add_argument(
        "duration",
        type=int,
        help="出力動画の長さ（秒）"
    )
    
    parser.add_argument(
        "output_video",
        help="出力動画ファイルのパス"
    )
    
    return parser.parse_args()


def main():
    """メイン関数"""
    # コマンドライン引数をパース
    args = parse_arguments()
    
    # ファイルの存在チェック
    if not os.path.exists(args.background_video):
        print(f"エラー: 背景動画ファイルが見つかりません: {args.background_video}")
        sys.exit(1)
        
    if not os.path.exists(args.overlay_image):
        print(f"エラー: オーバーレイ画像ファイルが見つかりません: {args.overlay_image}")
        sys.exit(1)
    
    # 動画の長さをチェック
    if args.duration <= 0:
        print(f"エラー: 動画の長さは1秒以上である必要があります: {args.duration}")
        sys.exit(1)
    
    # 動画と画像をミックス
    mix_video_with_image(args.background_video, args.overlay_image, 
                        args.output_video, args.duration)


if __name__ == "__main__":
    main()