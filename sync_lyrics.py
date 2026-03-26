#!/usr/bin/env python3
"""
Lyrics Sync Tool - Detects when each line is sung using Whisper word-level timestamps.
Uses sequential word matching (not segment matching) for much better accuracy.

Usage:
    python3 sync_lyrics.py --audio "I Will Stand in the Light.mp3"
    python3 sync_lyrics.py --audio "I Will Stand in the Light.mp3" --model medium  (more accurate)

This creates 'timestamps.json'. You can edit it to fine-tune, then run:
    python3 generate_video_synced.py --audio "I Will Stand in the Light.mp3"

Requirements:
    pip3 install openai-whisper torch
    brew install ffmpeg
"""

import argparse
import json
import os
import re
import string

LYRICS_LINES = [
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


def clean_word(w):
    """Normalize a word for matching."""
    return re.sub(r'[^a-z\']', '', w.lower().strip())


def extract_all_words(result):
    """Extract every word with its timestamp from Whisper output."""
    words = []
    for seg in result["segments"]:
        if "words" not in seg:
            continue
        for w in seg["words"]:
            cleaned = clean_word(w["word"])
            if cleaned:
                words.append({
                    "word": cleaned,
                    "start": w["start"],
                    "end": w["end"],
                    "raw": w["word"].strip(),
                })
    return words


def align_lyrics_to_words(whisper_words):
    """
    Sequentially align each lyric line to whisper words.
    Walks through whisper words in order, matching each lyric line's words
    in sequence. This ensures:
    - Every lyric line gets a timestamp
    - Lines are in the correct order
    - Repeated lines (like chorus) get matched to the right occurrence
    """
    timestamps = []
    word_cursor = 0  # current position in whisper_words

    for section, lyric_text in LYRICS_LINES:
        lyric_words = [clean_word(w) for w in lyric_text.split() if clean_word(w)]

        if not lyric_words:
            continue

        # Try to find these words starting from word_cursor
        best_start_idx = None
        best_end_idx = None
        best_score = 0

        # Search window: from cursor to cursor + 200 words ahead
        search_end = min(len(whisper_words), word_cursor + 300)

        for start_pos in range(word_cursor, search_end):
            # Try to match lyric words starting at this position
            matched = 0
            last_matched_pos = start_pos
            pos = start_pos

            for lw in lyric_words:
                # Look for this lyric word within a small window from current pos
                found = False
                for offset in range(0, 5):  # allow skipping up to 4 whisper words
                    check_pos = pos + offset
                    if check_pos >= len(whisper_words):
                        break
                    if whisper_words[check_pos]["word"] == lw:
                        matched += 1
                        last_matched_pos = check_pos
                        pos = check_pos + 1
                        found = True
                        break
                if not found:
                    # Try fuzzy: check if whisper word starts with or contains lyric word
                    for offset in range(0, 5):
                        check_pos = pos + offset
                        if check_pos >= len(whisper_words):
                            break
                        ww = whisper_words[check_pos]["word"]
                        if lw in ww or ww in lw or (len(lw) > 3 and lw[:3] == ww[:3]):
                            matched += 0.7
                            last_matched_pos = check_pos
                            pos = check_pos + 1
                            found = True
                            break
                    if not found:
                        pos += 1  # skip and continue

            score = matched / len(lyric_words)

            # Prefer matches closer to cursor (sequential order)
            proximity_bonus = max(0, 1.0 - (start_pos - word_cursor) * 0.005)
            adjusted_score = score * 0.7 + proximity_bonus * 0.3

            if score >= 0.4 and adjusted_score > best_score:
                best_score = adjusted_score
                best_start_idx = start_pos
                best_end_idx = last_matched_pos

        if best_start_idx is not None and best_end_idx is not None:
            start_time = whisper_words[best_start_idx]["start"]
            end_time = whisper_words[best_end_idx]["end"]

            timestamps.append({
                "section": section,
                "text": lyric_text,
                "start": round(start_time, 2),
                "end": round(end_time, 2),
                "confidence": round(best_score, 2),
            })

            # Move cursor past the matched words
            word_cursor = best_end_idx + 1
        else:
            # Could not match - will interpolate later
            timestamps.append({
                "section": section,
                "text": lyric_text,
                "start": None,
                "end": None,
                "confidence": 0,
            })

    # Interpolate any missing timestamps
    _interpolate_gaps(timestamps)

    return timestamps


def _interpolate_gaps(timestamps):
    """Fill in missing timestamps by interpolating between known ones."""
    # First pass: forward fill
    last_end = 0.0
    for i, ts in enumerate(timestamps):
        if ts["start"] is not None:
            last_end = ts["end"]
            continue

        # Find next known timestamp
        next_start = last_end + 20.0  # fallback
        for j in range(i + 1, len(timestamps)):
            if timestamps[j]["start"] is not None:
                next_start = timestamps[j]["start"]
                break

        # Count consecutive gaps
        gap_count = 0
        for j in range(i, len(timestamps)):
            if timestamps[j]["start"] is None:
                gap_count += 1
            else:
                break

        # Distribute time evenly
        gap_duration = next_start - last_end
        interval = gap_duration / (gap_count + 1)

        for j in range(gap_count):
            idx = i + j
            if timestamps[idx]["start"] is None:
                timestamps[idx]["start"] = round(last_end + interval * (j + 1), 2)
                timestamps[idx]["end"] = round(timestamps[idx]["start"] + min(interval * 0.8, 2.5), 2)
                timestamps[idx]["confidence"] = 0.0
                timestamps[idx]["interpolated"] = True

        last_end = timestamps[i + gap_count - 1]["end"] if gap_count > 0 else last_end


def main():
    parser = argparse.ArgumentParser(description="Sync lyrics to audio using Whisper")
    parser.add_argument("--audio", type=str, required=True, help="Path to audio file")
    parser.add_argument("--output", type=str, default="timestamps.json", help="Output timestamps file")
    parser.add_argument("--model", type=str, default="base",
                        help="Whisper model: tiny, base, small, medium, large (bigger = more accurate but slower)")
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

    print(f"Transcribing '{args.audio}' with word-level timestamps...")
    print("This may take a few minutes...")
    result = model.transcribe(args.audio, word_timestamps=True)

    # Extract all words
    all_words = extract_all_words(result)
    print(f"\nWhisper detected {len(all_words)} words across {len(result['segments'])} segments")

    # Show what Whisper heard (for debugging)
    print("\n--- What Whisper heard (first 200 words) ---")
    preview = " ".join(w["raw"] for w in all_words[:200])
    print(preview)
    print("---\n")

    print("Aligning lyrics to detected words...")
    timestamps = align_lyrics_to_words(all_words)

    # Save
    with open(args.output, "w") as f:
        json.dump(timestamps, f, indent=2)

    matched = sum(1 for t in timestamps if t["confidence"] > 0)
    interpolated = sum(1 for t in timestamps if t.get("interpolated"))
    total = len(timestamps)

    print(f"\nResults:")
    print(f"  Matched:      {matched} / {total} lines")
    print(f"  Interpolated: {interpolated} lines (estimated timing)")
    print(f"  Total:        {total} lines")

    # Show timeline
    print(f"\n--- Sync Timeline ---")
    current_section = None
    for ts in timestamps:
        if ts["section"] != current_section:
            current_section = ts["section"]
            print(f"\n  [{current_section}]")
        marker = "*" if ts.get("interpolated") else " "
        conf = f"{ts['confidence']:.0%}" if ts["confidence"] > 0 else "est."
        print(f"  {marker} {ts['start']:6.1f}s - {ts['end']:6.1f}s  ({conf:>4})  {ts['text']}")

    print(f"\nTimestamps saved to: {args.output}")

    if interpolated > 0:
        print(f"\nLines marked with * have estimated timing.")
        print(f"You can edit {args.output} to adjust start/end times (in seconds).")
        print(f"Tip: Use --model medium or --model small for better accuracy.")

    print(f"\nNext step:")
    print(f'  python3 generate_video_synced.py --audio "{args.audio}"')


if __name__ == "__main__":
    main()
