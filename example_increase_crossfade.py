from deferred_concat import movie
from advanced_video_concatenator import CrossfadeEffect, TransitionMode

def main() -> None:
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
