# Examples - movie-mix-util

Practical examples and workflows for the movie-mix-util video processing library.

## Table of Contents

1. [Basic Operations](#basic-operations)
2. [Advanced Workflows](#advanced-workflows) 
3. [Professional Effects](#professional-effects)
4. [Batch Processing](#batch-processing)
5. [Error Handling](#error-handling)
6. [Performance Optimization](#performance-optimization)

## Basic Operations

### Simple Video Concatenation

```python
from movie_mix_util import quick_concatenate

# Combine three videos with 1-second crossfades
result = quick_concatenate(
    video_paths=["intro.mp4", "main_content.mp4", "outro.mp4"],
    output_path="complete_video.mp4",
    crossfade_duration=1.0
)

print(f"Created video: {result.duration:.1f} seconds")
print(f"File size: {result.size_mb:.1f} MB")
```

### Image Overlay on Video

```python
from movie_mix_util import quick_mix

# Add a logo to a background video
result = quick_mix(
    background_video="background.mp4",
    overlay_image="company_logo.png", 
    output_path="branded_video.mp4",
    duration=60  # 1-minute output
)

print(f"Created branded video: {result.path}")
```

### Standalone Crossfade Effect

```python
from movie_mix_util import quick_crossfade, CrossfadeEffect

# Create a smooth transition between two scenes
result = quick_crossfade(
    video1_path="scene1.mp4",
    video2_path="scene2.mp4",
    fade_duration=2.5,
    output_path="scene_transition.mp4",
    effect=CrossfadeEffect.DISSOLVE
)
```

## Advanced Workflows

### Custom Video Sequence

```python
from movie_mix_util import VideoProcessor, VideoSequenceBuilder, TransitionMode

# Create a processor with custom settings
processor = VideoProcessor(
    default_fps=60,
    default_size=(3840, 2160)  # 4K resolution
)

# Build a complex sequence
sequence = (VideoSequenceBuilder()
    .add_video("title_card.mp4")
    .add_crossfade(1.0, TransitionMode.CROSSFADE_NO_INCREASE)
    .add_video("chapter1.mp4") 
    .add_crossfade(2.0, TransitionMode.CROSSFADE_INCREASE)
    .add_video("chapter2.mp4")
    .add_crossfade(1.5, TransitionMode.CROSSFADE_NO_INCREASE) 
    .add_video("credits.mp4")
    .build())

# Process the sequence
result = processor.concatenate_videos(sequence, "final_movie.mp4")
print(f"Movie duration: {result.duration / 60:.1f} minutes")
```

### Multi-Format Processing

```python
from movie_mix_util import VideoProcessor, VideoInfo
import os
from pathlib import Path

def process_video_collection(input_dir: str, output_dir: str):
    """Process all videos in a directory with consistent settings."""
    
    processor = VideoProcessor()
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Find all video files
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv']
    video_files = [
        f for f in input_path.iterdir() 
        if f.suffix.lower() in video_extensions
    ]
    
    results = []
    for video_file in sorted(video_files):
        output_file = output_path / f"processed_{video_file.stem}.mp4"
        
        # Add watermark to each video
        result = processor.mix_video_with_image(
            video_path=str(video_file),
            image_path="watermark.png", 
            output_path=str(output_file),
            duration=30
        )
        results.append(result)
        print(f"Processed: {video_file.name} -> {output_file.name}")
    
    return results

# Use the function
results = process_video_collection("input_videos/", "output_videos/")
```

## Professional Effects

### Deferred Execution Crossfade Examples

This section demonstrates crossfade effects using the deferred execution pattern, allowing for efficient FFmpeg command execution.

#### Overlay Crossfade (Shortened Duration)

This example shows how to create a crossfade effect where the total video duration is shortened by the fade duration.

```python
#!/usr/bin/env python
from deferred_concat import movie
from advanced_video_concatenator import CrossfadeEffect, TransitionMode

def main():
    """
    DeferredConcatを使用して、2つのビデオをオーバーレイでクロスフェードするサンプル
    """
    base = movie("samples/sample_A.mp4")
    add = "samples/sample_B.mp4"

    (
        base
        .append(
            add,
            duration=1,
            effect=CrossfadeEffect.FADE,
            mode=TransitionMode.CROSSFADE_NO_INCREASE
        )
        .execute("output/overlay_crossfade.mp4")
    )

if __name__ == "__main__":
    main()
```

#### Increase Crossfade (Increased Duration)

This example demonstrates a crossfade effect where the total video duration is increased by the fade duration.

```python
#!/usr/bin/env python
from deferred_concat import movie
from advanced_video_concatenator import CrossfadeEffect, TransitionMode

def main():
    """
    DeferredConcatを使用して、2つのビデオをincreaseモードでクロスフェードするサンプル
    """
    base = movie("samples/sample_A.mp4")
    add = "samples/sample_B.mp4"

    (
        base
        .append(
            add,
            duration=1,
            effect=CrossfadeEffect.FADE,
            mode=TransitionMode.CROSSFADE_INCREASE
        )
        .execute("output/increase_crossfade.mp4")
    )

if __name__ == "__main__":
    main()
```

### Advanced Crossfade Gallery

```python
from movie_mix_util import create_crossfade_video, CrossfadeEffect, CrossfadeOutputMode

# Dictionary of professional effects
effects_showcase = {
    "smooth_fade": CrossfadeEffect.FADE,
    "quick_dissolve": CrossfadeEffect.DISSOLVE,
    "dramatic_wipe": CrossfadeEffect.WIPE_LEFT,
    "dynamic_slide": CrossfadeEffect.SLIDE_RIGHT,
    "artistic_circle": CrossfadeEffect.CIRCLE_CROP,
    "geometric_rect": CrossfadeEffect.RECT_CROP,
    "diagonal_wipe": CrossfadeEffect.WIPE_UP_LEFT,
    "radial_transition": CrossfadeEffect.RADIAL
}

def create_effects_demo(video1: str, video2: str, output_dir: str):
    """Create a demo of all crossfade effects."""
    
    for effect_name, effect_type in effects_showcase.items():
        output_path = f"{output_dir}/demo_{effect_name}.mp4"
        
        result = create_crossfade_video(
            video1_path=video1,
            video2_path=video2,
            fade_duration=3.0,
            output_path=output_path,
            effect=effect_type,
            output_mode=CrossfadeOutputMode.FULL_SEQUENCE
        )
        
        print(f"Created {effect_name}: {result['actual_duration']:.1f}s")

# Generate effects demo
create_effects_demo("sample1.mp4", "sample2.mp4", "effects_demo/")
```

### Custom Duration Outputs

```python
from movie_mix_util import create_crossfade_video, CrossfadeOutputMode

# Create exactly 10-second promotional clips
def create_promo_clip(video1: str, video2: str, output_path: str):
    """Create a 10-second promotional clip with crossfade."""
    
    result = create_crossfade_video(
        video1_path=video1,
        video2_path=video2, 
        fade_duration=2.0,
        output_path=output_path,
        output_mode=CrossfadeOutputMode.CUSTOM,
        custom_duration=10.0
    )
    
    return result

# Create multiple promo clips
promo_pairs = [
    ("product1.mp4", "product2.mp4", "promo_tech.mp4"),
    ("lifestyle1.mp4", "lifestyle2.mp4", "promo_lifestyle.mp4"),
    ("brand1.mp4", "brand2.mp4", "promo_brand.mp4")
]

for video1, video2, output in promo_pairs:
    result = create_promo_clip(video1, video2, output)
    print(f"Created promo: {output}")
```

## Batch Processing

### Automated Video Pipeline

```python
from movie_mix_util import VideoProcessor, VideoSequenceBuilder, TransitionMode
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

class VideoPipeline:
    """Automated video processing pipeline."""
    
    def __init__(self, config_file: str):
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        self.processor = VideoProcessor()
    
    def process_batch(self, batch_config: dict) -> dict:
        """Process a single batch according to configuration."""
        
        videos = batch_config['videos']
        transitions = batch_config.get('transitions', [])
        output_path = batch_config['output']
        
        # Build sequence
        builder = VideoSequenceBuilder()
        for i, video in enumerate(videos):
            builder.add_video(video)
            
            # Add transition if not the last video
            if i < len(videos) - 1:
                transition_config = transitions[i] if i < len(transitions) else {}
                duration = transition_config.get('duration', 1.0)
                mode_str = transition_config.get('mode', 'increase')
                mode = TransitionMode.CROSSFADE_INCREASE if mode_str == 'increase' else TransitionMode.CROSSFADE_NO_INCREASE
                builder.add_crossfade(duration, mode)
        
        # Process
        sequence = builder.build()
        result = self.processor.concatenate_videos(sequence, output_path)
        
        return {
            'batch': batch_config['name'],
            'output': output_path,
            'duration': result.duration,
            'size_mb': result.size_mb
        }
    
    def run_pipeline(self) -> list[dict]:
        """Run the complete pipeline."""
        results = []
        
        # Process batches in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for batch in self.config['batches']:
                future = executor.submit(self.process_batch, batch)
                futures.append(future)
            
            for future in futures:
                result = future.result()
                results.append(result)
                print(f"Completed batch: {result['batch']}")
        
        return results

# Example configuration file (pipeline_config.json)
config_example = {
    "batches": [
        {
            "name": "episode1",
            "videos": ["intro.mp4", "content1.mp4", "outro.mp4"],
            "transitions": [
                {"duration": 1.0, "mode": "no_increase"},
                {"duration": 2.0, "mode": "increase"}
            ],
            "output": "episode1_final.mp4"
        },
        {
            "name": "episode2", 
            "videos": ["intro.mp4", "content2.mp4", "outro.mp4"],
            "output": "episode2_final.mp4"
        }
    ]
}

# Save config and run pipeline
with open("pipeline_config.json", "w") as f:
    json.dump(config_example, f, indent=2)

pipeline = VideoPipeline("pipeline_config.json")
results = pipeline.run_pipeline()
```

### Social Media Optimization

```python
from movie_mix_util import VideoProcessor, quick_mix
from pathlib import Path

class SocialMediaProcessor:
    """Optimize videos for different social media platforms."""
    
    PLATFORM_SPECS = {
        'instagram_story': {'size': (1080, 1920), 'duration': 15},
        'instagram_post': {'size': (1080, 1080), 'duration': 60},
        'youtube_short': {'size': (1080, 1920), 'duration': 60},
        'tiktok': {'size': (1080, 1920), 'duration': 30},
        'twitter': {'size': (1280, 720), 'duration': 140}
    }
    
    def __init__(self):
        self.processor = VideoProcessor()
    
    def optimize_for_platform(self, video_path: str, platform: str, output_dir: str) -> dict:
        """Optimize a video for a specific social media platform."""
        
        if platform not in self.PLATFORM_SPECS:
            raise ValueError(f"Unknown platform: {platform}")
        
        specs = self.PLATFORM_SPECS[platform]
        output_path = Path(output_dir) / f"{Path(video_path).stem}_{platform}.mp4"
        
        # Create processor with platform-specific settings
        self.processor.default_size = specs['size']
        
        # For square/vertical formats, add background
        if specs['size'][0] <= specs['size'][1]:  # Square or vertical
            result = quick_mix(
                background_video=video_path,
                overlay_image="brand_background.png",
                output_path=str(output_path),
                duration=specs['duration']
            )
        else:  # Horizontal
            # Just trim to required duration
            result = self.processor.trim_video(
                video_path, 
                str(output_path),
                duration=specs['duration']
            )
        
        return {
            'platform': platform,
            'output_path': str(output_path),
            'duration': result.duration,
            'resolution': f"{result.width}x{result.height}"
        }
    
    def create_multi_platform_content(self, source_video: str, output_dir: str):
        """Create optimized versions for all platforms."""
        results = {}
        
        for platform in self.PLATFORM_SPECS:
            try:
                result = self.optimize_for_platform(source_video, platform, output_dir)
                results[platform] = result
                print(f"✅ {platform}: {result['resolution']} @ {result['duration']}s")
            except Exception as e:
                print(f"❌ {platform}: Failed - {e}")
                results[platform] = {'error': str(e)}
        
        return results

# Usage
social_processor = SocialMediaProcessor()
results = social_processor.create_multi_platform_content(
    "master_content.mp4", 
    "social_outputs/"
)
```

## Error Handling

### Robust Processing with Fallbacks

```python
from movie_mix_util import VideoProcessingError, quick_concatenate, quick_mix
import logging
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def robust_video_processing(
    videos: list[str], 
    output_path: str,
    fallback_strategy: str = "skip_failed"
) -> Optional[dict]:
    """
    Process videos with robust error handling and fallback strategies.
    
    Args:
        videos: List of input video paths
        output_path: Output file path
        fallback_strategy: "skip_failed", "use_placeholder", or "abort"
    
    Returns:
        Processing result or None if failed
    """
    
    # Validate inputs
    valid_videos = []
    for video_path in videos:
        try:
            # Basic validation
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video not found: {video_path}")
            
            # Try to get video info (this will catch corrupt files)
            info = get_video_info(video_path)
            if info.duration < 0.1:
                raise ValueError(f"Video too short: {video_path}")
            
            valid_videos.append(video_path)
            logger.info(f"✅ Validated: {video_path}")
            
        except Exception as e:
            logger.warning(f"❌ Invalid video {video_path}: {e}")
            
            if fallback_strategy == "abort":
                logger.error("Aborting due to invalid input")
                return None
            elif fallback_strategy == "use_placeholder":
                placeholder_path = create_placeholder_video(duration=5.0)
                valid_videos.append(placeholder_path)
                logger.info(f"🔄 Using placeholder for: {video_path}")
            # For "skip_failed", we just don't add it to valid_videos
    
    if len(valid_videos) < 2:
        logger.error("Need at least 2 valid videos for concatenation")
        return None
    
    # Attempt processing with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = quick_concatenate(
                video_paths=valid_videos,
                output_path=output_path,
                crossfade_duration=1.0
            )
            
            logger.info(f"🎉 Success: {output_path} ({result.duration:.1f}s)")
            return {
                'success': True,
                'output_path': output_path,
                'duration': result.duration,
                'videos_used': len(valid_videos),
                'videos_skipped': len(videos) - len(valid_videos)
            }
            
        except VideoProcessingError as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.error("All processing attempts failed")
                return {
                    'success': False,
                    'error': str(e),
                    'attempts': max_retries
                }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                'success': False,
                'error': f"Unexpected error: {e}"
            }
    
    return None

def create_placeholder_video(duration: float = 5.0) -> str:
    """Create a placeholder video for failed inputs."""
    # This would create a simple colored video with text
    # Implementation details depend on your specific needs
    placeholder_path = f"placeholder_{duration}s.mp4"
    # ... create placeholder video ...
    return placeholder_path

# Usage with error handling
video_list = ["video1.mp4", "corrupted.mp4", "video3.mp4", "missing.mp4"]
result = robust_video_processing(
    videos=video_list,
    output_path="robust_output.mp4", 
    fallback_strategy="skip_failed"
)

if result and result['success']:
    print(f"Processing succeeded: {result['videos_used']} videos used")
else:
    print(f"Processing failed: {result.get('error', 'Unknown error')}")
```

## Performance Optimization

### Memory-Efficient Processing

```python
from movie_mix_util import VideoProcessor
import psutil
import gc
from contextlib import contextmanager

@contextmanager
def memory_monitor(operation_name: str):
    """Context manager to monitor memory usage."""
    process = psutil.Process()
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"🚀 Starting {operation_name}")
    print(f"📊 Memory before: {mem_before:.1f} MB")
    
    try:
        yield
    finally:
        gc.collect()  # Force garbage collection
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_diff = mem_after - mem_before
        
        print(f"📊 Memory after: {mem_after:.1f} MB ({mem_diff:+.1f} MB)")
        print(f"✅ Completed {operation_name}")

def process_large_video_set(video_batches: list[list[str]], output_dir: str):
    """Process large video sets with memory management."""
    
    processor = VideoProcessor()
    
    for i, batch in enumerate(video_batches):
        with memory_monitor(f"Batch {i+1}/{len(video_batches)}"):
            try:
                output_path = f"{output_dir}/batch_{i+1}.mp4"
                result = quick_concatenate(batch, output_path)
                
                print(f"  ✅ Batch {i+1}: {result.duration:.1f}s")
                
                # Clear any temporary files
                cleanup_temp_files()
                
            except Exception as e:
                print(f"  ❌ Batch {i+1} failed: {e}")
                continue

def cleanup_temp_files():
    """Clean up temporary files to free memory."""
    temp_patterns = ["*.tmp", "*.temp", "ffmpeg*.log"]
    # Implementation to clean temp files
    pass

# Usage
large_video_batches = [
    ["video1.mp4", "video2.mp4", "video3.mp4"],
    ["video4.mp4", "video5.mp4", "video6.mp4"],
    # ... more batches
]

process_large_video_set(large_video_batches, "batch_outputs/")
```

### Parallel Processing Workflow

```python
from movie_mix_util import quick_crossfade, CrossfadeEffect
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import time

def create_crossfade_worker(args: tuple) -> dict:
    """Worker function for parallel crossfade processing."""
    video1, video2, output_path, effect, duration = args
    
    start_time = time.time()
    try:
        result = quick_crossfade(
            video1_path=video1,
            video2_path=video2,
            fade_duration=duration,
            output_path=output_path,
            effect=effect
        )
        
        return {
            'success': True,
            'output': output_path,
            'duration': result.duration,
            'processing_time': time.time() - start_time
        }
    except Exception as e:
        return {
            'success': False,
            'output': output_path,
            'error': str(e),
            'processing_time': time.time() - start_time
        }

def parallel_crossfade_generation(video_pairs: list, effects: list, output_dir: str):
    """Generate multiple crossfades in parallel."""
    
    # Prepare work items
    work_items = []
    for i, (video1, video2) in enumerate(video_pairs):
        for j, effect in enumerate(effects):
            output_path = f"{output_dir}/crossfade_{i}_{effect.value}.mp4"
            work_items.append((video1, video2, output_path, effect, 2.0))
    
    # Use all CPU cores minus one
    max_workers = max(1, cpu_count() - 1)
    print(f"🚀 Processing {len(work_items)} crossfades using {max_workers} workers")
    
    start_time = time.time()
    results = []
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all work
        future_to_item = {
            executor.submit(create_crossfade_worker, item): item 
            for item in work_items
        }
        
        # Collect results
        for future in as_completed(future_to_item):
            result = future.result()
            results.append(result)
            
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['output']} ({result['processing_time']:.1f}s)")
    
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r['success'])
    
    print(f"\n📊 Summary:")
    print(f"   Total items: {len(work_items)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {len(work_items) - successful}")
    print(f"   Total time: {total_time:.1f}s")
    print(f"   Average per item: {total_time / len(work_items):.1f}s")
    
    return results

# Usage
video_pairs = [
    ("scene1.mp4", "scene2.mp4"),
    ("scene2.mp4", "scene3.mp4"), 
    ("scene3.mp4", "scene4.mp4")
]

effects_to_test = [
    CrossfadeEffect.FADE,
    CrossfadeEffect.DISSOLVE,
    CrossfadeEffect.WIPE_LEFT,
    CrossfadeEffect.SLIDE_RIGHT
]

results = parallel_crossfade_generation(
    video_pairs=video_pairs,
    effects=effects_to_test,
    output_dir="parallel_crossfades/"
)
```

These examples demonstrate the full range of capabilities in movie-mix-util, from simple operations to complex production workflows. Each example includes proper error handling and follows best practices for video processing workflows.