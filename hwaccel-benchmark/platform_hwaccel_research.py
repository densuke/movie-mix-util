#!/usr/bin/env python
"""
プラットフォーム別ハードウェアアクセラレーション調査スクリプト

各プラットフォームでのハードウェアアクセラレーション対応状況を調査する
"""

import subprocess
import platform
import sys
from typing import Dict, List, Optional, Tuple

class HardwareAccelResearcher:
    """ハードウェアアクセラレーション調査クラス"""
    
    def __init__(self):
        self.system = platform.system()
        self.machine = platform.machine()
        self.available_encoders = []
        self.available_hwaccels = []
        
    def detect_ffmpeg_capabilities(self) -> Dict[str, List[str]]:
        """FFmpegの機能を検出"""
        capabilities = {
            'encoders': [],
            'hwaccels': [],
            'decoders': []
        }
        
        # エンコーダー検出
        try:
            result = subprocess.run(['ffmpeg', '-encoders'], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if any(codec in line for codec in ['h264', 'h265', 'hevc', 'av1']):
                        for encoder in ['libx264', 'h264_videotoolbox', 'h264_nvenc', 
                                      'h264_qsv', 'h264_vaapi', 'h264_amf',
                                      'libx265', 'hevc_videotoolbox', 'hevc_nvenc',
                                      'hevc_qsv', 'hevc_vaapi', 'hevc_amf']:
                            if encoder in line:
                                capabilities['encoders'].append(encoder)
        except Exception as e:
            print(f"エンコーダー検出エラー: {e}")
        
        # ハードウェアアクセラレーション検出
        try:
            result = subprocess.run(['ffmpeg', '-hwaccels'], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and line not in ['Hardware acceleration methods:', '']:
                        capabilities['hwaccels'].append(line)
        except Exception as e:
            print(f"ハードウェアアクセラレーション検出エラー: {e}")
        
        return capabilities
    
    def get_platform_specific_recommendations(self) -> Dict[str, any]:
        """プラットフォーム固有の推奨設定を取得"""
        recommendations = {
            'primary_encoder': 'libx264',
            'primary_hwaccel': None,
            'fallback_options': [],
            'performance_tips': [],
            'platform_notes': []
        }
        
        if self.system == 'Darwin':  # macOS
            recommendations.update(self._get_macos_recommendations())
        elif self.system == 'Windows':
            recommendations.update(self._get_windows_recommendations())
        elif self.system == 'Linux':
            recommendations.update(self._get_linux_recommendations())
        
        return recommendations
    
    def _get_macos_recommendations(self) -> Dict[str, any]:
        """macOS向け推奨設定"""
        return {
            'primary_encoder': 'h264_videotoolbox',
            'primary_hwaccel': 'videotoolbox',
            'fallback_options': [
                ('libx264', None, 'ソフトウェアフォールバック')
            ],
            'performance_tips': [
                'VideoToolboxはApple Siliconで最適化されている',
                'プロファイル設定（baseline, main, high）でエンコード品質調整可能',
                'リアルタイム設定（-realtime 1）で低遅延エンコード可能',
                'macOS 10.13以降でHEVC/H.265対応'
            ],
            'platform_notes': [
                f'アーキテクチャ: {self.machine}',
                'VideoToolboxはGPUとMedia Engineを活用',
                'Metal Performance Shadersとの連携可能'
            ]
        }
    
    def _get_windows_recommendations(self) -> Dict[str, any]:
        """Windows向け推奨設定"""
        return {
            'primary_encoder': 'h264_nvenc',  # NVIDIA優先
            'primary_hwaccel': 'cuda',
            'fallback_options': [
                ('h264_qsv', 'qsv', 'Intel Quick Sync Video'),
                ('h264_amf', 'd3d11va', 'AMD AMF'),
                ('libx264', None, 'ソフトウェアフォールバック')
            ],
            'performance_tips': [
                'NVIDIA: GeForce GTX 600シリーズ以降でNVENC対応',
                'Intel: 第2世代Core以降でQuick Sync Video対応',
                'AMD: GCN 1.0以降でAMF対応',
                'DirectX 11/12との連携で更なる最適化可能'
            ],
            'platform_notes': [
                'GPU固有の最適化設定が重要',
                'Windows Media Foundationとの統合',
                'マルチGPU環境での負荷分散考慮'
            ]
        }
    
    def _get_linux_recommendations(self) -> Dict[str, any]:
        """Linux向け推奨設定"""
        return {
            'primary_encoder': 'h264_vaapi',  # VAAPI優先
            'primary_hwaccel': 'vaapi',
            'fallback_options': [
                ('h264_nvenc', 'cuda', 'NVIDIA NVENC'),
                ('h264_qsv', 'qsv', 'Intel Quick Sync Video'),
                ('libx264', None, 'ソフトウェアフォールバック')
            ],
            'performance_tips': [
                'VAAPI: Intel/AMD統合GPUで幅広く対応',
                'NVIDIA: 専用ドライバとCUDAランタイム必要',
                'カーネルモジュールとユーザースペースドライバの整合性重要',
                'DRM/KMSとの連携でゼロコピー操作可能'
            ],
            'platform_notes': [
                'ディストリビューション固有のパッケージ管理',
                'Mesa/libvaライブラリバージョン依存',
                'コンテナ環境での特別な権限設定必要'
            ]
        }
    
    def detect_gpu_capabilities(self) -> Dict[str, any]:
        """GPU機能の検出"""
        gpu_info = {
            'detected_gpus': [],
            'capabilities': {}
        }
        
        if self.system == 'Darwin':
            gpu_info.update(self._detect_macos_gpu())
        elif self.system == 'Windows':
            gpu_info.update(self._detect_windows_gpu())
        elif self.system == 'Linux':
            gpu_info.update(self._detect_linux_gpu())
        
        return gpu_info
    
    def _detect_macos_gpu(self) -> Dict[str, any]:
        """macOS GPU検出"""
        try:
            result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                  capture_output=True, text=True, check=False)
            gpu_info = {'detected_gpus': [], 'capabilities': {}}
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                current_gpu = None
                for line in lines:
                    line = line.strip()
                    if 'Chipset Model:' in line or 'Graphics:' in line:
                        current_gpu = line.split(':')[1].strip()
                        gpu_info['detected_gpus'].append(current_gpu)
                    elif 'Metal:' in line and current_gpu:
                        gpu_info['capabilities'][current_gpu] = {
                            'metal_support': 'Supported' in line,
                            'videotoolbox_likely': True
                        }
            
            return gpu_info
        except Exception as e:
            return {'detected_gpus': ['検出失敗'], 'capabilities': {}, 'error': str(e)}
    
    def _detect_windows_gpu(self) -> Dict[str, any]:
        """Windows GPU検出（簡易版）"""
        # 実際の実装では wmi や DirectX診断ツールを使用
        return {
            'detected_gpus': ['Windows GPU検出は実装予定'],
            'capabilities': {},
            'note': 'dxdiag /t output.txt での詳細情報取得を推奨'
        }
    
    def _detect_linux_gpu(self) -> Dict[str, any]:
        """Linux GPU検出"""
        gpu_info = {'detected_gpus': [], 'capabilities': {}}
        
        try:
            # lspci でGPU検出
            result = subprocess.run(['lspci', '-v'], 
                                  capture_output=True, text=True, check=False)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'VGA' in line or 'Display' in line or '3D' in line:
                        gpu_info['detected_gpus'].append(line.strip())
            
            # VAAPI機能確認
            vaapi_result = subprocess.run(['vainfo'], 
                                        capture_output=True, text=True, check=False)
            if vaapi_result.returncode == 0:
                gpu_info['capabilities']['vaapi'] = 'available'
            
        except Exception as e:
            gpu_info['error'] = str(e)
        
        return gpu_info
    
    def generate_report(self) -> str:
        """調査結果レポート生成"""
        capabilities = self.detect_ffmpeg_capabilities()
        recommendations = self.get_platform_specific_recommendations()
        gpu_info = self.detect_gpu_capabilities()
        
        report = f"""
=== ハードウェアアクセラレーション調査レポート ===
プラットフォーム: {self.system} ({self.machine})

=== FFmpeg機能検出結果 ===
利用可能なエンコーダー: {', '.join(capabilities['encoders']) or 'なし'}
利用可能なハードウェアアクセラレーション: {', '.join(capabilities['hwaccels']) or 'なし'}

=== 推奨設定 ===
主エンコーダー: {recommendations['primary_encoder']}
主ハードウェアアクセラレーション: {recommendations['primary_hwaccel'] or 'なし'}

=== フォールバックオプション ==="""
        
        for i, (encoder, hwaccel, note) in enumerate(recommendations['fallback_options'], 1):
            report += f"\n{i}. {encoder} (hwaccel: {hwaccel or 'なし'}) - {note}"
        
        report += f"""

=== パフォーマンスヒント ==="""
        for tip in recommendations['performance_tips']:
            report += f"\n• {tip}"
        
        report += f"""

=== プラットフォーム固有の注意点 ==="""
        for note in recommendations['platform_notes']:
            report += f"\n• {note}"
        
        report += f"""

=== GPU検出結果 ===
検出されたGPU: {', '.join(gpu_info['detected_gpus']) or 'なし'}
機能: {gpu_info['capabilities']}
"""
        
        return report

def main():
    researcher = HardwareAccelResearcher()
    report = researcher.generate_report()
    print(report)
    
    # レポートをファイルに保存
    with open('hwaccel_research_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nレポートを hwaccel_research_report.txt に保存しました。")

if __name__ == "__main__":
    main()