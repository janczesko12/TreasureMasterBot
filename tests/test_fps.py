"""Unit tests for app.core.fps.FpsCounter.

New test-only file; nothing imports it except pytest's test discovery.
Covers the rolling-window FPS math in ``app/core/fps.py`` (created
earlier this session for Version 0.3, per the approved plan's Phase 0
item 4: "Add FpsCounter utility"), using explicit ``now_s`` timestamps
passed to ``tick()`` so the tests are deterministic and don't depend
on real wall-clock timing.
"""

from __future__ import annotations

from app.core.fps import FpsCounter


class TestFpsCounter:
    def test_returns_zero_with_no_samples(self) -> None:
        counter = FpsCounter()

        assert counter.fps == 0.0

    def test_returns_zero_with_a_single_sample(self) -> None:
        counter = FpsCounter()
        counter.tick(now_s=0.0)

        assert counter.fps == 0.0

    def test_computes_fps_from_two_samples(self) -> None:
        counter = FpsCounter()
        counter.tick(now_s=0.0)
        counter.tick(now_s=1.0)

        assert counter.fps == 1.0

    def test_computes_fps_from_multiple_samples(self) -> None:
        counter = FpsCounter()
        counter.tick(now_s=0.0)
        counter.tick(now_s=0.5)
        counter.tick(now_s=1.0)

        assert counter.fps == 2.0

    def test_trims_samples_outside_the_window(self) -> None:
        counter = FpsCounter(window_s=2.0)
        counter.tick(now_s=0.0)
        counter.tick(now_s=0.5)
        counter.tick(now_s=3.0)

        assert counter.fps == 0.0

    def test_respects_custom_window_s(self) -> None:
        counter = FpsCounter(window_s=1.0)
        counter.tick(now_s=0.0)
        counter.tick(now_s=0.5)
        counter.tick(now_s=1.5)

        assert counter.fps == 1.0

    def test_uses_current_monotonic_time_when_now_s_omitted(self) -> None:
        counter = FpsCounter()
        counter.tick()
        counter.tick()

        assert counter.fps >= 0.0
