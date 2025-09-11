#!/usr/bin/env python
from movie_mix_util import quick_mix

def main():
    """
    背景動画と静止画を合成して指定長の動画を生成するサンプル
    """
    result = quick_mix(
        background_video="samples/02_ball_bokeh_02_slyblue.mp4",
        overlay_image="samples/title-base.png",
        output_path="movie_mix_output.mp4",
        duration=30
    )
    print(f"Generated video: {result.path}")

if __name__ == "__main__":
    main()
