#!/usr/bin/env python
"""
現実的なワークロードでのハードウェアアクセラレーション検証

より負荷の高い条件でテストし、実際の使用場面での効果を測定
"""

import subprocess
import time
import os
import tempfile
from pathlib import Path

def create_heavy_test_video(output_path: str, duration: int = 30, resolution: str = "3840x2160"):
    """負荷の高いテスト用動画を生成"""
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', f'testsrc=duration={duration}:size={resolution}:rate=60',
        '-f', 'lavfi', 
        '-i', f'sine=frequency=1000:duration={duration}',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '18',  # 高品質
        '-c:a', 'aac',
        '-pix_fmt', 'yuv420p',
        output_path
    ]
    print(f"重い測定用動画を生成中... ({resolution}, 60fps, {duration}秒)")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"動画生成エラー: {result.stderr}")
        return False
    return True

def benchmark_encoding(input_path: str, output_path: str, use_hwaccel: bool, 
                      bitrate: str = "15M", preset: str = "medium"):
    """詳細ベンチマーク実行"""
    if use_hwaccel:
        cmd = [
            'ffmpeg', '-y',
            '-hwaccel', 'videotoolbox',
            '-i', input_path,
            '-c:v', 'h264_videotoolbox',
            '-b:v', bitrate,
            '-profile:v', 'high',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-loglevel', 'info',
            output_path
        ]
        encoder_type = "VideoToolbox (HW)"
    else:
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-c:v', 'libx264',
            '-preset', preset,
            '-b:v', bitrate,
            '-profile:v', 'high',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-loglevel', 'info',
            output_path
        ]
        encoder_type = f"libx264 (SW, {preset})"
    
    print(f"\n{encoder_type} でエンコード中...")
    print(f"コマンド: {' '.join(cmd[:8])}...")
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    duration = end_time - start_time
    
    # 出力ファイルサイズ確認
    file_size = 0
    if os.path.exists(output_path) and result.returncode == 0:
        file_size = os.path.getsize(output_path)
    
    # ログからフレームレート情報抽出
    fps_info = "不明"
    lines = result.stderr.split('\n')
    for line in lines:
        if 'fps=' in line and 'speed=' in line:
            try:
                fps_part = line.split('fps=')[1].split()[0]
                speed_part = line.split('speed=')[1].split('x')[0]
                fps_info = f"{fps_part}fps (速度: {speed_part}x)"
            except:
                pass
    
    return {
        'encoder': encoder_type,
        'duration': duration,
        'returncode': result.returncode,
        'file_size': file_size,
        'fps_info': fps_info,
        'stderr': result.stderr,
        'success': result.returncode == 0
    }

def run_comprehensive_benchmark():
    """包括的ベンチマーク実行"""
    print("=== 現実的なワークロードでのハードウェアアクセラレーション検証 ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 複数の条件でテスト
        test_conditions = [
            {"resolution": "1920x1080", "duration": 20, "bitrate": "8M", "name": "1080p"},
            {"resolution": "2560x1440", "duration": 15, "bitrate": "12M", "name": "1440p"},
            {"resolution": "3840x2160", "duration": 10, "bitrate": "20M", "name": "4K"},
        ]
        
        results = []
        
        for condition in test_conditions:
            print(f"\n{'='*60}")
            print(f"テスト条件: {condition['name']} ({condition['resolution']}, {condition['duration']}秒)")
            print(f"{'='*60}")
            
            # テスト動画生成
            input_video = os.path.join(temp_dir, f"test_{condition['name']}.mp4")
            if not create_heavy_test_video(
                input_video, 
                duration=condition['duration'], 
                resolution=condition['resolution']
            ):
                continue
            
            # 各エンコーダーでテスト
            test_scenarios = [
                {"hw": True, "name": "hardware"},
                {"hw": False, "preset": "ultrafast", "name": "software_ultrafast"},
                {"hw": False, "preset": "medium", "name": "software_medium"},
                {"hw": False, "preset": "slow", "name": "software_slow"},
            ]
            
            condition_results = {"condition": condition['name']}
            
            for scenario in test_scenarios:
                output_video = os.path.join(temp_dir, f"output_{condition['name']}_{scenario['name']}.mp4")
                
                if scenario['hw']:
                    result = benchmark_encoding(input_video, output_video, True, condition['bitrate'])
                else:
                    result = benchmark_encoding(
                        input_video, output_video, False, 
                        condition['bitrate'], scenario.get('preset', 'medium')
                    )
                
                condition_results[scenario['name']] = result
                
                if result['success']:
                    print(f"{result['encoder']:25} | {result['duration']:6.2f}秒 | {result['file_size']/1024/1024:6.1f}MB | {result['fps_info']}")
                else:
                    print(f"{result['encoder']:25} | エラー")
            
            results.append(condition_results)
            
            # 速度比較計算と表示
            if ('hardware' in condition_results and 'software_medium' in condition_results and 
                condition_results['hardware']['success'] and condition_results['software_medium']['success']):
                
                hw_time = condition_results['hardware']['duration']
                sw_time = condition_results['software_medium']['duration']
                speedup = sw_time / hw_time
                
                print(f"\n📊 {condition['name']} 結果:")
                print(f"   ハードウェア: {hw_time:.2f}秒")
                print(f"   ソフトウェア: {sw_time:.2f}秒")
                print(f"   速度向上: {speedup:.2f}倍")
                
                if speedup > 1.5:
                    print("   ✅ 有意な改善")
                elif speedup > 1.2:
                    print("   ⚡ 中程度の改善")
                elif speedup > 1.05:
                    print("   📈 わずかな改善")
                else:
                    print("   ⚠️  改善なし/ソフトウェアの方が速い")
        
        print(f"\n{'='*60}")
        print("総合分析")
        print(f"{'='*60}")
        
        # 総合的な分析
        for result in results:
            condition_name = result['condition']
            if 'hardware' in result and 'software_medium' in result:
                hw = result['hardware']
                sw = result['software_medium']
                
                if hw['success'] and sw['success']:
                    speedup = sw['duration'] / hw['duration']
                    quality_ratio = hw['file_size'] / sw['file_size'] if sw['file_size'] > 0 else 1.0
                    
                    print(f"\n{condition_name}:")
                    print(f"  速度向上: {speedup:.2f}倍")
                    print(f"  ファイルサイズ比: {quality_ratio:.2f}")
                    print(f"  推奨: {'ハードウェア' if speedup > 1.2 else 'ソフトウェア'}")

if __name__ == "__main__":
    run_comprehensive_benchmark()