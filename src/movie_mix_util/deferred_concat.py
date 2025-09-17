#!/usr/bin/env python
"""
遅延実行型の動画連結ライブラリ

メソッドチェーンで動画連結タスクを定義し、
最後にexecute()を呼び出すことで、一度のFFmpegコマンドで
効率的に動画処理を実行する。
"""

from __future__ import annotations
import ffmpeg
import os
import sys
from typing import List, Tuple, Literal, Union, Any

# 既存の定義をインポート
from .video_processing_lib import DEFAULT_VIDEO_CODEC, DEFAULT_PIXEL_FORMAT, DEFAULT_HWACCEL
from .advanced_video_concatenator import (
    CrossfadeEffect,
    DEFAULT_VIDEO_WIDTH,
    DEFAULT_VIDEO_HEIGHT,
    DEFAULT_FPS,
    get_video_duration,
    TransitionMode,
)


def get_video_resolution(video_path: str) -> Tuple[int, int]:
    """
    動画ファイルの解像度を取得する。
    
    Args:
        video_path (str): 動画ファイルのパス
        
    Returns:
        Tuple[int, int]: (幅, 高さ)のタプル
        
    Raises:
        ValueError: 解像度の取得に失敗した場合
    """
    try:
        probe = ffmpeg.probe(video_path)
        for stream in probe['streams']:
            if stream['codec_type'] == 'video':
                width = int(stream['width'])
                height = int(stream['height'])
                return (width, height)
        raise ValueError("ビデオストリームが見つかりません")
    except ffmpeg.Error as e:
        raise ValueError(f"動画の解析に失敗しました: {e}")


def get_safe_bitrate_for_videotoolbox(detected_bitrate: int, width: int, height: int) -> int:
    """
    VideoToolboxで安全に使用できるビットレートを計算する。
    
    Args:
        detected_bitrate (int): 検出されたビットレート
        width (int): 動画の幅
        height (int): 動画の高さ
        
    Returns:
        int: 安全なビットレート値
    """
    # 解像度ベースの最大ビットレート制限
    if height >= 1080:
        max_safe_bitrate = 15000000  # 15Mbps for 1080p+
    elif height >= 720:
        max_safe_bitrate = 8000000   # 8Mbps for 720p
    elif height >= 480:
        max_safe_bitrate = 4000000   # 4Mbps for 480p
    else:
        max_safe_bitrate = 2000000   # 2Mbps for lower resolutions
    
    # 検出されたビットレートと安全な上限の小さい方を選択
    return min(detected_bitrate, max_safe_bitrate)


def try_videotoolbox_encode_with_bitrate_fallback(
    output_args: list,
    base_params: dict,
    target_bitrate: int,
    ffmpeg_path: str,
    quiet: bool
) -> None:
    """
    VideoToolboxエンコーダーで段階的ビットレート試行を行う。
    
    Args:
        output_args: ffmpegの出力引数
        base_params: ベースとなるエンコードパラメータ
        target_bitrate: 目標ビットレート
        ffmpeg_path: ffmpegの実行パス
        quiet: 静寂モード
        
    Raises:
        ffmpeg.Error: 全ての試行が失敗した場合
    """
    # 試行するビットレートのリスト（段階的に下げる）
    bitrate_attempts = [
        target_bitrate,
        int(target_bitrate * 0.75),  # 75%に削減
        int(target_bitrate * 0.5),   # 50%に削減
        5000000  # 最終的に5Mbps固定
    ]
    
    for i, bitrate in enumerate(bitrate_attempts):
        try:
            print(f"VideoToolboxビットレート試行 {i+1}/{len(bitrate_attempts)}: {bitrate / 1000000:.1f}Mbps")
            
            # パラメータをコピーして今回のビットレートを設定
            current_params = base_params.copy()
            current_params['b:v'] = bitrate
            
            (
                ffmpeg
                .output(*output_args, **current_params)
                .overwrite_output()
                .run(cmd=ffmpeg_path, quiet=quiet)
            )
            
            print(f"✅ VideoToolboxエンコード成功 (ビットレート: {bitrate / 1000000:.1f}Mbps)")
            return  # 成功した場合はここで終了
            
        except ffmpeg.Error as e:
            print(f"❌ ビットレート {bitrate / 1000000:.1f}Mbpsで失敗")
            
            # エラー詳細の出力（デバッグ用）
            if hasattr(e, 'stderr') and e.stderr:
                stderr_text = e.stderr.decode('utf-8', errors='ignore') if isinstance(e.stderr, bytes) else str(e.stderr)
                if "Error setting bitrate property" in stderr_text:
                    print(f"⚠️ VideoToolboxビットレートエラー検出")
                else:
                    print(f"その他のエラー: {stderr_text[:200]}...")
            
            # 最後の試行でも失敗した場合は例外を再発生
            if i == len(bitrate_attempts) - 1:
                raise e


