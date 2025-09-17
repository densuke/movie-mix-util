#!/usr/bin/env python
"""
高度動画連結スクリプト

複数の動画を様々な結合モードで連結する
- 単純結合: そのまま連結
- クロスフェード(増加無し): 前動画短縮、総時間変化なし  
- クロスフェード(増加あり): フェイド時間分総時間増加
"""

import ffmpeg
import sys
import os
import argparse
from typing import List, Tuple, Literal, Union, Any
from dataclasses import dataclass
from enum import Enum

# 定数定義
DEFAULT_VIDEO_WIDTH = 1920
DEFAULT_VIDEO_HEIGHT = 1080
DEFAULT_FPS = 30
from .video_processing_lib import DEFAULT_VIDEO_CODEC, DEFAULT_PIXEL_FORMAT, DEFAULT_HWACCEL
FRAME_DURATION = 0.033  # 1フレーム分の時間


class TransitionMode(Enum):
    """結合モード定義"""
    NONE = "none"                           # 単純結合
    CROSSFADE_NO_INCREASE = "no_increase"   # クロスフェード(増加無し)
    CROSSFADE_INCREASE = "increase"         # クロスフェード(増加あり)


class CrossfadeEffect(Enum):
    """クロスフェード効果の種類"""
    FADE = "fade"                    # フェード
    DISSOLVE = "dissolve"            # ディゾルブ
    WIPELEFT = "wipeleft"            # 左ワイプ
    WIPERIGHT = "wiperight"          # 右ワイプ
    WIPEUP = "wipeup"                # 上ワイプ
    WIPEDOWN = "wipedown"            # 下ワイプ
    SLIDELEFT = "slideleft"          # 左スライド
    SLIDERIGHT = "slideright"        # 右スライド
    SLIDEUP = "slideup"              # 上スライド
    SLIDEDOWN = "slidedown"          # 下スライド
    CIRCLECROP = "circlecrop"        # サークルクロップ
    RECTCROP = "rectcrop"            # 矩形クロップ
    DISTANCE = "distance"            # 距離効果
    FADEBLACK = "fadeblack"          # ブラックフェード
    FADEWHITE = "fadewhite"          # ホワイトフェード
    RADIAL = "radial"                # 放射状
    SMOOTHLEFT = "smoothleft"        # スムース左
    SMOOTHRIGHT = "smoothright"      # スムース右
    SMOOTHUP = "smoothup"            # スムース上
    SMOOTHDOWN = "smoothdown"        # スムース下
    CIRCLEOPEN = "circleopen"        # サークルオープン
    CIRCLECLOSE = "circleclose"      # サークルクローズ
    VERTOPEN = "vertopen"            # 縦オープン
    VERTCLOSE = "vertclose"          # 縦クローズ
    HORZOPEN = "horzopen"            # 横オープン
    HORZCLOSE = "horzclose"          # 横クローズ
    DIAGBL = "diagbl"                # 左下対角
    DIAGBR = "diagbr"                # 右下対角
    DIAGTL = "diagtl"                # 左上対角
    DIAGTR = "diagtr"                # 右上対角


class CrossfadeOutputMode(Enum):
    """クロスフェード出力モード"""
    FADE_ONLY = "fade_only"          # フェード部分のみ出力
    FULL_SEQUENCE = "full_sequence"  # 動画1 + フェード + 動画2 の完全版
    CUSTOM = "custom"                # カスタム時間指定


@dataclass
class VideoSegment:
    """動画セグメント情報"""
    path: str


@dataclass
class Transition:
    """結合時のトランジション情報"""
    mode: TransitionMode
    duration: float = 1.0


