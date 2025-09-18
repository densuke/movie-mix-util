#!/usr/bin/env python
from movie_mix_util import movie, CrossfadeEffect, TransitionMode

def main():
    """
    DeferredConcatを使用して、複数のビデオを異なるトランジションで連結するサンプル
    """
    base = movie("/tmp/mix1.mp4")

    (
        base
        .append(
            "/tmp/mix2.mp4",
            duration=1,
            effect=CrossfadeEffect.FADE,
            mode=TransitionMode.CROSSFADE_NO_INCREASE
        )
        .execute("examples/cat_movies2_output.mp4")
    )
    print("Generated video: examples/cat_movies2_output.mp4")

if __name__ == "__main__":
    main()
