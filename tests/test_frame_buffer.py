"""Unit tests for app.core.frame_buffer (DropOldestBuffer and FrameMailbox).

New test-only file; nothing imports it except pytest's test discovery.
Covers the two hand-off primitives added earlier this session for
Version 0.3 per the approved plan's Phase 0 items 2-3 ("Add a bounded,
drop-oldest frame buffer helper" / "Add a thread-safe single-slot
'latest frame' mailbox helper") and exercised by Phase 3 item 15
("frame_buffer, mailbox ... unit tests"). No data schemas involved -
plain ``queue.Queue``-compatible behavior tested with ints as a stand-in
for ``Frame`` payloads.
"""

from __future__ import annotations

import queue

import pytest

from app.core.frame_buffer import DropOldestBuffer, FrameMailbox


class TestDropOldestBuffer:
    def test_get_returns_items_in_fifo_order_within_capacity(self) -> None:
        buffer: DropOldestBuffer[int] = DropOldestBuffer(max_size=4)
        buffer.put_latest(1)
        buffer.put_latest(2)

        assert buffer.get_nowait() == 1
        assert buffer.get_nowait() == 2

    def test_drops_oldest_item_when_full(self) -> None:
        buffer: DropOldestBuffer[int] = DropOldestBuffer(max_size=2)
        buffer.put_latest(1)
        buffer.put_latest(2)
        buffer.put_latest(3)

        assert buffer.get_nowait() == 2
        assert buffer.get_nowait() == 3

    def test_get_nowait_raises_empty_when_no_items(self) -> None:
        buffer: DropOldestBuffer[int] = DropOldestBuffer()

        with pytest.raises(queue.Empty):
            buffer.get_nowait()

    def test_get_raises_empty_on_timeout(self) -> None:
        buffer: DropOldestBuffer[int] = DropOldestBuffer()

        with pytest.raises(queue.Empty):
            buffer.get(timeout=0.01)

    def test_get_returns_item_when_available(self) -> None:
        buffer: DropOldestBuffer[int] = DropOldestBuffer()
        buffer.put_latest(42)

        assert buffer.get() == 42

    def test_task_done_does_not_raise_after_get(self) -> None:
        buffer: DropOldestBuffer[int] = DropOldestBuffer()
        buffer.put_latest(1)
        buffer.get_nowait()

        buffer.task_done()

    def test_qsize_reflects_current_contents(self) -> None:
        buffer: DropOldestBuffer[int] = DropOldestBuffer(max_size=4)

        assert buffer.qsize() == 0

        buffer.put_latest(1)
        buffer.put_latest(2)

        assert buffer.qsize() == 2


class TestFrameMailbox:
    def test_get_returns_none_before_any_set(self) -> None:
        mailbox: FrameMailbox[int] = FrameMailbox()

        assert mailbox.get() is None

    def test_get_returns_the_value_that_was_set(self) -> None:
        mailbox: FrameMailbox[int] = FrameMailbox()
        mailbox.set(7)

        assert mailbox.get() == 7

    def test_set_overwrites_the_previous_value(self) -> None:
        mailbox: FrameMailbox[int] = FrameMailbox()
        mailbox.set(1)
        mailbox.set(2)

        assert mailbox.get() == 2
