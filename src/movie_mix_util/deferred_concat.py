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
from .advanced_video_concatenator import (
    CrossfadeEffect,
    DEFAULT_VIDEO_WIDTH,
    DEFAULT_VIDEO_HEIGHT,
    DEFAULT_FPS,
    DEFAULT_VIDEO_CODEC,
    DEFAULT_PIXEL_FORMAT,
    get_video_duration,
    TransitionMode,
)


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
        processed_video = ffmpeg.input(current_video_path).video
        
        # オーディオストリームの有無をチェック
        try:
            probe = ffmpeg.probe(current_video_path)
            if any(s['codec_type'] == 'audio' for s in probe['streams']):
                processed_audio = ffmpeg.input(current_video_path).audio
            else:
                processed_audio = None
        except ffmpeg.Error:
            processed_audio = None
        
        total_duration = get_video_duration(current_video_path)

        for i, next_video_op in enumerate(video_ops[1:]):
            next_video_path = next_video_op[1]
            transition = transition_ops[i]
            _, duration, effect, mode = transition

            next_video_stream = ffmpeg.input(next_video_path)
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
            # ffmpegの実行可能ファイルのパスを環境変数から取得、なければデフォルト
            ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')

            if processed_audio:
                output_args = [processed_video, processed_audio, output_path]
            else:
                output_args = [processed_video, output_path]

            (
                ffmpeg
                .output(*output_args,
                        vcodec=DEFAULT_VIDEO_CODEC,
                        pix_fmt=DEFAULT_PIXEL_FORMAT,
                        r=DEFAULT_FPS)
                .overwrite_output()
                .run(cmd=ffmpeg_path, quiet=quiet)
            )
            
            print("✅ 動画連結処理が完了しました。")
            
            actual_duration = get_video_duration(output_path)
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            
            return {
                "output_path": output_path,
                "duration": actual_duration,
                "file_size_mb": file_size,
            }

        except ffmpeg.Error as e:
            stderr = e.stderr.decode() if e.stderr else '詳細不明'
            print(f"FFmpegエラー: {stderr}")
            raise RuntimeError(f"FFmpegの実行に失敗しました。エラー: {stderr}") from e


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

