"""Tests for deferred (lazy) concatenation planning skeleton.

These tests mock duration probing to avoid invoking ffmpeg.
"""
from pathlib import Path
import pytest

from deferred_concat import VideoConcatPlan, TransitionMode

@pytest.fixture()
def fake_videos(tmp_path, monkeypatch):
    paths = []
    # create small empty placeholder files (probing is mocked)
    for name in ["A.mp4", "B.mp4", "C.mp4"]:
        p = tmp_path / name
        p.write_bytes(b"00")
        paths.append(p)
    # monkeypatch probe function inside module
    import deferred_concat
    def fake_probe(path: str) -> float:
        base = Path(path).name[0]
        return {"A": 10.0, "B": 15.0, "C": 8.0}[base]
    monkeypatch.setattr(deferred_concat, "_probe_duration", fake_probe)
    return paths

def test_dry_run_no_increase_chain(fake_videos, tmp_path):
    out = tmp_path / "out.mp4"
    plan = (VideoConcatPlan()
            .append(str(fake_videos[0]))
            .crossfade(2.0, TransitionMode.CROSSFADE_NO_INCREASE)
            .append(str(fake_videos[1]))
            .output(str(out)))
    result = plan.dry_run()
    # total = 10 + 15 - 2 = 23
    assert abs(result["timeline_total"] - 23.0) < 1e-6
    assert "xfade(no_increase)" in result["graph_preview"]

def test_dry_run_increase_chain(fake_videos, tmp_path):
    out = tmp_path / "out2.mp4"
    plan = (VideoConcatPlan()
            .append(str(fake_videos[0]))
            .crossfade(1.5, TransitionMode.CROSSFADE_INCREASE)
            .append(str(fake_videos[1]))
            .output(str(out)))
    result = plan.dry_run()
    # total = 10 + 15 + 1.5 = 26.5
    assert abs(result["timeline_total"] - 26.5) < 1e-6
    assert "(+duration)" in result["graph_preview"]

def test_dry_run_mixed(fake_videos, tmp_path):
    out = tmp_path / "out3.mp4"
    plan = (VideoConcatPlan()
            .append(str(fake_videos[0]))
            .crossfade(1.0, TransitionMode.CROSSFADE_NO_INCREASE)
            .append(str(fake_videos[1]))
            .crossfade(0.5, TransitionMode.CROSSFADE_INCREASE)
            .append(str(fake_videos[2]))
            .output(str(out)))
    result = plan.dry_run()
    # total = 10 + 15 + 8 -1 +0.5 = 32.5
    assert abs(result["timeline_total"] - 32.5) < 1e-6
    assert result["items"][0]["type"] == "clip"
    assert result["items"][1]["type"] == "transition"


@pytest.mark.requires_ffmpeg
def test_execute_simple_chain(samples_dir, tmp_path):
    a = samples_dir / "ball_bokeh_02_slyblue.mp4"
    b = samples_dir / "13523522_1920_1080_60fps.mp4"
    out = tmp_path / "exec_out.mp4"
    plan = (VideoConcatPlan()
        .append(str(a))
        .simple()
        .append(str(b))
        .output(str(out)))
    info = plan.execute()
    assert out.exists()
    assert info["final_duration"] > 0


@pytest.mark.requires_ffmpeg
def test_execute_crossfade_no_increase(samples_dir, tmp_path):
    a = samples_dir / "ball_bokeh_02_slyblue.mp4"
    b = samples_dir / "13523522_1920_1080_60fps.mp4"
    out = tmp_path / "exec_xfade_no_inc.mp4"
    plan = (VideoConcatPlan()
        .append(str(a))
        .crossfade(1.0, TransitionMode.CROSSFADE_NO_INCREASE)
        .append(str(b))
        .output(str(out)))
    info = plan.execute()
    assert out.exists()
    assert abs(info["planned_duration"] - info["final_duration"]) < 3.0  # tolerance for approximation

def test_requires_output(fake_videos):
    plan = VideoConcatPlan().append(str(fake_videos[0]))
    with pytest.raises(ValueError):
        plan.dry_run()

def test_first_item_must_be_clip(fake_videos, tmp_path):
    out = tmp_path / "o.mp4"
    plan = VideoConcatPlan()
    # 強制的に内部を壊して例外を誘発（直接属性アクセスは本来想定外）
    plan._items.append(42)  # type: ignore
    plan.output(str(out))
    with pytest.raises(ValueError):
        plan.dry_run()