def get_video_duration(video_path: str) -> float:
    """動画の長さを取得する
    
    Args:
        video_path: 動画ファイルのパス
        
    Returns:
        float: 動画の長さ（秒）
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
        'ffmpeg.Stream': ffmpegのカラーストリーム
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
        'ffmpeg.Stream': 抽出されたフレームのストリーム
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
        'ffmpeg.Stream': クロスフェイドセグメントのストリーム
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


def calculate_sequence_duration(sequence: List[Union[VideoSegment, Transition]]) -> float:
    """シーケンス全体の長さを計算する
    
    Args:
        sequence: 動画セグメントとトランジションのリスト
        
    Returns:
        シーケンス全体の長さ（秒）
    """
    total_duration = 0.0
    previous_video_duration = 0.0
    
    for item in sequence:
        if isinstance(item, VideoSegment):
            video_duration = get_video_duration(item.path)
            total_duration += video_duration
            previous_video_duration = video_duration
        elif isinstance(item, Transition):
            if item.mode == TransitionMode.CROSSFADE_NO_INCREASE:
                # 増加無し: 前動画から短縮分を差し引く
                total_duration -= item.duration
            elif item.mode == TransitionMode.CROSSFADE_INCREASE:
                # 増加あり: フェイド時間を追加
                total_duration += item.duration
            # NONE の場合は何もしない
    
    return total_duration


def concatenate_videos_advanced(sequence: List[Union[VideoSegment, Transition]], 
                              output: str) -> None:
    """複数動画を高度な結合モードで連結する
    
    Args:
        sequence: 動画セグメントとトランジションのリスト
        output_path: 出力動画ファイルのパス
    """
    
    # シーケンス検証
    if len(sequence) < 1:
        print("エラー: 少なくとも1つの動画セグメントが必要です")
        sys.exit(1)
        
    if not isinstance(sequence[0], VideoSegment):
        print("エラー: シーケンスは動画セグメントから始まる必要があります")
        sys.exit(1)
    
    # 全体時間を計算
    total_duration = calculate_sequence_duration(sequence)
    print(f"シーケンス全体の長さ: {total_duration:.2f}秒")
    
    try:
        segments_list = []
        current_video_path = None
        current_video_duration = 0.0
        
        print("シーケンス処理中...")
        
        for i, item in enumerate(sequence):
            if isinstance(item, VideoSegment):
                print(f"- 動画セグメント: {os.path.basename(item.path)}")
                current_video_path = item.path
                current_video_duration = get_video_duration(item.path)
                
                # 次の要素がno_increaseのクロスフェイドかチェック
                next_item = sequence[i + 1] if i + 1 < len(sequence) else None
                if (next_item and isinstance(next_item, Transition) and 
                    next_item.mode == TransitionMode.CROSSFADE_NO_INCREASE):
                    # 前動画を短縮
                    shortened_duration = current_video_duration - next_item.duration
                    video_input = ffmpeg.input(item.path, t=shortened_duration, hwaccel=DEFAULT_HWACCEL)
                    print(f"  短縮: {current_video_duration:.1f}s → {shortened_duration:.1f}s")
                else:
                    # そのまま
                    video_input = ffmpeg.input(item.path, hwaccel=DEFAULT_HWACCEL)
                    print(f"  長さ: {current_video_duration:.1f}s")
                
                segments_list.append(video_input.video)
                
            elif isinstance(item, Transition):
                if item.mode in [TransitionMode.CROSSFADE_NO_INCREASE, TransitionMode.CROSSFADE_INCREASE]:
                    # 次の動画セグメントを取得
                    next_video = sequence[i + 1] if i + 1 < len(sequence) else None
                    if not next_video or not isinstance(next_video, VideoSegment):
                        print("エラー: トランジションの後に動画セグメントが必要です")
                        sys.exit(1)
                    
                    print(f"- クロスフェイド: {item.duration:.1f}秒 ({item.mode.value})")
                    crossfade_segment = create_crossfade_segment(
                        current_video_path, next_video.path, 
                        current_video_duration, item.duration
                    )
                    segments_list.append(crossfade_segment)
                # NONE の場合は何もしない（単純連結）
        
        if not segments_list:
            print("エラー: 処理可能なセグメントがありません")
            sys.exit(1)
        
        print(f"セグメント数: {len(segments_list)}")
        
        # concatフィルターで連結
        if len(segments_list) == 1:
            concatenated = segments_list[0]
        else:
            concatenated = ffmpeg.concat(*segments_list, v=1, a=0, unsafe=1)
        
        # 出力設定
        out = ffmpeg.output(concatenated, output,
                          vcodec=DEFAULT_VIDEO_CODEC,
                          pix_fmt=DEFAULT_PIXEL_FORMAT,
                          r=DEFAULT_FPS)
        
        # 既存ファイルがあれば上書き
        out = ffmpeg.overwrite_output(out)
        
        print("動画連結処理開始...")
        print(f"出力: {output}")
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


def parse_crossfade_string(crossfade_str: str) -> List[Transition]:
    """クロスフェイド文字列をパースしてTransitionリストに変換
    
    Args:
        crossfade_str: "1.0:no_increase,1.5:increase" 形式の文字列
        
    Returns:
        List[Transition]: Transitionオブジェクトのリスト
    """
    if not crossfade_str:
        return []
        
    transitions = []
    parts = crossfade_str.split(',')
    
    for part in parts:
        part = part.strip()
        if ':' in part:
            duration_str, mode_str = part.split(':', 1)
            try:
                duration = float(duration_str)
                mode = TransitionMode(mode_str.strip())
                transitions.append(Transition(mode, duration))
            except (ValueError, KeyError) as e:
                print(f"エラー: 不正なクロスフェイド設定: {part}")
                sys.exit(1)
        else:
            # デフォルトモード
            try:
                duration = float(part)
                transitions.append(Transition(TransitionMode.CROSSFADE_INCREASE, duration))
            except ValueError:
                print(f"エラー: 不正なクロスフェイド設定: {part}")
                sys.exit(1)
    
    return transitions


def build_sequence_from_args(videos: List[str], transitions: List[Transition]) -> List[Union[VideoSegment, Transition]]:
    """引数から動画シーケンスを構築する
    
    Args:
        videos: 動画ファイルパスのリスト
        transitions: トランジションのリスト
        
    Returns:
        List[Union[VideoSegment, Transition]]: 動画セグメントとトランジションの交互シーケンス
    """
    sequence = []
    
    for i, video_path in enumerate(videos):
        sequence.append(VideoSegment(video_path))
        
        # 最後の動画でなければトランジション追加
        if i < len(videos) - 1:
            if i < len(transitions):
                sequence.append(transitions[i])
            else:
                # デフォルトトランジション (単純結合)
                sequence.append(Transition(TransitionMode.NONE))
    
    return sequence


def parse_arguments() -> argparse.Namespace:
    """コマンドライン引数をパースする
    
    動画連結スクリプトのコマンドライン引数をパースし、
    適切なヘルプメッセージと例を提供する。
    
    Returns:
        argparse.Namespace: パースされたコマンドライン引数
        
    Examples:
        >>> args = parse_arguments()
        >>> args.videos
        ['A.mp4', 'B.mp4', 'C.mp4']
        >>> args.output
        'result.mp4'
    """
    parser = argparse.ArgumentParser(
        description="複数動画を高度な結合モードで連結",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 単純結合
  python advanced_video_concatenator.py A.mp4 B.mp4 C.mp4 --output result.mp4

  # クロスフェイド結合
  python advanced_video_concatenator.py A.mp4 B.mp4 C.mp4 \\
    --crossfade "1.0:no_increase,1.5:increase" --output result.mp4

結合モード:
  none         - 単純結合
  no_increase  - クロスフェード(増加無し): 前動画短縮
  increase     - クロスフェード(増加あり): フェイド時間追加
        """
    )
    
    parser.add_argument(
        "videos",
        nargs="+",
        help="動画ファイルのリスト（2つ以上）"
    )
    
    parser.add_argument(
        "--crossfade",
        help="クロスフェイド設定: duration:mode,duration:mode... (例: 1.0:no_increase,1.5:increase)"
    )
    
    parser.add_argument(
        "--output",
        required=True,
        help="出力動画ファイルのパス"
    )
    
    return parser.parse_args()


