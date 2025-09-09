"""Deferred (lazy) video concatenation planning module.

This module introduces a new API to build a concatenation plan with method
chaining and execute everything in a single ffmpeg invocation (future work).

Current status: SKELETON (dry-run). It only validates the plan and prints
(outlines) the intended filter graph operations without invoking ffmpeg.

Goals:
- Preserve existing public API (advanced_video_concatenator, VideoSequenceBuilder)
- Offer new fluent interface: (VideoConcatPlan().append('A.mp4').crossfade(1.0,'no_increase').append('B.mp4').execute())
- Support transition modes compatible with TransitionMode

Next steps (not yet implemented):
- Generate real filter_complex leveraging xfade / concat
- Support both no_increase and increase semantics (legacy static crossfade & improved dynamic crossfade)
- (Optional) audio handling in later phase
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Union, Iterable
from enum import Enum
from pathlib import Path

try:  # pragma: no cover - import resolution
    from advanced_video_concatenator import TransitionMode as _RealTransitionMode, get_video_duration as _real_get_video_duration
    TransitionMode = _RealTransitionMode  # expose alias
    def _probe_duration(path: str) -> float:
        return _real_get_video_duration(path)
except Exception:  # pragma: no cover - fallback
    class TransitionMode(Enum):  # minimal stub
        NONE = "none"
        CROSSFADE_NO_INCREASE = "no_increase"
        CROSSFADE_INCREASE = "increase"
    def _probe_duration(path: str) -> float:
        raise RuntimeError("get_video_duration unavailable in stub context")


@dataclass
class _VideoClip:
    path: str
    duration: Optional[float] = None  # filled lazily

@dataclass
class _TransitionSpec:
    mode: TransitionMode
    duration: float

class PlanState(Enum):
    BUILDING = "building"
    FROZEN = "frozen"
    EXECUTED = "executed"

ClipOrTransition = Union['_VideoClip', '_TransitionSpec']


class VideoConcatPlan:
    """Fluent builder for deferred concatenation.

    Example:
        plan = (VideoConcatPlan()
                  .append("A.mp4")
                  .crossfade(1.0, TransitionMode.CROSSFADE_NO_INCREASE)
                  .append("B.mp4")
                  .append("C.mp4")
                  .output("out.mp4")
                  .dry_run())
    """
    def __init__(self) -> None:
    self._items: List[ClipOrTransition] = []  # sequence
        self._output_path: Optional[str] = None
        self._state: PlanState = PlanState.BUILDING
        self._legacy_static_crossfade: bool = True  # legacy visual semantics for increase mode

    # ------------------ Fluent API ------------------
    def append(self, video_path: str) -> "VideoConcatPlan":
        self._assert_building()
        if not Path(video_path).exists():
            # We allow non-existent only for dry planning? For now raise to mimic current behavior
            raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")
        self._items.append(_VideoClip(video_path))
        return self

    def crossfade(self, duration: float, mode: TransitionMode = TransitionMode.CROSSFADE_INCREASE) -> "VideoConcatPlan":
        self._assert_building()
        if duration <= 0:
            raise ValueError("クロスフェード時間は0より大きい必要があります")
        self._items.append(_TransitionSpec(mode=mode, duration=duration))
        return self

    def simple(self) -> "VideoConcatPlan":
        """Add a simple (NONE) transition"""
        self._assert_building()
        self._items.append(_TransitionSpec(mode=TransitionMode.NONE, duration=0.0))
        return self

    def output(self, path: str) -> "VideoConcatPlan":
        self._assert_building()
        self._output_path = path
        return self

    def legacy_static(self, enabled: bool = True) -> "VideoConcatPlan":
        """Toggle legacy static crossfade visual style (increase mode)."""
        self._legacy_static_crossfade = enabled
        return self

    # ------------------ Execution (dry for now) ------------------
    def dry_run(self) -> dict:
        """Validate and return planned operations & computed timing without invoking ffmpeg."""
        self._freeze()
        timeline = self._compute_timeline()
        graph_preview = self._build_filter_graph_preview(timeline)
        return {
            "output": self._output_path,
            "items": [self._describe_item(it) for it in self._items],
            "timeline_total": timeline["total_duration"],
            "graph_preview": graph_preview,
            "legacy_static_crossfade": self._legacy_static_crossfade,
        }

    # Placeholder for future actual execution
    def execute(self) -> dict:
        # First freeze to validate & fill durations
        self._freeze()
        # Build legacy sequence objects for reuse of existing implementation
        try:  # local import to avoid heavy cost if only dry_run used
            from advanced_video_concatenator import (
                VideoSegment as LegacyVideoSegment,
                Transition as LegacyTransition,
                concatenate_videos_advanced as legacy_concat,
            )
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"既存連結機能のインポートに失敗しました: {e}")

        legacy_sequence: List[object] = []
        for it in self._items:
            if isinstance(it, _VideoClip):
                legacy_sequence.append(LegacyVideoSegment(it.path))
            elif isinstance(it, _TransitionSpec):
                legacy_sequence.append(LegacyTransition(it.mode, it.duration))

        # Execute using existing advanced pipeline (single ffmpeg run)
        legacy_concat(legacy_sequence, self._output_path)  # type: ignore[arg-type]

        # Probe final duration
        final_duration = _probe_duration(self._output_path)
        timeline = self._compute_timeline()
        return {
            "output": self._output_path,
            "final_duration": final_duration,
            "planned_duration": timeline["total_duration"],
            "items": [self._describe_item(i) for i in self._items],
            "legacy_path": True,
        }

    # ------------------ Internals ------------------
    def _assert_building(self) -> None:
        if self._state is not PlanState.BUILDING:
            raise RuntimeError("Plan is frozen; no further modifications allowed")

    def _freeze(self) -> None:
        if self._state is PlanState.BUILDING:
            if not self._output_path:
                raise ValueError("output() で出力パスを指定してください")
            if not self._items:
                raise ValueError("少なくとも1つの動画が必要です")
            if not isinstance(self._items[0], _VideoClip):
                raise ValueError("最初の要素は動画である必要があります")
            # duration 補完
            for it in self._items:
                if isinstance(it, _VideoClip) and it.duration is None:
                    it.duration = _probe_duration(it.path)
            self._state = PlanState.FROZEN

    def _compute_timeline(self) -> dict:
        total = 0.0
        details: List[dict] = []
        for it in self._items:
            if isinstance(it, _VideoClip):
                dur = it.duration or 0.0
                total += dur
                details.append({"type": "clip", "path": it.path, "duration": it.duration})
            elif isinstance(it, _TransitionSpec):
                if it.mode == TransitionMode.CROSSFADE_NO_INCREASE:
                    total -= it.duration
                elif it.mode == TransitionMode.CROSSFADE_INCREASE:
                    total += it.duration
                details.append({"type": "transition", "mode": it.mode.value, "duration": it.duration})
        return {"total_duration": total, "details": details}

    def _build_filter_graph_preview(self, timeline: dict) -> str:
        # Outline style representation only
        lines = ["# Planned filter graph (preview only)"]
        input_index = 0
        clip_label = None
        xf_count = 0
        for idx, it in enumerate(self._items):
            if isinstance(it, _VideoClip):
                label = f"[v{input_index}]"
                lines.append(f"input {it.path} as {label} duration={it.duration:.2f}s")
                input_index += 1
                if clip_label is None:
                    clip_label = label
                else:
                    # next transition will define how to combine; no action here
                    pass
            elif isinstance(it, _TransitionSpec):
                if it.mode == TransitionMode.NONE:
                    lines.append("-- simple concat boundary --")
                elif it.mode == TransitionMode.CROSSFADE_NO_INCREASE:
                    xf_count += 1
                    lines.append(f"xfade(no_increase) dur={it.duration} -> [xf{xf_count}]")
                    clip_label = f"[xf{xf_count}]"
                elif it.mode == TransitionMode.CROSSFADE_INCREASE:
                    xf_count += 1
                    mode = "increase-static" if self._legacy_static_crossfade else "increase-dynamic"
                    lines.append(f"xfade({mode}) dur={it.duration} -> [xf{xf_count}] (+duration)")
                    clip_label = f"[xf{xf_count}]"
        lines.append(f"final output -> {self._output_path}")
        lines.append(f"total ≈ {timeline['total_duration']:.2f}s")
        return "\n".join(lines)

    def _describe_item(self, it: object) -> dict:
        if isinstance(it, _VideoClip):
            return {"type": "clip", "path": it.path, "duration": it.duration}
        if isinstance(it, _TransitionSpec):
            return {"type": "transition", "mode": it.mode.value, "duration": it.duration}
        return {"type": "unknown"}

__all__ = ["VideoConcatPlan"]
