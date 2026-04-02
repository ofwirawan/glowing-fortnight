"""
Test cases for speaker ID debouncing.

Tests based on the specification:
- Remove rapid speaker-ID bounces shorter than min_hold_frames
- Replace short flicker runs with surrounding stable speaker ID
- Preserve None segments (no speaker detected)
"""

import pytest
from src.debouncer import debounce_speaker_ids


class TestDebounceBasics:
    """Basic functionality tests."""

    def test_empty_input(self):
        """Empty list returns empty list."""
        result = debounce_speaker_ids([])
        assert result == []

    def test_single_speaker_stable(self):
        """Single stable speaker throughout."""
        result = debounce_speaker_ids([0] * 50)
        assert result == [0] * 50

    def test_all_none(self):
        """All None (no speakers) returns all None."""
        result = debounce_speaker_ids([None] * 50)
        assert result == [None] * 50

    def test_two_stable_speakers(self):
        """Two stable speakers, no flickering."""
        input_ids = [0] * 50 + [1] * 50
        result = debounce_speaker_ids(input_ids)
        assert result == input_ids


class TestDebounceDocstringExamples:
    """Test the examples provided in the docstring."""

    def test_short_flicker_removed(self):
        """Short 3-frame flicker is replaced by surrounding speaker."""
        input_ids = [0] * 50 + [1] * 3 + [0] * 50
        result = debounce_speaker_ids(input_ids, min_hold_frames=10)
        assert result == [0] * 103
        assert len(result) == len(input_ids)

    def test_none_segments_untouched(self):
        """None segments are never modified."""
        input_ids = [None] * 10 + [0] * 50
        result = debounce_speaker_ids(input_ids, min_hold_frames=15)
        assert result == input_ids


class TestDebounceShortSegments:
    """Tests for removing short flicker segments."""

    def test_one_frame_flicker(self):
        """Single-frame flicker is removed."""
        input_ids = [0] * 20 + [1] + [0] * 20
        result = debounce_speaker_ids(input_ids, min_hold_frames=5)
        assert result == [0] * 41

    def test_two_frame_flicker(self):
        """Two-frame flicker below threshold is removed."""
        input_ids = [0] * 20 + [1, 1] + [0] * 20
        result = debounce_speaker_ids(input_ids, min_hold_frames=5)
        assert result == [0] * 42

    def test_exact_threshold_kept(self):
        """Segment exactly at threshold is kept (not removed)."""
        input_ids = [0] * 20 + [1] * 10 + [0] * 20
        result = debounce_speaker_ids(input_ids, min_hold_frames=10)
        # 10 frames of speaker 1 is not shorter than threshold
        assert result == input_ids

    def test_below_threshold_removed(self):
        """Segment below threshold is removed."""
        input_ids = [0] * 20 + [1] * 9 + [0] * 20
        result = debounce_speaker_ids(input_ids, min_hold_frames=10)
        assert result == [0] * 49


class TestDebouncePositioning:
    """Tests for flicker at different positions."""

    def test_flicker_at_start(self):
        """Short flicker at sequence start uses next stable speaker."""
        input_ids = [1] * 3 + [0] * 50
        result = debounce_speaker_ids(input_ids, min_hold_frames=10)
        assert result == [0] * 53

    def test_flicker_at_end(self):
        """Short flicker at sequence end uses previous stable speaker."""
        input_ids = [0] * 50 + [1] * 3
        result = debounce_speaker_ids(input_ids, min_hold_frames=10)
        assert result == [0] * 53

    def test_flicker_in_middle(self):
        """Short flicker in middle uses previous stable speaker."""
        input_ids = [0] * 30 + [1] * 5 + [0] * 30
        result = debounce_speaker_ids(input_ids, min_hold_frames=10)
        assert result == [0] * 65

    def test_flicker_between_two_speakers(self):
        """Short flicker between two different stable speakers."""
        input_ids = [0] * 30 + [2] * 4 + [1] * 30
        result = debounce_speaker_ids(input_ids, min_hold_frames=10)
        # 4 frames of speaker 2 is below threshold, replaced by previous (0)
        assert result == [0] * 34 + [1] * 30


class TestDebounceMultipleFlickers:
    """Tests for multiple flicker segments."""

    def test_consecutive_flickers(self):
        """Multiple short flickers are all removed."""
        input_ids = [0] * 20 + [1] * 3 + [0] * 10 + [2] * 2 + [0] * 20
        result = debounce_speaker_ids(input_ids, min_hold_frames=5)
        assert result == [0] * 55

    def test_separate_flickers(self):
        """Multiple separated short flickers are removed independently."""
        input_ids = [0] * 20 + [1] * 3 + [0] * 40 + [2] * 4 + [0] * 20
        result = debounce_speaker_ids(input_ids, min_hold_frames=10)
        assert result == [0] * 87

    def test_mixed_stable_and_flickers(self):
        """Stable segments preserved, flickers removed."""
        input_ids = [0] * 50 + [1] * 2 + [0] * 30 + [2] * 20 + [1] * 3
        result = debounce_speaker_ids(input_ids, min_hold_frames=5)
        # First [1]*2 is flicker, removed
        # [1]*3 at end is flicker, replaced with previous (2)
        assert result == [0] * 82 + [2] * 20 + [2] * 3


