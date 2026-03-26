#!/usr/bin/env python3
"""
Lyrics Sync Tool - Detects when each line is sung in the audio using Whisper.
Generates a timestamps file that the video generator uses for perfect sync.

Usage:
    python3 sync_lyrics.py --audio "I Will Stand in the Light.mp3"

This will create a file called 'timestamps.json' with the timing for each line.
You can then edit timestamps.json to fine-tune any timing, and run:
    python3 generate_video_synced.py --audio "I Will Stand in the Light.mp3"

Requirements:
    pip3 install openai-whisper torch
    brew install ffmpeg
"""

import argparse
import json
import os
import sys

LYRICS_LINES = [
    # (section, line)
    ("Intro", "This fear is real"),
    ("Intro", "This night is long"),
    ("Intro", "But something deeper calls me on"),

    ("Verse 1", "Monday morning waits before me"),
    ("Verse 1", "Like a mountain made of stone"),
    ("Verse 1", "And I feel the weight of worry"),
    ("Verse 1", "Like I have to stand alone"),
    ("Verse 1", "But somewhere underneath the shaking"),
    ("Verse 1", "Under all the fear I feel"),
    ("Verse 1", "There is something still unbroken"),
    ("Verse 1", "There is something steady, real"),

    ("Pre-Chorus", "So when the dark comes close"),
    ("Pre-Chorus", "And the worst begins to speak"),
    ("Pre-Chorus", "I will listen for the deeper voice"),
    ("Pre-Chorus", "That tells my soul to keep"),

    ("Chorus", "I will stand in the light"),
    ("Chorus", "Even when my heart is afraid"),
    ("Chorus", "Even when the road is uncertain"),
    ("Chorus", "Even when my courage shakes"),
    ("Chorus", "I am more than this fear"),
    ("Chorus", "I am more than this pain"),
    ("Chorus", "And whatever waits before me"),
    ("Chorus", "Will not take my faith away"),
    ("Chorus", "This trial may test me"),
    ("Chorus", "But it will not erase me"),
    ("Chorus", "I will stand in the light"),

    ("Verse 2", "I do not need to know the ending"),
    ("Verse 2", "To take the next right breath"),
    ("Verse 2", "I do not need to feel unbroken"),
    ("Verse 2", "To keep walking through the test"),
    ("Verse 2", "There is strength inside the trembling"),
    ("Verse 2", "There is hope inside the strain"),
    ("Verse 2", "And the soul that has survived so much"),
    ("Verse 2", "Can rise again, again"),

    ("Pre-Chorus", "So if my hands are shaking"),
    ("Pre-Chorus", "That does not mean I fall"),
    ("Pre-Chorus", "It means I'm human in the moment"),
    ("Pre-Chorus", "And still answering the call"),

    ("Chorus", "I will stand in the light"),
    ("Chorus", "Even when my heart is afraid"),
    ("Chorus", "Even when the road is uncertain"),
    ("Chorus", "Even when my courage shakes"),
    ("Chorus", "I am more than this fear"),
    ("Chorus", "I am more than this pain"),
    ("Chorus", "And whatever waits before me"),
    ("Chorus", "Will not take my faith away"),
    ("Chorus", "This trial may test me"),
    ("Chorus", "But it will not erase me"),
    ("Chorus", "I will stand in the light"),

    ("Bridge", "Let truth be louder than panic"),
    ("Bridge", "Let peace be stronger than dread"),
    ("Bridge", "Let every thought that rises against me"),
    ("Bridge", "Lose its power in my head"),
    ("Bridge", "I have walked through fire before this"),
    ("Bridge", "I have made it through the strain"),
    ("Bridge", "And I will not give this moment"),
    ("Bridge", "More power than my name"),
    ("Bridge", "So breathe, my soul, breathe slowly"),
    ("Bridge", "Stand, my heart, stand tall"),
    ("Bridge", "The night may speak in thunder"),
    ("Bridge", "But it does not speak for all"),

    ("Final Chorus", "I will stand in the light"),
    ("Final Chorus", "Even when my heart is afraid"),
    ("Final Chorus", "Even when the road is uncertain"),
    ("Final Chorus", "Even when my courage shakes"),
    ("Final Chorus", "I am more than this fear"),
    ("Final Chorus", "I am more than this pain"),
    ("Final Chorus", "And whatever waits before me"),
    ("Final Chorus", "Will not take my faith away"),
    ("Final Chorus", "This trial may test me"),
    ("Final Chorus", "But it will not erase me"),
    ("Final Chorus", "I will stand in the light"),

    ("Outro", "This fear is real"),
    ("Outro", "But it is not my master"),
    ("Outro", "Morning is coming"),
    ("Outro", "And I will meet it standing"),
]


