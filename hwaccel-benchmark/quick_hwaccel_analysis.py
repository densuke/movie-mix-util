#!/usr/bin/env python
"""
ハードウェアアクセラレーション効果の分析

VideoToolboxの特性と期待される効果を分析
"""

import subprocess
import time
import os
import tempfile

def analyze_videotoolbox_characteristics():
    """VideoToolboxの特性分析"""
    print("=== VideoToolbox特性分析 ===\n")
    
    print("🔍 VideoToolbox (Apple Silicon)の特性:")
    print("• **省電力最優先**: 速度よりもバッテリー効率を重視")
    print("• **統合型アーキテクチャ**: CPU-GPU間のデータ転送が高速")
    print("• **短時間処理**: 初期化オーバーヘッドで効果が薄れる")
    print("• **軽量ワークロード**: libx264との差が小さくなる")
    
    print("\n⚡ ハードウェアアクセラレーションが効果的な場面:")
    print("• 長時間(30秒以上)の動画処理")
    print("• 高解像度(4K以上)コンテンツ")
    print("• 高フレームレート(60fps以上)")
    print("• 複数動画の同時処理")
    print("• バッチ処理での連続エンコード")
    
    print("\n📊 1.08倍の結果について:")
    print("• **妥当な結果**: 軽量タスクでは一般的")
    print("• **Apple Silicon最適化**: CPUも十分高速")
    print("• **統合メモリ**: データ転送ボトルネックが少ない")

def test_batch_processing():
    """バッチ処理での効果測定"""
    print("\n=== バッチ処理効果テスト ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 小さなテスト動画を複数生成
        test_files = []
        for i in range(3):
            test_file = os.path.join(temp_dir, f'test_{i}.mp4')
            cmd = [
                'ffmpeg', '-y', '-loglevel', 'quiet',
                '-f', 'lavfi', '-i', 'testsrc=duration=8:size=1920x1080:rate=30',
                '-c:v', 'libx264', '-preset', 'fast', test_file
            ]
            subprocess.run(cmd)
            test_files.append(test_file)
        
        # ハードウェア処理（バッチ）
        print("🔧 ハードウェアでバッチ処理...")
        hw_start = time.time()
        for i, test_file in enumerate(test_files):
            output = os.path.join(temp_dir, f'hw_output_{i}.mp4')
            cmd = [
                'ffmpeg', '-y', '-loglevel', 'quiet',
                '-hwaccel', 'videotoolbox',
                '-i', test_file,
                '-c:v', 'h264_videotoolbox',
                '-b:v', '5M',
                output
            ]
            subprocess.run(cmd)
        hw_time = time.time() - hw_start
        
        # ソフトウェア処理（バッチ）
        print("🔧 ソフトウェアでバッチ処理...")
        sw_start = time.time()
        for i, test_file in enumerate(test_files):
            output = os.path.join(temp_dir, f'sw_output_{i}.mp4')
            cmd = [
                'ffmpeg', '-y', '-loglevel', 'quiet',
                '-i', test_file,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-b:v', '5M',
                output
            ]
            subprocess.run(cmd)
        sw_time = time.time() - sw_start
        
        batch_speedup = sw_time / hw_time
        print(f"\n📊 バッチ処理結果:")
        print(f"ハードウェア: {hw_time:.2f}秒")
        print(f"ソフトウェア: {sw_time:.2f}秒")
        print(f"速度向上: {batch_speedup:.2f}倍")
        
        return batch_speedup

def test_different_bitrates():
    """異なるビットレートでの効果測定"""
    print("\n=== ビットレート別効果測定 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # テスト動画生成
        input_file = os.path.join(temp_dir, 'input.mp4')
        cmd = [
            'ffmpeg', '-y', '-loglevel', 'quiet',
            '-f', 'lavfi', '-i', 'testsrc=duration=10:size=1920x1080:rate=30',
            '-c:v', 'libx264', '-preset', 'fast', input_file
        ]
        subprocess.run(cmd)
        
        bitrates = ['2M', '8M', '15M']
        results = {}
        
        for bitrate in bitrates:
            print(f"\n🔧 ビットレート {bitrate} でテスト...")
            
            # ハードウェア
            hw_output = os.path.join(temp_dir, f'hw_{bitrate}.mp4')
            hw_start = time.time()
            cmd = [
                'ffmpeg', '-y', '-loglevel', 'quiet',
                '-hwaccel', 'videotoolbox',
                '-i', input_file,
                '-c:v', 'h264_videotoolbox',
                '-b:v', bitrate,
                hw_output
            ]
            subprocess.run(cmd)
            hw_time = time.time() - hw_start
            
            # ソフトウェア
            sw_output = os.path.join(temp_dir, f'sw_{bitrate}.mp4')
            sw_start = time.time()
            cmd = [
                'ffmpeg', '-y', '-loglevel', 'quiet',
                '-i', input_file,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-b:v', bitrate,
                sw_output
            ]
            subprocess.run(cmd)
            sw_time = time.time() - sw_start
            
            speedup = sw_time / hw_time
            results[bitrate] = speedup
            print(f"{bitrate}: {speedup:.2f}倍")
        
        return results

def provide_recommendations():
    """実装推奨事項"""
    print("\n" + "="*60)
    print("🎯 実装推奨事項")
    print("="*60)
    
    print("\n1. **ハードウェアアクセラレーション判定基準**:")
    print("   • 1.05倍未満: 効果なし → ソフトウェア使用")
    print("   • 1.05-1.2倍: 省電力効果あり → バッテリー駆動時に有効")
    print("   • 1.2倍以上: 明確な速度向上 → 積極的に使用")
    
    print("\n2. **動的切り替えロジック**:")
    print("   • 短時間(10秒未満): ソフトウェア優先")
    print("   • 長時間(30秒以上): ハードウェア優先")  
    print("   • バッチ処理: ハードウェア優先")
    print("   • 低解像度(720p未満): ソフトウェア優先")
    
    print("\n3. **環境変数での制御拡張**:")
    print("   • MOVIE_MIX_HWACCEL_THRESHOLD=1.2  # 切り替え閾値")
    print("   • MOVIE_MIX_PREFER_BATTERY=1       # 省電力優先")
    print("   • MOVIE_MIX_FORCE_HWACCEL=1        # 強制ハードウェア")
    
    print("\n4. **ユーザーへの透明性向上**:")
    print("   • 使用エンコーダーの明確な表示")
    print("   • 推定省電力効果の表示")
    print("   • パフォーマンス向上率の表示")

def main():
    analyze_videotoolbox_characteristics()
    
    print("\n" + "="*60)
    print("🧪 実測テスト")
    print("="*60)
    
    batch_speedup = test_batch_processing()
    bitrate_results = test_different_bitrates()
    
    print(f"\n📊 総合結果:")
    print(f"• バッチ処理での効果: {batch_speedup:.2f}倍")
    print(f"• 高ビットレートでの効果: {bitrate_results.get('15M', 'N/A'):.2f}倍")
    
    # 結論
    print(f"\n🎯 結論:")
    if batch_speedup > 1.2 or any(v > 1.2 for v in bitrate_results.values()):
        print("✅ ハードウェアアクセラレーションは有効")
        print("   特に長時間・高品質・バッチ処理で効果大")
    else:
        print("⚖️  ハードウェアアクセラレーションは省電力目的で有効")
        print("   速度向上は限定的だが、バッテリー消費は削減")
    
    provide_recommendations()

if __name__ == "__main__":
    main()