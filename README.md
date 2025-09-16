# movie-mix-util - Modern Video Processing Library

A comprehensive Python library for video processing, composition, and concatenation with advanced crossfade effects.

## Features

- **Video Concatenation**: Combine multiple videos with various transition modes
- **Crossfade Effects**: 30+ professional transition effects (fade, dissolve, wipe, slide, etc.)
- **Image Overlay**: Overlay images on video backgrounds with automatic scaling
- **Multiple Output Modes**: 
  - Fade-only segments
  - Full concatenated sequences  
  - Custom duration outputs
- **Type-Safe API**: Modern Python with comprehensive type hints
- **Professional Documentation**: Complete API reference and examples

## Installation

### Requirements
- Python 3.11+
- FFmpeg (required for video processing)

```bash
# Install FFmpeg
# macOS: 
brew install ffmpeg
# Ubuntu: 
sudo apt install ffmpeg
# Windows: Download from https://ffmpeg.org/

# Install movie-mix-util
pip install git+https://github.com/densuke/movie-mix-util.git

# Or using uv
uv pip install git+https://github.com/densuke/movie-mix-util.git

# For local development with uv (editable install)
# From your project directory, assuming movie-mix-util is a sibling directory
# Replace /path/to/your/local/movie-mix-util/repository with the actual path to your local clone
uv pip install -e git+file:///home/youruser/dev/movie-mix-util

# For development
git clone https://github.com/densuke/movie-mix-util.git
cd movie-mix-util
uv sync --dev
```

## Quick Start

### Running the cat_movies.py Example

To run the `cat_movies.py` example located in the `examples/` directory:

1.  Ensure you have installed `movie-mix-util` in editable mode for local development (as described above).
2.  Navigate to your project directory (e.g., `cat-movie-example`).
3.  Make sure the necessary video files (e.g., `samples/02_ball_bokeh_02_slyblue.mp4`) are available in the expected paths relative to `cat_movies.py`.
4.  Execute the script:
    ```bash
    uv run examples/cat_movies.py
    ```

### Basic Video Concatenation

```python
from movie_mix_util import VideoProcessor, VideoSequenceBuilder, TransitionMode

# Create processor
processor = VideoProcessor()

# Build sequence with transitions
sequence = (VideoSequenceBuilder()
    .add_video("video1.mp4")
    .add_crossfade(1.0, TransitionMode.CROSSFADE_NO_INCREASE)
    .add_video("video2.mp4")
    .add_crossfade(2.0, TransitionMode.CROSSFADE_INCREASE)
    .add_video("video3.mp4")
    .build())

# Process videos
result = processor.concatenate_videos(sequence, "output.mp4")
print(f"Created video: {result.duration:.1f} seconds")
```

### Quick Functions

```python
from movie_mix_util import quick_concatenate, quick_mix, quick_crossfade

# Simple concatenation
result = quick_concatenate(
    ["video1.mp4", "video2.mp4", "video3.mp4"],
    "combined.mp4",
    crossfade_duration=1.5
)

# Video + image overlay
result = quick_mix(
    "background_video.mp4", 
    "overlay_image.png", 
    "mixed_output.mp4", 
    duration=30
)

# Standalone crossfade effect
result = quick_crossfade(
    "video1.mp4", 
    "video2.mp4",
    fade_duration=2.0,
    output_path="crossfade.mp4"
)
```

### Advanced Crossfade Effects

```python
from movie_mix_util import create_crossfade_video, CrossfadeEffect, CrossfadeOutputMode

# Create professional crossfade with specific effect
result = create_crossfade_video(
    "video1.mp4",
    "video2.mp4", 
    fade_duration=1.5,
    output_path="professional_transition.mp4",
    effect=CrossfadeEffect.SLIDE_RIGHT,
    output_mode=CrossfadeOutputMode.FADE_ONLY
)
```

### Deferred Execution Model (遅延実行モデル)

For more complex concatenations, the deferred execution model provides a powerful and efficient way to build your video sequence. This approach constructs the entire FFmpeg filter graph in memory and executes it as a single command, minimizing overhead.

```python
from deferred_concat import movie, CrossfadeEffect

# Build and execute a sequence in a single chain
result = (
    movie("intro.mp4")
    .append("scene1.mp4", duration=2.0, effect=CrossfadeEffect.DISSOLVE, mode=TransitionMode.CROSSFADE_NO_INCREASE)
    .append("scene2.mp4", duration=1.5, effect=CrossfadeEffect.WIPELEFT, mode=TransitionMode.CROSSFADE_INCREASE)
    .append("outro.mp4", duration=3.0, effect=CrossfadeEffect.FADE, mode=TransitionMode.CROSSFADE_NO_INCREASE)
    .execute("final_movie_deferred.mp4")
)

print(f"Successfully created video: {result['output_path']}")
```

## Transition Modes

| Mode | Description | Duration Calculation |
|------|-------------|---------------------|
| `NONE` | Simple concatenation | A(15s) + B(15s) = 30s |
| `CROSSFADE_NO_INCREASE` | Overlap transition | A(15s) + B(15s) - 1s = 29s |
| `CROSSFADE_INCREASE` | Additive transition | A(15s) + fade(1s) + B(15s) = 31s |

## Crossfade Effects

Available effects include: `FADE`, `DISSOLVE`, `WIPE_LEFT`, `WIPE_RIGHT`, `SLIDE_LEFT`, `SLIDE_RIGHT`, `CIRCLE_CROP`, `RECT_CROP`, and many more. See [API_REFERENCE.md](API_REFERENCE.md) for the complete list.

## Output Modes

- `FADE_ONLY`: Generate only the crossfade transition segment
- `FULL_SEQUENCE`: Complete concatenated video with transitions
- `CUSTOM`: Custom duration output with specified length

## Documentation

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Examples](EXAMPLES.md) - Practical usage examples
- [Tests](tests/) - Comprehensive test suite

## Development

```bash
# Run tests
uv run pytest

# Code formatting
uv run black .
uv run ruff --fix .

# Type checking
uv run mypy .

# Build package
uv build
```

## Dependencies

- **ffmpeg-python** >= 0.2.0 - FFmpeg Python bindings
- **Pillow** >= 11.3.0 - Image processing library

## Error Handling

The library provides comprehensive error handling for common scenarios:

- Missing input files
- Invalid video formats
- FFmpeg processing errors
- Parameter validation errors

All exceptions inherit from `VideoProcessingError` for easy catching.

## Performance

- Efficient FFmpeg pipeline processing
- Memory-conscious streaming operations
- Parallel processing where possible
- Optimized for production workloads

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Changelog

### Version 1.0.0
- Complete library rewrite with modern Python 3.12+ features
- 30+ professional crossfade effects
- Type-safe API with comprehensive documentation
- Multiple output modes and flexible configuration
- Performance optimizations and error handling improvements