def fuzzy_match(whisper_text, lyric_text):
    """Simple fuzzy matching between whisper output and expected lyrics."""
    w = whisper_text.lower().strip().strip(".,!?'\"")
    l = lyric_text.lower().strip().strip(".,!?'\"")

    # Exact match
    if w == l:
        return 1.0

    # Check if one contains the other
    if w in l or l in w:
        return 0.8

    # Word overlap
    w_words = set(w.split())
    l_words = set(l.split())
    if not l_words:
        return 0.0
    overlap = len(w_words & l_words) / len(l_words)
    return overlap


def align_whisper_to_lyrics(segments):
    """Align Whisper segments to our known lyrics using fuzzy matching."""
    timestamps = []
    lyric_idx = 0

    # Combine all whisper words with their timestamps
    whisper_lines = []
    for seg in segments:
        whisper_lines.append({
            "text": seg["text"].strip(),
            "start": seg["start"],
            "end": seg["end"],
        })

    # For each lyric line, find the best matching whisper segment
    used_segments = set()

    for lyric_idx, (section, lyric_text) in enumerate(LYRICS_LINES):
        best_score = 0
        best_seg_idx = None
        best_start = None
        best_end = None

        # Search through whisper segments
        for si, seg in enumerate(whisper_lines):
            if si in used_segments:
                continue
            score = fuzzy_match(seg["text"], lyric_text)

            # Also try combining consecutive segments
            if si + 1 < len(whisper_lines) and si + 1 not in used_segments:
                combined = seg["text"] + " " + whisper_lines[si + 1]["text"]
                combined_score = fuzzy_match(combined, lyric_text)
                if combined_score > score:
                    score = combined_score

            if score > best_score:
                best_score = score
                best_seg_idx = si
                best_start = seg["start"]
                best_end = seg["end"]

        if best_score >= 0.3 and best_seg_idx is not None:
            used_segments.add(best_seg_idx)
            timestamps.append({
                "section": section,
                "text": lyric_text,
                "start": round(best_start, 2),
                "end": round(best_end, 2),
                "confidence": round(best_score, 2),
            })
        else:
            # No match found - will need manual timing
            timestamps.append({
                "section": section,
                "text": lyric_text,
                "start": None,
                "end": None,
                "confidence": 0,
                "NOTE": "COULD NOT AUTO-DETECT - please set start/end manually",
            })

    # Fill in gaps: interpolate missing timestamps
    last_good_time = 0
    for i, ts in enumerate(timestamps):
        if ts["start"] is not None:
            last_good_time = ts["start"]
        else:
            # Look ahead for next good timestamp
            next_good_time = last_good_time + 3.0
            for j in range(i + 1, len(timestamps)):
                if timestamps[j]["start"] is not None:
                    next_good_time = timestamps[j]["start"]
                    break
            # Count how many gaps
            gap_count = 0
            for j in range(i, len(timestamps)):
                if timestamps[j]["start"] is None:
                    gap_count += 1
                else:
                    break
            # Interpolate
            interval = (next_good_time - last_good_time) / (gap_count + 1)
            ts["start"] = round(last_good_time + interval, 2)
            ts["end"] = round(ts["start"] + 2.0, 2)
            last_good_time = ts["start"]

    return timestamps


def main():
    parser = argparse.ArgumentParser(description="Sync lyrics to audio using Whisper")
    parser.add_argument("--audio", type=str, required=True, help="Path to audio file")
    parser.add_argument("--output", type=str, default="timestamps.json", help="Output timestamps file")
    parser.add_argument("--model", type=str, default="base", help="Whisper model: tiny, base, small, medium, large")
    args = parser.parse_args()

    if not os.path.exists(args.audio):
        print(f"ERROR: Audio file not found: {args.audio}")
        return

    try:
        import whisper
    except ImportError:
        print("Whisper not installed. Installing now...")
        os.system("pip3 install openai-whisper torch")
        import whisper

    print(f"Loading Whisper model '{args.model}'...")
    print("(First time may download the model - this is normal)")
    model = whisper.load_model(args.model)

    print(f"Transcribing '{args.audio}'...")
    print("This may take a few minutes depending on the song length...")
    result = model.transcribe(args.audio, word_timestamps=True)

    print(f"\nWhisper detected {len(result['segments'])} segments")
    print("\nAligning to lyrics...")

    timestamps = align_whisper_to_lyrics(result["segments"])

    # Save timestamps
    with open(args.output, "w") as f:
        json.dump(timestamps, f, indent=2)

    print(f"\nTimestamps saved to: {args.output}")
    print(f"\nMatched {sum(1 for t in timestamps if t['confidence'] > 0)} / {len(timestamps)} lines")

    # Show results
    unmatched = [t for t in timestamps if t["confidence"] == 0]
    if unmatched:
        print(f"\n{len(unmatched)} lines need manual timing:")
        for t in unmatched:
            print(f"  - \"{t['text']}\"")

    print(f"\nYou can now edit {args.output} to fine-tune any timing.")
    print("Then run:")
    print(f'  python3 generate_video_synced.py --audio "{args.audio}"')


if __name__ == "__main__":
    main()
