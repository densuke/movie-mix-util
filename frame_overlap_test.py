#!/usr/bin/env python
"""
フレーム重複問題の確認テスト

xfadeフィルターで生成されたクロスフェード動画の
最初と最後のフレームが元動画と重複しているかを検証
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from advanced_video_concatenator import create_crossfade_video, CrossfadeEffect, CrossfadeOutputMode


def extract_frame(video_path: str, frame_position: str, output_path: str) -> bool:
    """動画からフレームを抽出
    
    Args:
        video_path: 動画ファイルパス
        frame_position: フレーム位置 ("first" or "last")
        output_path: 出力画像パス
        
    Returns:
        bool: 成功したかどうか
    """
    try:
        if frame_position == "first":
            # 最初のフレーム
            cmd = ["ffmpeg", "-i", video_path, "-vframes", "1", "-f", "image2", "-y", output_path]
        elif frame_position == "last":
            # 最後のフレーム - フレーム数を取得してから最終フレームを抽出
            frame_count_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
                              "-count_frames", "-show_entries", "stream=nb_frames", 
                              "-of", "csv=p=0", video_path]
            frame_result = subprocess.run(frame_count_cmd, capture_output=True, text=True)
            
            if frame_result.returncode == 0 and frame_result.stdout.strip().isdigit():
                # フレーム数が取得できた場合
                total_frames = int(frame_result.stdout.strip())
                last_frame_idx = total_frames - 1
                cmd = ["ffmpeg", "-i", video_path, "-vf", f"select='eq(n\\,{last_frame_idx})'", 
                      "-vframes", "1", "-f", "image2", "-y", output_path]
            else:
                # フォールバック: 動画の最後から0.1秒前の位置で抽出
                duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
                               "-of", "default=noprint_wrappers=1:nokey=1", video_path]
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
                if duration_result.returncode == 0:
                    try:
                        duration = float(duration_result.stdout.strip())
                        seek_time = max(0, duration - 0.033)  # 約1フレーム前
                        cmd = ["ffmpeg", "-ss", str(seek_time), "-i", video_path, 
                              "-vframes", "1", "-f", "image2", "-y", output_path]
                    except ValueError:
                        # さらなるフォールバック: reverse selectを使用
                        cmd = ["ffmpeg", "-i", video_path, "-vf", "select='eq(pict_type\\,I)'", 
                              "-vframes", "1", "-f", "image2", "-y", output_path]
                else:
                    return False
        else:
            raise ValueError("frame_position must be 'first' or 'last'")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg stderr: {result.stderr}")
            print(f"FFmpeg command: {' '.join(cmd)}")
        return result.returncode == 0
        
    except Exception as e:
        print(f"フレーム抽出エラー: {e}")
        return False


def compare_images(img1_path: str, img2_path: str) -> bool:
    """2つの画像を比較
    
    Args:
        img1_path: 画像1のパス
        img2_path: 画像2のパス
        
    Returns:
        bool: 同じ画像かどうか
    """
    try:
        # ImageMagickのcompareコマンドを使用
        cmd = ["compare", "-metric", "AE", img1_path, img2_path, "null:"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # AE (Absolute Error) が0なら同じ画像
        if result.returncode == 0:
            ae_value = int(result.stderr.strip()) if result.stderr.strip().isdigit() else 1
            return ae_value == 0
        else:
            # ImageMagickがない場合はファイルサイズで簡易比較
            size1 = os.path.getsize(img1_path)
            size2 = os.path.getsize(img2_path)
            return size1 == size2
            
    except Exception as e:
        print(f"画像比較エラー: {e}")
        return False


def test_frame_overlap_problem():
    """フレーム重複問題のテスト"""
    print("🔍 フレーム重複問題の確認テスト開始")
    
    # テスト用ディレクトリ
    samples_dir = Path("samples")
    test_dir = Path("tests/frame_test")
    test_dir.mkdir(exist_ok=True)
    
    # テスト用動画ファイル
    video1 = str(samples_dir / "ball_bokeh_02_slyblue.mp4")
    video2 = str(samples_dir / "13523522_1920_1080_60fps.mp4")
    
    if not Path(video1).exists() or not Path(video2).exists():
        print("❌ テスト用動画ファイルが見つかりません")
        return False
    
    # 一時ディレクトリ作成
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # クロスフェード動画生成（FADE_ONLYモード）
        crossfade_video = str(test_dir / "test_frame_overlap.mp4")
        print(f"クロスフェード動画生成: {crossfade_video}")
        
        try:
            result = create_crossfade_video(
                video1, video2,
                fade_duration=1.0,
                output_path=crossfade_video,
                effect=CrossfadeEffect.FADE,
                output_mode=CrossfadeOutputMode.FADE_ONLY
            )
            print(f"生成成功: {result['actual_duration']:.2f}秒")
            
        except Exception as e:
            print(f"❌ クロスフェード動画生成失敗: {e}")
            return False
        
        # フレーム抽出
        frames = {
            "video1_last": str(temp_path / "video1_last.png"),
            "video2_first": str(temp_path / "video2_first.png"),
            "crossfade_first": str(temp_path / "crossfade_first.png"),
            "crossfade_last": str(temp_path / "crossfade_last.png")
        }
        
        print("フレーム抽出中...")
        
        # 各フレームを抽出
        extractions = [
            (video1, "last", frames["video1_last"]),
            (video2, "first", frames["video2_first"]),
            (crossfade_video, "first", frames["crossfade_first"]),
            (crossfade_video, "last", frames["crossfade_last"])
        ]
        
        for video_path, position, output_path in extractions:
            if not extract_frame(video_path, position, output_path):
                print(f"❌ フレーム抽出失敗: {output_path}")
                return False
            print(f"  ✅ {Path(output_path).name} 抽出成功")
        
        # フレーム重複チェック
        print("\nフレーム重複チェック...")
        
        # 1. クロスフェード動画の最初のフレーム vs 動画1の最後のフレーム
        is_first_duplicate = compare_images(frames["crossfade_first"], frames["video1_last"])
        print(f"  最初のフレーム重複: {'あり' if is_first_duplicate else 'なし'}")
        
        # 2. クロスフェード動画の最後のフレーム vs 動画2の最初のフレーム  
        is_last_duplicate = compare_images(frames["crossfade_last"], frames["video2_first"])
        print(f"  最後のフレーム重複: {'あり' if is_last_duplicate else 'なし'}")
        
        # 結果判定
        has_problem = is_first_duplicate or is_last_duplicate
        
        if has_problem:
            print("⚠️  フレーム重複問題を確認しました")
            print("   修正が必要です")
        else:
            print("✅ フレーム重複問題は検出されませんでした")
        
        # フレームファイルを保存（デバッグ用）
        for name, path in frames.items():
            dest = test_dir / f"{name}.png"
            if Path(path).exists():
                import shutil
                shutil.copy2(path, dest)
                print(f"  保存: {dest}")
        
        return has_problem


def main():
    """メイン関数"""
    print("🧪 フレーム重複問題確認テスト")
    
    # 前提条件チェック
    required_tools = ["ffmpeg"]  # ImageMagickは任意
    for tool in required_tools:
        try:
            subprocess.run([tool, "-version"], capture_output=True)
        except FileNotFoundError:
            print(f"❌ 必要なツールが見つかりません: {tool}")
            return 1
    
    # テスト実行
    has_problem = test_frame_overlap_problem()
    
    if has_problem:
        print("\n📋 修正推奨:")
        print("  - remove_overlap_framesパラメータの追加")
        print("  - フレーム精度調整の実装")
        return 1
    else:
        print("\n✅ 現在の実装に問題は検出されませんでした")
        return 0


if __name__ == "__main__":
    sys.exit(main())