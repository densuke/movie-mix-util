from movie_mix_util import movie, CrossfadeEffect, TransitionMode

def main() -> None:
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