class TestDebounceWithNone:
    """Tests for None handling in debouncing."""

    def test_none_between_speakers(self):
        """None segments are preserved between speakers."""
        input_ids = [0] * 20 + [None] * 5 + [1] * 20
        result = debounce_speaker_ids(input_ids, min_hold_frames=10)
        assert result == input_ids

    def test_none_around_flicker(self):
        """None around a flicker doesn't affect removal."""
        input_ids = [None] * 5 + [0] * 20 + [1] * 3 + [0] * 20
        result = debounce_speaker_ids(input_ids, min_hold_frames=10)
        assert result == [None] * 5 + [0] * 43

    def test_flicker_before_none(self):
        """Flicker followed by None uses previous speaker."""
        input_ids = [0] * 20 + [1] * 3 + [None] * 10
        result = debounce_speaker_ids(input_ids, min_hold_frames=10)
        # The [1]*3 flicker should be replaced by 0
        assert result == [0] * 23 + [None] * 10

    def test_flicker_after_none(self):
        """Flicker after None uses next stable speaker."""
        input_ids = [None] * 10 + [1] * 3 + [0] * 20
        result = debounce_speaker_ids(input_ids, min_hold_frames=10)
        # The [1]*3 flicker should be replaced by 0
        assert result == [None] * 10 + [0] * 23

    def test_only_none_before_flicker_at_start(self):
        """Flicker at start with only None before it uses next speaker."""
        input_ids = [None] * 5 + [2] * 2 + [0] * 30
        result = debounce_speaker_ids(input_ids, min_hold_frames=5)
        # [2]*2 is flicker, use next stable which is 0
        assert result == [None] * 5 + [0] * 32


class TestDebounceThresholds:
    """Tests for different threshold values."""

    def test_min_hold_frames_2(self):
        """min_hold_frames=2 means only 1-frame segments removed."""
        input_ids = [0] * 20 + [1] + [0] * 20
        result = debounce_speaker_ids(input_ids, min_hold_frames=2)
        assert result == [0] * 41

    def test_min_hold_frames_large(self):
        """Large threshold removes more segments."""
        input_ids = [0] * 20 + [1] * 15 + [0] * 20
        result = debounce_speaker_ids(input_ids, min_hold_frames=20)
        # [1]*15 is below 20, removed
        assert result == [0] * 55

    def test_high_threshold_preserves_long_segments(self):
        """Segments longer than high threshold are preserved."""
        input_ids = [0] * 20 + [1] * 100 + [0] * 20
        result = debounce_speaker_ids(input_ids, min_hold_frames=50)
        assert result == [1] * 140


class TestDebounceLength:
    """Tests that output length matches input length."""

    def test_output_length_matches_input(self):
        """Output list is always same length as input."""
        test_cases = [
            [0] * 50,
            [0] * 50 + [1] * 50,
            [0] * 20 + [1] * 3 + [0] * 30,
            [None] * 20 + [0] * 20,
        ]
        for input_ids in test_cases:
            result = debounce_speaker_ids(input_ids, min_hold_frames=5)
            assert len(result) == len(input_ids)


class TestDebounceEdgeCases:
    """Edge case tests."""

    def test_min_hold_frames_zero(self):
        """min_hold_frames=0 removes all short segments (none removed)."""
        input_ids = [0] * 20 + [1] * 5 + [0] * 20
        result = debounce_speaker_ids(input_ids, min_hold_frames=0)
        # Everything is >= 0 frames, so nothing removed
        assert result == input_ids

    def test_alternating_speakers(self):
        """Alternating speakers with short holds."""
        input_ids = [0, 1, 0, 1, 0, 1] * 10
        result = debounce_speaker_ids(input_ids, min_hold_frames=5)
        # Each segment is 1 frame, all removed, collapse to first speaker
        assert all(x == result[0] for x in result if x is not None)

    def test_very_long_sequence(self):
        """Very long sequence with multiple flickers."""
        input_ids = [0] * 1000 + [1] * 2 + [0] * 1000
        result = debounce_speaker_ids(input_ids, min_hold_frames=5)
        assert result == [0] * 2002

    def test_all_different_speakers(self):
        """All different single-frame speakers."""
        input_ids = list(range(50))
        result = debounce_speaker_ids(input_ids, min_hold_frames=2)
        # All segments are 1 frame, all removed
        assert len(result) == 50
        # All should be replaced with first stable (or nearest)

    def test_mixed_none_and_speakers(self):
        """Complex mix of None and speaker segments."""
        input_ids = [None, 0, 0, None, 1, 1, 1, None, 2]
        result = debounce_speaker_ids(input_ids, min_hold_frames=2)
        # [0]*2 is stable, [1]*3 is stable, [2]*1 is flicker (use previous)
        assert len(result) == len(input_ids)