class DeferredVideoSequence:
    """
    動画連結の遅延実行を管理するクラス。

    メソッドチェーンで操作を積み重ね、最後に `execute` を呼び出すことで
    単一のFFmpegプロセスで全ての処理を実行する。
    """

    def __init__(self, video_path: str):
        """
        シーケンスを初期化する。

        Args:
            video_path (str): 最初の動画ファイルのパス。

        Raises:
            FileNotFoundError: 指定された動画ファイルが見つからない場合。
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")
        
        self._operations = [('add_video', video_path)]

    def append(
        self,
        video_path: str,
        duration: float = 1.0,
        effect: CrossfadeEffect = CrossfadeEffect.FADE,
        mode: TransitionMode = TransitionMode.CROSSFADE_INCREASE
    ) -> DeferredVideoSequence:
        """
        シーケンスに新しい動画をトランジション付きで追加する。

        Args:
            video_path (str): 追加する動画ファイルのパス。
            duration (float): トランジションの時間（秒）。
            effect (CrossfadeEffect): 使用するトランジション効果。
            mode (TransitionMode): トランジションのモード（増加あり/なし）。

        Returns:
            DeferredVideoSequence: メソッドチェーンのための自身のインスタンス。
        
        Raises:
            FileNotFoundError: 指定された動画ファイルが見つからない場合。
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")
            
        self._operations.append(('transition', duration, effect, mode))
        self._operations.append(('add_video', video_path))
        return self

    def execute(self, output_path: str, quiet: bool = False) -> dict[str, Any]:
        """
        定義されたシーケンスに基づいて動画連結処理を実行する。

        Raises:
            RuntimeError: FFmpegの実行に失敗した場合。
            ValueError: シーケンスに動画が1つしか定義されていない場合。
        """
        video_ops = [op for op in self._operations if op[0] == 'add_video']
        if len(video_ops) < 2:
            raise ValueError("連結するには少なくとも2つの動画が必要です。")

        print("遅延実行シーケンスの処理を開始します...")

        transition_ops = [op for op in self._operations if op[0] == 'transition']

        # 最初のストリーム
        current_video_path = video_ops[0][1]
        processed_video = ffmpeg.input(current_video_path, hwaccel=DEFAULT_HWACCEL).video
        
        # オーディオストリームの有無をチェック
        try:
            probe = ffmpeg.probe(current_video_path)
            if any(s['codec_type'] == 'audio' for s in probe['streams']):
                processed_audio = ffmpeg.input(current_video_path, hwaccel=DEFAULT_HWACCEL).audio
            else:
                processed_audio = None
        except ffmpeg.Error:
            processed_audio = None
        
        total_duration = get_video_duration(current_video_path)

        for i, next_video_op in enumerate(video_ops[1:]):
            next_video_path = next_video_op[1]
            transition = transition_ops[i]
            _, duration, effect, mode = transition

            next_video_stream = ffmpeg.input(next_video_path, hwaccel=DEFAULT_HWACCEL)
            next_video_duration = get_video_duration(next_video_path)

            # ビデオのxfade
            xfade_offset = 0.0
            if mode == TransitionMode.CROSSFADE_NO_INCREASE:
                xfade_offset = total_duration - duration
            elif mode == TransitionMode.CROSSFADE_INCREASE:
                xfade_offset = total_duration

            processed_video = ffmpeg.filter(
                [processed_video.filter('fps', fps=DEFAULT_FPS), next_video_stream.video.filter('fps', fps=DEFAULT_FPS)],
                'xfade',
                transition=effect.value,
                duration=duration,
                offset=xfade_offset
            )
            
            # 音声のacrossfade
            if processed_audio:
                try:
                    next_video_probe = ffmpeg.probe(next_video_path)
                    if any(s['codec_type'] == 'audio' for s in next_video_probe['streams']):
                        processed_audio = ffmpeg.filter(
                            [processed_audio, next_video_stream.audio],
                            'acrossfade',
                            d=duration
                        )
                    else:
                        # 次の動画にオーディオがない場合、現在のオーディオストリームをそのまま維持
                        pass
                except ffmpeg.Error:
                    # 次の動画のオーディオプロファイルに失敗した場合、現在のオーディオストリームをそのまま維持
                    pass

            if mode == TransitionMode.CROSSFADE_NO_INCREASE:
                total_duration += next_video_duration - duration
            elif mode == TransitionMode.CROSSFADE_INCREASE:
                total_duration += next_video_duration

        print(f"出力ファイル: {output_path}")
        
        try:
            # 入力動画の最高ビットレートと解像度を検出
            max_bitrate = 0
            video_resolutions = []
            
            for video_op in video_ops:
                video_path = video_op[1]
                try:
                    # ビットレート検出
                    probe_result = ffmpeg.probe(video_path)
                    for stream in probe_result['streams']:
                        if stream['codec_type'] == 'video' and 'bit_rate' in stream:
                            bitrate = int(stream['bit_rate'])
                            max_bitrate = max(max_bitrate, bitrate)
                    
                    # 解像度検出
                    width, height = get_video_resolution(video_path)
                    video_resolutions.append((width, height))
                    
                except Exception as e:
                    print(f"⚠️ 動画解析エラー ({video_path}): {e}")
                    continue
            
            # デフォルトビットレート（検出できない場合）
            if max_bitrate == 0:
                max_bitrate = 5000000  # 5Mbps
            
            # 最大解像度を取得（複数動画の中で最大のもの）
            if video_resolutions:
                max_width = max(res[0] for res in video_resolutions)
                max_height = max(res[1] for res in video_resolutions)
            else:
                # フォールバック値
                max_width, max_height = DEFAULT_VIDEO_WIDTH, DEFAULT_VIDEO_HEIGHT
            
            print(f"検出された最高ビットレート: {max_bitrate / 1000000:.1f}Mbps")
            print(f"最大解像度: {max_width}x{max_height}")
            
            # VideoToolbox用の安全なビットレート計算
            if DEFAULT_VIDEO_CODEC == 'h264_videotoolbox':
                safe_bitrate = get_safe_bitrate_for_videotoolbox(max_bitrate, max_width, max_height)
                if safe_bitrate != max_bitrate:
                    print(f"VideoToolbox安全ビットレート: {safe_bitrate / 1000000:.1f}Mbps (制限適用)")
                target_bitrate = safe_bitrate
            else:
                target_bitrate = max_bitrate
            
            # ffmpegの実行可能ファイルのパスを環境変数から取得、なければデフォルト
            ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')

            if processed_audio:
                output_args = [processed_video, processed_audio, output_path]
            else:
                output_args = [processed_video, output_path]

            # エンコーダー別のパラメータ設定（ビットレートベース）
            output_params = {
                'vcodec': DEFAULT_VIDEO_CODEC,
                'pix_fmt': DEFAULT_PIXEL_FORMAT,
                'r': DEFAULT_FPS,
                'b:v': target_bitrate  # 安全なビットレートを使用
            }
            
            # ハードウェアエンコーダー用の追加パラメータ
            if DEFAULT_VIDEO_CODEC == 'h264_videotoolbox':
                # VideoToolbox用の元動画品質維持設定
                output_params.update({
                    'allow_sw': 1,  # ソフトウェアフォールバック許可
                    'realtime': 0,   # リアルタイム制約を無効化
                    'profile:v': 'high',  # プロファイル設定
                    'level': '4.1'  # レベル設定（1080p対応）
                })
            elif DEFAULT_VIDEO_CODEC == 'h264_nvenc':
                # NVENC用の元動画品質維持設定
                output_params.update({
                    'preset': 'slow',  # 品質重視
                    'profile:v': 'high'
                })
            elif DEFAULT_VIDEO_CODEC == 'h264_qsv':
                # Intel QSV用の元動画品質維持設定
                output_params.update({
                    'preset': 'slow',
                    'profile:v': 'high'
                })
            elif DEFAULT_VIDEO_CODEC == 'libx264':
                # ソフトウェアエンコーダー用の元動画品質維持設定
                output_params.update({
                    'preset': 'slow',  # 品質重視
                    'profile:v': 'high'
                })

            try:
                if DEFAULT_VIDEO_CODEC == 'h264_videotoolbox':
                    # VideoToolboxの場合は段階的ビットレート試行
                    try_videotoolbox_encode_with_bitrate_fallback(
                        output_args, output_params, target_bitrate, ffmpeg_path, quiet
                    )
                else:
                    # その他のエンコーダーは従来通り
                    (
                        ffmpeg
                        .output(*output_args, **output_params)
                        .overwrite_output()
                        .run(cmd=ffmpeg_path, quiet=quiet)
                    )
            except ffmpeg.Error as hw_error:
                # ハードウェアエンコーダーが失敗した場合、ソフトウェアエンコーダーにフォールバック
                if DEFAULT_VIDEO_CODEC != 'libx264':
                    print(f"⚠️ ハードウェアエンコーダー({DEFAULT_VIDEO_CODEC})が失敗しました。ソフトウェアエンコーダーで再試行します。")
                    
                    # エラー詳細の出力（デバッグ用）
                    if hasattr(hw_error, 'stderr') and hw_error.stderr:
                        stderr_text = hw_error.stderr.decode('utf-8', errors='ignore') if isinstance(hw_error.stderr, bytes) else str(hw_error.stderr)
                        print(f"ハードウェアエンコーダーエラー詳細: {stderr_text[:500]}...")
                    
                    fallback_params = {
                        'vcodec': 'libx264',
                        'pix_fmt': DEFAULT_PIXEL_FORMAT,
                        'r': DEFAULT_FPS,
                        'b:v': target_bitrate,  # 安全なビットレートを使用
                        'preset': 'slow',  # 品質重視
                        'profile:v': 'high'
                    }
                    (
                        ffmpeg
                        .output(*output_args, **fallback_params)
                        .overwrite_output()
                        .run(cmd=ffmpeg_path, quiet=quiet)
                    )
                else:
                    # すでにソフトウェアエンコーダーの場合は例外を再発生
                    raise hw_error
            
            print("✅ 動画連結処理が完了しました。")
            
            actual_duration = get_video_duration(output_path)
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            
            return {
                "output_path": output_path,
                "duration": actual_duration,
                "file_size_mb": file_size,
            }

        except ffmpeg.Error as e:
            # エラー詳細の詳細な取得
            stderr_text = ""
            stdout_text = ""
            
            if hasattr(e, 'stderr') and e.stderr:
                if isinstance(e.stderr, bytes):
                    stderr_text = e.stderr.decode('utf-8', errors='ignore')
                else:
                    stderr_text = str(e.stderr)
            
            if hasattr(e, 'stdout') and e.stdout:
                if isinstance(e.stdout, bytes):
                    stdout_text = e.stdout.decode('utf-8', errors='ignore')
                else:
                    stdout_text = str(e.stdout)
            
            error_detail = f"STDERR: {stderr_text}\nSTDOUT: {stdout_text}" if (stderr_text or stdout_text) else "詳細不明"
            print(f"FFmpegエラー詳細:\n{error_detail}")
            raise RuntimeError(f"FFmpegの実行に失敗しました。エラー詳細:\n{error_detail}") from e