def create_crossfade_video(
    video1_path: str,
    video2_path: str, 
    fade_duration: float,
    output_path: str,
    effect: CrossfadeEffect = CrossfadeEffect.FADE,
    output_mode: CrossfadeOutputMode = CrossfadeOutputMode.FADE_ONLY,
    custom_duration: float | None = None
) -> dict[str, Any]:
    """2つの動画間のクロスフェード動画を生成する
    
    Args:
        video1_path: 最初の動画ファイルパス
        video2_path: 2番目の動画ファイルパス
        fade_duration: フェード時間（秒）
        output_path: 出力動画ファイルパス
        effect: クロスフェード効果の種類
        output_mode: 出力モード
        custom_duration: カスタム時間（CUSTOM モード時）
        
    Returns:
        処理結果の詳細情報
        
    Raises:
        FileNotFoundError: 入力動画ファイルが見つからない場合
        ValueError: パラメータが不正な場合
        ffmpeg.Error: FFmpeg処理でエラーが発生した場合
    """
    # 入力ファイルの存在チェック
    for path in [video1_path, video2_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"動画ファイルが見つかりません: {path}")
    
    # 動画の長さを取得
    duration1 = get_video_duration(video1_path)
    duration2 = get_video_duration(video2_path)
    
    # パラメータ検証
    if fade_duration <= 0:
        raise ValueError("フェード時間は0より大きい値である必要があります")
    if fade_duration > min(duration1, duration2):
        raise ValueError(f"フェード時間 {fade_duration}s は動画の長さより短くする必要があります（最小: {min(duration1, duration2):.1f}s）")
    
    print(f"クロスフェード動画生成開始...")
    print(f"動画1: {os.path.basename(video1_path)} ({duration1:.1f}s)")
    print(f"動画2: {os.path.basename(video2_path)} ({duration2:.1f}s)")
    print(f"フェード時間: {fade_duration}s")
    print(f"効果: {effect.value}")
    print(f"出力モード: {output_mode.value}")
    
    try:
        # 入力ストリーム準備
        input1 = ffmpeg.input(video1_path, hwaccel=DEFAULT_HWACCEL)
        input2 = ffmpeg.input(video2_path, hwaccel=DEFAULT_HWACCEL)
        
        # 出力モードに応じた処理
        if output_mode == CrossfadeOutputMode.FADE_ONLY:
            # フェード部分のみ出力
            # 動画1の最後の部分を取得（フレームレート統一）
            video1_start = duration1 - fade_duration
            v1_trimmed = (input1.video
                         .filter('trim', start=video1_start, duration=fade_duration)
                         .filter('setpts', 'PTS-STARTPTS')
                         .filter('fps', fps=DEFAULT_FPS))
            
            # 動画2の最初の部分を取得（フレームレート統一）
            v2_trimmed = (input2.video
                         .filter('trim', duration=fade_duration)
                         .filter('setpts', 'PTS-STARTPTS')
                         .filter('fps', fps=DEFAULT_FPS))
            
            # クロスフェード適用
            crossfaded = ffmpeg.filter([v1_trimmed, v2_trimmed], 'xfade', 
                                     transition=effect.value, 
                                     duration=fade_duration,
                                     offset=0)
            
            output_duration = fade_duration
            
        elif output_mode == CrossfadeOutputMode.FULL_SEQUENCE:
            # 完全版出力（動画1 + フェード + 動画2）
            # 動画1の前部分（フレームレート統一）
            v1_before = (input1.video
                        .filter('trim', duration=duration1-fade_duration)
                        .filter('setpts', 'PTS-STARTPTS')
                        .filter('fps', fps=DEFAULT_FPS))
            
            # フェード部分（フレームレート統一）
            v1_fade = (input1.video
                      .filter('trim', start=duration1-fade_duration, duration=fade_duration)
                      .filter('setpts', 'PTS-STARTPTS')
                      .filter('fps', fps=DEFAULT_FPS))
            v2_fade = (input2.video
                      .filter('trim', duration=fade_duration)
                      .filter('setpts', 'PTS-STARTPTS')
                      .filter('fps', fps=DEFAULT_FPS))
            fade_part = ffmpeg.filter([v1_fade, v2_fade], 'xfade',
                                    transition=effect.value,
                                    duration=fade_duration,
                                    offset=0)
            
            # 動画2の後部分（フレームレート統一）
            v2_after = (input2.video
                       .filter('trim', start=fade_duration)
                       .filter('setpts', 'PTS-STARTPTS')
                       .filter('fps', fps=DEFAULT_FPS))
            
            # 全体を連結
            crossfaded = ffmpeg.concat(v1_before, fade_part, v2_after, v=1, a=0)
            output_duration = duration1 + duration2 - fade_duration
            
        elif output_mode == CrossfadeOutputMode.CUSTOM:
            # カスタム時間指定
            if custom_duration is None:
                raise ValueError("CUSTOM モードではcustom_durationの指定が必要です")
            if custom_duration <= 0:
                raise ValueError("カスタム時間は0より大きい値である必要があります")
            
            # 動画1と動画2をフェード時間で重複させて連結（フレームレート統一）
            v1_part = (input1.video
                      .filter('trim', duration=min(custom_duration/2 + fade_duration/2, duration1))
                      .filter('setpts', 'PTS-STARTPTS')
                      .filter('fps', fps=DEFAULT_FPS))
            v2_part = (input2.video
                      .filter('trim', duration=min(custom_duration/2 + fade_duration/2, duration2))
                      .filter('setpts', 'PTS-STARTPTS')
                      .filter('fps', fps=DEFAULT_FPS))
            
            crossfaded = ffmpeg.filter([v1_part, v2_part], 'xfade',
                                     transition=effect.value,
                                     duration=fade_duration,
                                     offset=custom_duration/2 - fade_duration/2)
            
            output_duration = custom_duration
            
        # 出力設定
        out = ffmpeg.output(crossfaded, output_path,
                          vcodec=DEFAULT_VIDEO_CODEC,
                          pix_fmt=DEFAULT_PIXEL_FORMAT,
                          r=DEFAULT_FPS)
        
        # 既存ファイル上書き
        out = ffmpeg.overwrite_output(out)
        
        print(f"出力: {output_path}")
        print(f"予想時間: {output_duration:.1f}s")
        
        # 実行
        ffmpeg.run(out, quiet=False)
        
        # 実際の出力時間を取得
        actual_duration = get_video_duration(output_path)
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        
        print("✅ クロスフェード動画生成完了!")
        print(f"  実際の長さ: {actual_duration:.2f}s")
        print(f"  ファイルサイズ: {file_size:.1f}MB")
        
        return {
            "output_path": output_path,
            "effect": effect.value,
            "output_mode": output_mode.value,
            "fade_duration": fade_duration,
            "expected_duration": output_duration,
            "actual_duration": actual_duration,
            "file_size_mb": file_size,
            "input_videos": [video1_path, video2_path]
        }
        
    except ffmpeg.Error as e:
        print(f"FFmpegエラー: {e}")
        if e.stderr:
            print(f"詳細: {e.stderr.decode()}")
        raise
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        raise


