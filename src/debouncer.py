"""
Speaker ID debouncing for stable camera tracking.

Removes rapid speaker-ID bounces that cause jarring crop window snaps.
"""


def debounce_speaker_ids(speaker_track_ids, min_hold_frames=15):
    """
    Remove rapid speaker-ID bounces shorter than min_hold_frames.

    Speaker detection sometimes flickers the active-speaker label during
    crosstalk or brief classification uncertainty, producing 1-10 frame
    segments that cause jarring rapid-fire crop snaps. This pre-filter
    replaces those short segments with the surrounding stable speaker ID
    so the downstream dead-zone tracker never sees them.

    Algorithm:
      1. Run-length encode the raw IDs into (track_id, start, length) runs.
      2. For any run shorter than min_hold_frames, replace it with the
         previous stable run's ID (or the next stable run if it's the first).
      3. Expand back to a per-frame list.

    Args:
        speaker_track_ids: Per-frame list of speaker IDs (int or None).
            None means no speaker detected at that frame.
        min_hold_frames: Minimum frames a speaker must hold to be "stable".

    Returns:
        Same-length list with short flicker runs replaced by nearest stable ID.
        None segments are never modified.

    Examples:
        >>> debounce_speaker_ids([0]*50 + [1]*3 + [0]*50, min_hold_frames=10)
        [0]*103  # The 3-frame speaker-1 segment is replaced by speaker 0

        >>> debounce_speaker_ids([None]*10 + [0]*50, min_hold_frames=15)
        [None]*10 + [0]*50  # None segments are untouched
    """
    if not speaker_track_ids:
        return speaker_track_ids
    
    def run_length_encode(speaker_track_ids):
        
        current_track_id = speaker_track_ids[0]
        frame_start = 0
        
        compressed = []
        for idx in range(1, len(speaker_track_ids)):
            track_id = speaker_track_ids[idx]
            if track_id != current_track_id:
                length = idx-frame_start
                compressed.append([current_track_id, frame_start, length])
                
                frame_start = idx
                current_track_id = track_id
        
        compressed.append([current_track_id, frame_start, len(speaker_track_ids)-frame_start])
        return compressed
    
    compressed = run_length_encode(speaker_track_ids)
    first_unstable_ids = []
    prev_stable_id = None

    for i in range(len(compressed)):
        track_id, start, length = compressed[i]
        if track_id == None:
            continue
        
        # If no stable frames have been found
        if length < min_hold_frames and prev_stable_id == None:
            first_unstable_ids.append(i)
            continue
        
        if length < min_hold_frames:
            compressed[i][0] = prev_stable_id
        else:
            if not prev_stable_id:
                for unstable_frame in first_unstable_ids:
                    first_unstable_ids.pop(0)
                    compressed[unstable_frame][0] = track_id
            
            prev_stable_id = track_id

    # Compress to first speaker
    if first_unstable_ids:
        return [speaker_track_ids[0]] * len(speaker_track_ids)
    
    # Unpacking RLE
    debounced_speaker_track_ids = []
    for track_id, _, length in compressed:
        for _ in range(length):
            debounced_speaker_track_ids.append(track_id)
    
    return debounced_speaker_track_ids     