def movie(video_path: str) -> DeferredVideoSequence:
    """
    遅延実行シーケンスを開始するためのファクトリ関数。

    Args:
        video_path (str): 最初の動画ファイルのパス。

    Returns:
        DeferredVideoSequence: 新しいシーケンスオブジェクト。
    """
    return DeferredVideoSequence(video_path)

# --- 使用例 ---
if __name__ == '__main__':
    # このスクリプトが直接実行された場合のテストコード
    import re

    SAMPLES_DIR = 'samples'
    if not os.path.exists(SAMPLES_DIR):
        print(f"エラー: サンプルディレクトリ '{SAMPLES_DIR}' が見つかりません。")
        exit(1)

    # samplesディレクトリからmp4ファイルをリストアップし、自然順ソート
    video_files = sorted(
        [f for f in os.listdir(SAMPLES_DIR) if f.endswith('.mp4')],
        key=lambda f: int(re.search(r'^(\d+)', f).group(1) if re.search(r'^(\d+)', f) else -1)
    )

    if len(video_files) < 2:
        print("エラー: 連結するには少なくとも2つの動画がsamplesディレクトリに必要です。")
        exit(1)

    # フルパスに変換
    video_paths = [os.path.join(SAMPLES_DIR, f) for f in video_files]

    output_file = 'deferred_sample_output.mp4'

    print("遅延実行型の動画連結テストを開始します...")
    print(f"入力動画: {video_files}")

    try:
        # メソッドチェーンでシーケンスを構築
        sequence = movie(video_paths[0])
        
        # トランジション効果を順番に適用
        effects = [CrossfadeEffect.WIPELEFT, CrossfadeEffect.DISSOLVE, CrossfadeEffect.SLIDERIGHT, CrossfadeEffect.FADE]
        
        for i, video_path in enumerate(video_paths[1:]):
            effect = effects[i % len(effects)] # 効果をループさせる
            print(f"- {os.path.basename(video_path)} を追加 (効果: {effect.value}, 時間: 1.5s)")
            sequence.append(video_path, duration=1.5, effect=effect)

        # 実行
        result = sequence.execute(output_file)
        
        print("""
--- 処理結果 ---""")
        for key, value in result.items():
            print(f"{key}: {value}")
        print("--------------------")

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"""
エラーが発生しました: {e}""")