def main() -> None:
    """メイン関数 - コマンドラインインターフェースのエントリーポイント
    
    コマンドライン引数をパースし、動画連結処理を実行する。
    エラー発生時には適切なメッセージとともに終了する。
    
    Examples:
        $ python advanced_video_concatenator.py A.mp4 B.mp4 --output result.mp4
        $ python advanced_video_concatenator.py A.mp4 B.mp4 C.mp4 --crossfade "1.0:no_increase" --output result.mp4
    """
    # コマンドライン引数をパース
    args = parse_arguments()
    
    # 動画ファイルの存在チェック
    for video_path in args.videos:
        if not os.path.exists(video_path):
            print(f"エラー: 動画ファイルが見つかりません: {video_path}")
            sys.exit(1)
    
    if len(args.videos) < 2:
        print("エラー: 少なくとも2つの動画ファイルが必要です")
        sys.exit(1)
    
    # クロスフェイド設定をパース
    transitions = parse_crossfade_string(args.crossfade) if args.crossfade else []
    
    # シーケンスを構築
    sequence = build_sequence_from_args(args.videos, transitions)
    
    print("=== 動画連結シーケンス ===")
    for i, item in enumerate(sequence):
        if isinstance(item, VideoSegment):
            print(f"{i+1}. 動画: {os.path.basename(item.path)}")
        elif isinstance(item, Transition):
            print(f"{i+1}. 結合: {item.mode.value} ({item.duration}s)")
    print("========================")
    
    # 動画連結実行
    concatenate_videos_advanced(sequence, args.output)


if __name__ == "__main__":
    main()