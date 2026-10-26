"""Summarize missing observations for manual review, without inferring events."""
from collections import Counter
from math import isfinite


def tracking_gaps(records: list[dict]) -> list[dict]:
    previous = None
    for row in records:
        time = row['timestamp_seconds']
        if not isfinite(time) or time < 0:
            raise ValueError('Review requires finite nonnegative source timestamps.')
        if previous is not None and (row['frame_index'] != previous['frame_index'] + 1 or
                                     time <= previous['timestamp_seconds']):
            raise ValueError('Review requires consecutive frames with increasing source time.')
        if (row['status'] == 'observed') != (row['observation'] is not None):
            raise ValueError('Only observed records can carry an observation.')
        previous = row
    gaps = []
    index = 0
    while index < len(records):
        if records[index]['observation'] is not None:
            index += 1
            continue
        start = index
        while index < len(records) and records[index]['observation'] is None:
            index += 1
        first, last = records[start], records[index - 1]
        before = records[start - 1] if start else None
        after = records[index] if index < len(records) else None
        position = ('between_observations' if before and after else 'clip_start' if after
                    else 'clip_end' if before else 'entire_clip')
        gaps.append(dict(start_frame=first['frame_index'], end_frame=last['frame_index'],
                         start_seconds=first['timestamp_seconds'], end_seconds=last['timestamp_seconds'],
                         frame_count=index - start, position=position,
                         previous_track_id=before['track_id'] if before else None,
                         next_track_id=after['track_id'] if after else None,
                         resume_seconds=after['timestamp_seconds'] if after else None,
                         status_counts=dict(Counter(row['status'] for row in records[start:index]))))
    return gaps
