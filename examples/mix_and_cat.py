#!/usr/bin/env python
from movie_mix_util import TransitionMode, quick_mix, movie, CrossfadeEffect


def main():
    """
    背景動画と静止画を合成して指定長の動画を生成するサンプル
    """
    result = quick_mix(
        background_video="samples/02_ball_bokeh_02_slyblue.mp4",
        overlay_image="samples/title-base.png",
        output_path="/tmp/mix1.mp4",
        duration=5,
    )
    print(f"Generated video: {result.path}")

    result = quick_mix(
        background_video="samples/02_ball_bokeh_02_slyblue.mp4",
        overlay_image="samples/02-1.png",
        output_path="/tmp/mix2.mp4",
        duration=5,
    )

    base = movie("/tmp/mix1.mp4")
    base.append(
        "/tmp/mix2.mp4",
        duration=1,
        effect=CrossfadeEffect.DISSOLVE,
        mode=TransitionMode.CROSSFADE_NO_INCREASE,
    ).execute("examples/mix_and_cat_output.mp4")


if __name__ == "__main__":
    main()
