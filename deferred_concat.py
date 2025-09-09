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
from typing import List, Tuple, Literal, Union, Any, TypedDict

# プロジェクトルートからのインポートを可能にする
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_video_concatenator import (
    CrossfadeEffect,
    DEFAULT_VIDEO_WIDTH,
    DEFAULT_VIDEO_HEIGHT,
    DEFAULT_FPS,
    DEFAULT_VIDEO_CODEC,
    DEFAULT_PIXEL_FORMAT,
    get_video_duration,
)


class ExecutionResult(TypedDict):
    """executeメソッドの戻り値の型定義"""
    output_path: str
    duration: float
    file_size_mb: float


class DeferredVideoSequence:
    """
    動画連結の遅延実行を管理するクラス。

    メソッドチェーンで操作を積み重ね、最後に `execute` を呼び出すことで
    単一のFFmpegプロセスで全ての処理を実行します。

    Attributes:
        _operations (List[Tuple[str, Any]]): 実行される操作のリスト。
    """

    def __init__(self, video_path: str):
        """
        シーケンスを初期化します。

        Args:
            video_path (str): 最初の動画ファイルのパス。

        Raises:
            FileNotFoundError: 指定された動画ファイルが見つからない場合。
        
        Example:
            >>> seq = DeferredVideoSequence("input1.mp4")
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")
        
        self._operations: List[Tuple[str, Any]] = [('add_video', video_path)]

    def append(
        self,
        video_path: str,
        duration: float = 1.0,
        effect: CrossfadeEffect = CrossfadeEffect.FADE,
        mode: Literal['overlap', 'increase'] = 'overlap'
    ) -> DeferredVideoSequence:
        """
        シーケンスに新しい動画をトランジション付きで追加します。

        Args:
            video_path (str): 追加する動画ファイルのパス。
            duration (float): トランジションの時間（秒）。デフォルトは1.0秒。
            effect (CrossfadeEffect): 使用するトランジション効果。
                                      デフォルトは `CrossfadeEffect.FADE`。

        Returns:
            DeferredVideoSequence: メソッドチェーンのための自身のインスタンス。
        
        Raises:
            FileNotFoundError: 指定された動画ファイルが見つからない場合。

        Example:
            >>> movie("in1.mp4").append("in2.mp4", duration=2.0, effect=CrossfadeEffect.DISSOLVE)
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")
            
        self._operations.append(('transition', duration, effect, mode))
        self._operations.append(('add_video', video_path))
        return self

    def execute(self, output_path: str, quiet: bool = False) -> ExecutionResult:
        """
        定義されたシーケンスに基づいて動画連結処理を実行します。

        このメソッドが呼び出されると、それまでに追加されたすべての動画と
        トランジションが一つのFFmpegコマンドにまとめられ、実行されます。

        Args:
            output_path (str): 出力する動画ファイルのパス。
            quiet (bool): FFmpegのログ出力を抑制するかどうか。デフォルトはFalse。

        Returns:
            ExecutionResult: 処理結果の詳細を含む辞書。
                - output_path (str): 出力ファイルパス。
                - duration (float): 生成された動画の実際の長さ（秒）。
                - file_size_mb (float): ファイルサイズ（MB）。

        Raises:
            RuntimeError: FFmpegの実行に失敗した場合。
            ValueError: シーケンスに動画が1つしか定義されていない場合。
        """
        video_operations = [op for op in self._operations if op[0] == 'add_video']
        if len(video_operations) < 2:
            raise ValueError("連結するには少なくとも2つの動画が必要です。")

        print("遅延実行シーケンスの処理を開始します...")

        transition_operations = [op for op in self._operations if op[0] == 'transition']

        # 最初のビデオストリームを準備
        first_video_path = video_operations[0][1]
        processed_video = (
            ffmpeg.input(first_video_path).video
            .filter('setpts', 'PTS-STARTPTS')
            .filter('fps', fps=DEFAULT_FPS, round='near')
        )
        
        # 連結後の合計時間を計算していく
        total_duration = get_video_duration(first_video_path)

        # 2つ目以降の動画を順番に連結
        for i, next_video_op in enumerate(video_operations[1:]):
            next_video_path = next_video_op[1]
            transition = transition_operations[i]
            _, trans_duration, trans_effect, trans_mode = transition

            print(f"- {os.path.basename(next_video_path)} を '{trans_effect.value}' ( {trans_duration}s, mode={trans_mode} ) で連結します。")

            next_video_stream = (
                ffmpeg.input(next_video_path).video
                .filter('setpts', 'PTS-STARTPTS')
                .filter('fps', fps=DEFAULT_FPS, round='near')
            )
            next_video_duration = get_video_duration(next_video_path)

            if trans_mode == 'overlap':
                # xfadeフィルタでビデオを連結 (オーバーラップ)
                processed_video = ffmpeg.filter(
                    [processed_video, next_video_stream],
                    'xfade',
                    transition=trans_effect.value,
                    duration=trans_duration,
                    offset=total_duration - trans_duration
                )
                # 合計時間を更新
                total_duration += next_video_duration - trans_duration
            elif trans_mode == 'increase':
                # 増加モードは未実装
                raise NotImplementedError("`increase`モードはまだ実装されていません。")
            else:
                raise ValueError(f"不明なモードが指定されました: {trans_mode}")

        print(f"出力ファイル: {output_path}")
        
        try:
            # FFmpegの実行可能ファイルのパスを環境変数から取得、なければデフォルト
            ffmpeg_path = os.getenv('FFMPEG_PATH', 'ffmpeg')

            # フィルターチェーンを実行
            (
                ffmpeg
                .output(processed_video, output_path,
                        vcodec=DEFAULT_VIDEO_CODEC,
                        pix_fmt=DEFAULT_PIXEL_FORMAT,
                        r=DEFAULT_FPS)
                .overwrite_output()
                .run(cmd=ffmpeg_path, quiet=quiet)
            )
            
            print("✅ 動画連結処理が完了しました。")
            
            # 処理結果を返す
            actual_duration = get_video_duration(output_path)
            file_size = os.path.getsize(output_path) / (1024 * 1024)
            
            return {
                "output_path": output_path,
                "duration": actual_duration,
                "file_size_mb": file_size,
            }

        except ffmpeg.Error as e:
            stderr = e.stderr.decode(errors='ignore') if e.stderr else '詳細不明'
            print(f"FFmpegエラー: {stderr}")
            raise RuntimeError(f"FFmpegの実行に失敗しました。エラー: {stderr}") from e


