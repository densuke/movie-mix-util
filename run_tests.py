#!/usr/bin/env python
"""テスト実行スクリプト

様々なレベルのテストを実行するためのスクリプト
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """コマンドを実行して結果を表示"""
    print(f"\n=== {description} ===")
    print(f"実行中: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description}成功")
        else:
            print(f"❌ {description}失敗 (終了コード: {result.returncode})")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ {description}でエラーが発生: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="動画処理ライブラリのテスト実行")
    
    parser.add_argument("--quick", action="store_true", 
                       help="高速テストのみ実行（FFmpeg不要なテスト）")
    parser.add_argument("--unit", action="store_true",
                       help="単体テストのみ実行")
    parser.add_argument("--integration", action="store_true",
                       help="統合テストのみ実行")
    parser.add_argument("--all", action="store_true",
                       help="全てのテスト実行")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="詳細出力")
    parser.add_argument("--file", type=str,
                       help="特定のテストファイルのみ実行")
    
    args = parser.parse_args()
    
    # pytest基本オプション
    pytest_cmd = ["uv", "run", "pytest"]
    
    if args.verbose:
        pytest_cmd.extend(["-v", "-s"])
    
    # テスト対象の選択
    if args.file:
        test_target = f"tests/{args.file}"
        description = f"テストファイル {args.file}"
    elif args.quick:
        pytest_cmd.extend(["-m", "not slow and not integration"])
        test_target = "tests/"
        description = "クイックテスト"
    elif args.unit:
        pytest_cmd.extend(["-m", "not integration"])
        test_target = "tests/"
        description = "単体テスト"
    elif args.integration:
        pytest_cmd.extend(["-m", "integration"])
        test_target = "tests/"
        description = "統合テスト"
    elif args.all:
        test_target = "tests/"
        description = "全テスト"
    else:
        # デフォルト: 高速テスト
        pytest_cmd.extend(["-m", "not slow and not integration"])
        test_target = "tests/"
        description = "デフォルトテスト（高速テストのみ）"
    
    pytest_cmd.append(test_target)
    
    print("🎬 動画処理ライブラリ テスト実行")
    print(f"対象: {description}")
    
    # FFmpegチェック（統合テストの場合）
    if args.integration or args.all:
        print("\n📋 FFmpegの可用性チェック...")
        ffmpeg_check = run_command(["ffmpeg", "-version"], "FFmpegバージョンチェック")
        if not ffmpeg_check:
            print("⚠️ FFmpegが見つかりません。統合テストをスキップする場合があります。")
    
    # samplesディレクトリチェック
    samples_dir = Path("samples")
    if not samples_dir.exists():
        print("❌ samplesディレクトリが見つかりません")
        print("テストに必要なサンプルファイルを配置してください")
        return 1
    
    sample_files = list(samples_dir.glob("*"))
    print(f"\n📁 サンプルファイル: {len(sample_files)}個")
    for file in sample_files:
        if file.is_file():
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"  - {file.name}: {size_mb:.1f}MB")
    
    # テスト実行
    success = run_command(pytest_cmd, f"{description}実行")
    
    if success:
        print(f"\n✅ {description}が正常に完了しました")
        return 0
    else:
        print(f"\n❌ {description}で失敗がありました")
        return 1


if __name__ == "__main__":
    sys.exit(main())