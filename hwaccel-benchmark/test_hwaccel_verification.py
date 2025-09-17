#!/usr/bin/env python
"""
ハードウェアアクセラレーション検証テストスクリプト

FFmpegでハードウェアアクセラレーションが実際に使用されているかを検証する
"""

import subprocess
import time
import os
import tempfile
from pathlib import Path

def create_test_video(output_path: str, duration: int = 5):
    """テスト用動画を生成"""
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', f'testsrc=duration={duration}:size=1920x1080:rate=30',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        output_path
    ]
    subprocess.run(cmd, capture_output=True)

def test_encoding_with_hwaccel(input_path: str, output_path: str, use_hwaccel: bool = True):
    """ハードウェアアクセラレーションありなしでエンコードテスト"""
    if use_hwaccel:
        cmd = [
            'ffmpeg', '-y',
            '-hwaccel', 'videotoolbox',
            '-i', input_path,
            '-c:v', 'h264_videotoolbox',
            '-b:v', '5M',
            '-loglevel', 'info',
            output_path
        ]
    else:
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-c:v', 'libx264',
            '-b:v', '5M',
            '-loglevel', 'info',
            output_path
        ]
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    return {
        'duration': end_time - start_time,
        'returncode': result.returncode,
        'stderr': result.stderr,
        'cmd': ' '.join(cmd)
    }

def analyze_ffmpeg_log(log_text: str):
    """FFmpegのログを解析してハードウェアアクセラレーション使用状況を確認"""
    indicators = {
        'videotoolbox_used': False,
        'hardware_encoder': False,
        'software_encoder': False,
        'hwaccel_init': False
    }
    
    lines = log_text.split('\n')
    for line in lines:
        line_lower = line.lower()
        if 'videotoolbox' in line_lower:
            indicators['videotoolbox_used'] = True
        if 'h264_videotoolbox' in line_lower:
            indicators['hardware_encoder'] = True
        if 'libx264' in line_lower:
            indicators['software_encoder'] = True
        if 'hwaccel' in line_lower and ('init' in line_lower or 'created' in line_lower):
            indicators['hwaccel_init'] = True
    
    return indicators

def main():
    print("=== ハードウェアアクセラレーション検証テスト ===\n")
    
    # テスト用ディレクトリ作成
    with tempfile.TemporaryDirectory() as temp_dir:
        input_video = os.path.join(temp_dir, 'test_input.mp4')
        hw_output = os.path.join(temp_dir, 'test_hw_output.mp4')
        sw_output = os.path.join(temp_dir, 'test_sw_output.mp4')
        
        print("1. テスト用動画を生成中...")
        create_test_video(input_video, duration=10)
        print(f"テスト動画生成完了: {input_video}")
        
        print("\n2. ハードウェアアクセラレーション有効でエンコードテスト...")
        hw_result = test_encoding_with_hwaccel(input_video, hw_output, use_hwaccel=True)
        
        print("\n3. ソフトウェアエンコードでエンコードテスト...")
        sw_result = test_encoding_with_hwaccel(input_video, sw_output, use_hwaccel=False)
        
        print("\n=== 結果分析 ===")
        print(f"ハードウェアエンコード時間: {hw_result['duration']:.2f}秒")
        print(f"ソフトウェアエンコード時間: {sw_result['duration']:.2f}秒")
        print(f"速度向上: {sw_result['duration'] / hw_result['duration']:.2f}倍")
        
        print("\n=== ハードウェアアクセラレーションログ分析 ===")
        hw_indicators = analyze_ffmpeg_log(hw_result['stderr'])
        for key, value in hw_indicators.items():
            print(f"{key}: {value}")
        
        print("\n=== FFmpegログ (ハードウェア) ===")
        print(hw_result['stderr'][-1000:])  # 最後の1000文字を表示
        
        print("\n=== ファイルサイズ比較 ===")
        if os.path.exists(hw_output):
            hw_size = os.path.getsize(hw_output)
            print(f"ハードウェアエンコード: {hw_size} bytes")
        if os.path.exists(sw_output):
            sw_size = os.path.getsize(sw_output)
            print(f"ソフトウェアエンコード: {sw_size} bytes")

if __name__ == "__main__":
    main()