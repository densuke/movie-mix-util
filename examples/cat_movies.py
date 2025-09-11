#!/usr/bin/env python
from movie_mix_util import movie, CrossfadeEffect, TransitionMode

def main():
    """
    DeferredConcatを使用して、複数のビデオを異なるトランジションで連結するサンプル
    """
    base = movie("samples/01_13523522_1920_1080_60fps.mp4")

    (
        base
        .append(
            "samples/03_intensive_line_02_color.mp4",
            duration=1,
            effect=CrossfadeEffect.FADE,
            mode=TransitionMode.CROSSFADE_NO_INCREASE
        )
        .append(
            "samples/04_thunder_03_white_ver.mp4",
            duration=1.5,
            effect=CrossfadeEffect.DISSOLVE,
            mode=TransitionMode.CROSSFADE_NO_INCREASE
        )
        .append(
            "samples/02_ball_bokeh_02_slyblue.mp4",
            duration=2,
            effect=CrossfadeEffect.WIPELEFT,
            mode=TransitionMode.CROSSFADE_NO_INCREASE
        )
        .execute("cat_movies_output.mp4")
    )
    print("Generated video: cat_movies_output.mp4")

if __name__ == "__main__":
    main()
