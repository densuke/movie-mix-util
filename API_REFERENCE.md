# API Reference - movie-mix-util

Complete reference documentation for the movie-mix-util video processing library.

## Table of Contents

1. [Core Classes](#core-classes)
2. [Enumerations](#enumerations)
3. [Quick Functions](#quick-functions)
4. [Advanced Functions](#advanced-functions)
5. [Error Handling](#error-handling)
6. [Type Definitions](#type-definitions)

## Core Classes

### VideoProcessor

Main processing class for video operations.

```python
class VideoProcessor:
    """
    Primary interface for video processing operations.
    
    Provides methods for concatenating videos, applying transitions,
    and mixing video with images.
    """
```

#### Methods

##### `__init__(self, default_fps: int = 30, default_size: tuple[int, int] = (1920, 1080))`

Initialize the video processor.

**Parameters:**
- `default_fps` (int): Default frame rate for output videos
- `default_size` (tuple[int, int]): Default resolution as (width, height)

**Example:**
```python
processor = VideoProcessor(default_fps=60, default_size=(3840, 2160))
```

##### `concatenate_videos(self, sequence: VideoSequence, output_path: str) -> VideoInfo`

Concatenate videos according to the provided sequence.

**Parameters:**
- `sequence` (VideoSequence): Sequence definition with videos and transitions
- `output_path` (str): Path for the output video file

**Returns:**
- `VideoInfo`: Information about the generated video

**Raises:**
- `VideoProcessingError`: If processing fails
- `FileNotFoundError`: If input files don't exist

**Example:**
```python
sequence = VideoSequenceBuilder().add_video("A.mp4").build()
result = processor.concatenate_videos(sequence, "output.mp4")
```

##### `mix_video_with_image(self, video_path: str, image_path: str, output_path: str, duration: int = 30) -> VideoInfo`

Overlay an image on a video background.

**Parameters:**
- `video_path` (str): Path to background video
- `image_path` (str): Path to overlay image
- `output_path` (str): Path for output video
- `duration` (int): Duration in seconds

**Returns:**
- `VideoInfo`: Information about the generated video

### VideoSequenceBuilder

Builder pattern class for constructing video sequences.

```python
class VideoSequenceBuilder:
    """
    Builder for creating video sequences with transitions.
    
    Provides a fluent interface for adding videos and crossfade
    transitions in a sequence.
    """
```

#### Methods

##### `add_video(self, video_path: str) -> VideoSequenceBuilder`

Add a video to the sequence.

**Parameters:**
- `video_path` (str): Path to the video file

**Returns:**
- `VideoSequenceBuilder`: Self for method chaining

##### `add_crossfade(self, duration: float, mode: TransitionMode = TransitionMode.CROSSFADE_INCREASE) -> VideoSequenceBuilder`

Add a crossfade transition.

**Parameters:**
- `duration` (float): Crossfade duration in seconds
- `mode` (TransitionMode): Transition mode

**Returns:**
- `VideoSequenceBuilder`: Self for method chaining

##### `build(self) -> VideoSequence`

Build the final video sequence.

**Returns:**
- `VideoSequence`: Completed sequence definition

**Example:**
```python
sequence = (VideoSequenceBuilder()
    .add_video("video1.mp4")
    .add_crossfade(1.5, TransitionMode.CROSSFADE_NO_INCREASE)
    .add_video("video2.mp4")
    .build())
```

### VideoInfo

Container for video metadata and information.

```python
@dataclass
class VideoInfo:
    """
    Video file information and metadata.
    
    Attributes:
        path: File path
        duration: Duration in seconds
        width: Video width in pixels
        height: Video height in pixels
        fps: Frames per second
        size_mb: File size in megabytes
    """
    path: str
    duration: float
    width: int
    height: int
    fps: float
    size_mb: float
```

## Enumerations

### TransitionMode

Defines video transition behavior.

```python
class TransitionMode(Enum):
    """
    Video transition modes for concatenation.
    """
    NONE = "none"                          # Simple concatenation
    CROSSFADE_NO_INCREASE = "no_increase"  # Overlap, no time added
    CROSSFADE_INCREASE = "increase"        # Crossfade adds to total time
```

### CrossfadeEffect

Available crossfade transition effects.

```python
class CrossfadeEffect(Enum):
    """
    Professional crossfade effects for video transitions.
    """
    FADE = "fade"                          # Simple fade transition
    DISSOLVE = "fadefast"                  # Fast dissolve
    WIPE_LEFT = "wipeleft"                 # Wipe from right to left
    WIPE_RIGHT = "wiperight"               # Wipe from left to right
    SLIDE_LEFT = "slideleft"               # Slide left transition
    SLIDE_RIGHT = "slideright"             # Slide right transition
    CIRCLE_CROP = "circlecrop"             # Circular crop transition
    RECT_CROP = "rectcrop"                 # Rectangular crop
    # ... and 20+ more effects
```

### CrossfadeOutputMode

Output generation modes for crossfade operations.

```python
class CrossfadeOutputMode(Enum):
    """
    Output modes for crossfade video generation.
    """
    FADE_ONLY = "fade_only"                # Generate only transition segment
    FULL_SEQUENCE = "full_sequence"        # Complete video with transitions
    CUSTOM = "custom"                      # Custom duration output
```

## Quick Functions

### quick_concatenate

Simple video concatenation with uniform settings.

```python
def quick_concatenate(
    video_paths: list[str],
    output_path: str,
    crossfade_duration: float = 1.0,
    crossfade_mode: TransitionMode = TransitionMode.CROSSFADE_INCREASE
) -> VideoInfo:
    """
    Quick concatenation of multiple videos with uniform crossfade.
    
    Args:
        video_paths: List of input video file paths
        output_path: Output video file path  
        crossfade_duration: Duration of crossfade transitions
        crossfade_mode: Type of crossfade transition
    
    Returns:
        VideoInfo: Information about the generated video
        
    Raises:
        VideoProcessingError: If processing fails
        ValueError: If less than 2 videos provided
    """
```

**Example:**
```python
result = quick_concatenate(
    ["video1.mp4", "video2.mp4", "video3.mp4"],
    "output.mp4",
    crossfade_duration=2.0,
    crossfade_mode=TransitionMode.CROSSFADE_NO_INCREASE
)
```

### quick_mix

Quick video and image mixing.

```python
def quick_mix(
    background_video: str,
    overlay_image: str, 
    output_path: str,
    duration: int = 30
) -> VideoInfo:
    """
    Quick mixing of video background with image overlay.
    
    Args:
        background_video: Background video file path
        overlay_image: Overlay image file path
        output_path: Output video file path
        duration: Output duration in seconds
        
    Returns:
        VideoInfo: Information about the generated video
    """
```

### quick_crossfade

Generate standalone crossfade transitions.

```python
def quick_crossfade(
    video1_path: str,
    video2_path: str,
    fade_duration: float,
    output_path: str,
    effect: CrossfadeEffect = CrossfadeEffect.FADE
) -> VideoInfo:
    """
    Generate a standalone crossfade transition between two videos.
    
    Args:
        video1_path: First video file path
        video2_path: Second video file path  
        fade_duration: Duration of crossfade effect
        output_path: Output video file path
        effect: Type of crossfade effect
        
    Returns:
        VideoInfo: Information about the generated crossfade video
    """
```

## Advanced Functions

### create_crossfade_video

Advanced crossfade video generation with full control.

```python
def create_crossfade_video(
    video1_path: str,
    video2_path: str,
    fade_duration: float,
    output_path: str,
    effect: CrossfadeEffect = CrossfadeEffect.FADE,
    output_mode: CrossfadeOutputMode = CrossfadeOutputMode.FADE_ONLY,
    custom_duration: float | None = None
) -> dict[str, any]:
    """
    Create crossfade video with advanced options.
    
    Args:
        video1_path: First input video
        video2_path: Second input video
        fade_duration: Crossfade duration in seconds
        output_path: Output file path
        effect: Crossfade effect type
        output_mode: Output generation mode
        custom_duration: Custom output duration (for CUSTOM mode)
        
    Returns:
        dict: Processing results with metadata
        
    Raises:
        VideoProcessingError: If processing fails
        ValueError: If parameters are invalid
    """
```

**Example:**
```python
result = create_crossfade_video(
    "video1.mp4",
    "video2.mp4",
    fade_duration=3.0,
    output_path="transition.mp4",
    effect=CrossfadeEffect.CIRCLE_CROP,
    output_mode=CrossfadeOutputMode.FULL_SEQUENCE
)
```

### concatenate_videos_advanced

Advanced video concatenation with per-transition control.

```python
def concatenate_videos_advanced(
    videos: list[str],
    output_path: str,
    crossfade_config: list[dict[str, any]] | None = None,
    default_crossfade: float = 1.0,
    default_mode: TransitionMode = TransitionMode.CROSSFADE_INCREASE
) -> VideoInfo:
    """
    Advanced video concatenation with per-transition configuration.
    
    Args:
        videos: List of input video paths
        output_path: Output video path
        crossfade_config: Per-transition configuration
        default_crossfade: Default crossfade duration
        default_mode: Default transition mode
        
    Returns:
        VideoInfo: Generated video information
    """
```

## Error Handling

### VideoProcessingError

Base exception for all video processing errors.

```python
class VideoProcessingError(Exception):
    """
    Base exception for video processing operations.
    
    All specific video processing errors inherit from this class,
    allowing for easy exception handling.
    """
```

### Common Error Scenarios

```python
try:
    result = quick_concatenate(["video1.mp4", "video2.mp4"], "output.mp4")
except VideoProcessingError as e:
    print(f"Video processing failed: {e}")
except FileNotFoundError as e:
    print(f"Input file not found: {e}")
except ValueError as e:
    print(f"Invalid parameters: {e}")
```

## Type Definitions

### VideoSequence

Type alias for video sequence definition.

```python
VideoSequence = list[VideoSegment | Transition]
```

### VideoSegment

```python
@dataclass
class VideoSegment:
    """
    Represents a video segment in a sequence.
    
    Attributes:
        path: Video file path
        start_time: Start time offset (optional)
        duration: Segment duration (optional)
    """
    path: str
    start_time: float | None = None
    duration: float | None = None
```

### Transition

```python
@dataclass  
class Transition:
    """
    Represents a transition between video segments.
    
    Attributes:
        duration: Transition duration in seconds
        mode: Transition mode
        effect: Crossfade effect (for crossfade transitions)
    """
    duration: float
    mode: TransitionMode
    effect: CrossfadeEffect | None = None
```

## Usage Patterns

### Error Handling Pattern

```python
from movie_mix_util import VideoProcessingError, quick_concatenate

try:
    result = quick_concatenate(videos, "output.mp4")
    print(f"Success: {result.duration:.1f}s video created")
except VideoProcessingError as e:
    print(f"Processing error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Batch Processing Pattern

```python
from movie_mix_util import VideoProcessor, VideoSequenceBuilder

processor = VideoProcessor()
for i, video_set in enumerate(video_batches):
    sequence = VideoSequenceBuilder()
    for video in video_set:
        sequence.add_video(video).add_crossfade(1.0)
    
    result = processor.concatenate_videos(
        sequence.build(), 
        f"batch_{i}.mp4"
    )
    print(f"Batch {i}: {result.duration:.1f}s")
```

### Validation Pattern

```python
import os
from pathlib import Path

def validate_inputs(video_paths: list[str]) -> bool:
    """Validate input files exist and are accessible."""
    for path in video_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Video not found: {path}")
        if not os.access(path, os.R_OK):
            raise PermissionError(f"Cannot read: {path}")
    return True

# Use with API calls
video_files = ["video1.mp4", "video2.mp4"]
validate_inputs(video_files)
result = quick_concatenate(video_files, "output.mp4")
```

This API reference provides complete documentation for all public interfaces in the movie-mix-util library. For practical examples and workflows, see [EXAMPLES.md](EXAMPLES.md).