def movie(video_path: str) -> DeferredVideoSequence:
    """
    遅延実行シーケンスを開始するためのファクトリ関数。

    Args:
        video_path (str): 最初の動画ファイルのパス。

    Returns:
        DeferredVideoSequence: 新しいシーケンスオブジェクト。
    
    Example:
        >>> sequence = movie("intro.mp4")
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

    # samplesディレクトリからmp4ファイルをリストアップし、ファイル名の数字でソート
    try:
        video_files = sorted(
            [f for f in os.listdir(SAMPLES_DIR) if f.endswith('.mp4')],
            key=lambda f: int(re.search(r'^(\d+)', f).group(1))
        )
    except (AttributeError, ValueError):
        print(f"エラー: samples内のmp4ファイルは '数字_名前.mp4' の形式である必要があります。")
        # 数字で始まらないファイルを除外して再試行
        video_files = sorted(
            [f for f in os.listdir(SAMPLES_DIR) if f.endswith('.mp4') and re.match(r'^\d+', f)],
            key=lambda f: int(re.search(r'^(\d+)', f).group(1))
        )
        if not video_files:
            exit(1)
        print(f"数字で始まるファイルのみを対象とします: {video_files}")


    if len(video_files) < 2:
        print("エラー: 連結するには少なくとも2つの動画がsamplesディレクトリに必要です。")
        exit(1)

    # フルパスに変換
    video_paths = [os.path.join(SAMPLES_DIR, f) for f in video_files]

    output_file = 'deferred_sample_output.mp4'

    print("遅延実行型の動画連結テストを開始します...")
    print(f"入力動画: {[os.path.basename(p) for p in video_paths]}")

    try:
        # メソッドチェーンでシーケンスを構築
        sequence = movie(video_paths[0])
        
        # トランジション効果を順番に適用
        effects = [CrossfadeEffect.WIPELEFT, CrossfadeEffect.DISSOLVE, CrossfadeEffect.SLIDERIGHT, CrossfadeEffect.FADE]
        
        for i, video_path in enumerate(video_paths[1:]):
            effect = effects[i % len(effects)] # 効果をループさせる
            sequence.append(video_path, duration=1.5, effect=effect)

        # 実行
        result = sequence.execute(output_file, quiet=True)
        
        print("\n--- 処理結果 ---")
        for key, value in result.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
        print("--------------------")

    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"\nエラーが発生しました: {e}")

