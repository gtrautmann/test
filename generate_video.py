#!/usr/bin/env python3
"""
Lyrics Video Generator for "I Will Stand in the Light"
Generates an .mp4 video with animated lyrics over a dark background.

Usage:
    python3 generate_video.py --audio song.mp3
    python3 generate_video.py --audio song.mp3 --output my_video.mp4
    python3 generate_video.py  (no audio, generates lyrics-only video)

Requirements:
    pip3 install pillow
    brew install ffmpeg
"""

import argparse
import os
import subprocess
import shutil
import tempfile
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
WIDTH = 1920
HEIGHT = 1080
FPS = 30
BG_COLOR = (10, 10, 26)
FADE_FRAMES = int(0.8 * FPS)  # frames to fade in a line

SECTION_COLORS = {
    "Intro": (144, 184, 240),
    "Verse": (208, 216, 232),
    "Pre-Chorus": (184, 160, 224),
    "Chorus": (240, 192, 64),
    "Bridge": (224, 112, 64),
    "Final Chorus": (240, 192, 64),
    "Outro": (144, 184, 240),
}

LYRICS = [
    {
        "section": "Intro",
        "lines": [
            "This fear is real",
            "This night is long",
            "But something deeper calls me on",
        ],
    },
    {
        "section": "Verse 1",
        "lines": [
            "Monday morning waits before me",
            "Like a mountain made of stone",
            "And I feel the weight of worry",
            "Like I have to stand alone",
            "",
            "But somewhere underneath the shaking",
            "Under all the fear I feel",
            "There is something still unbroken",
            "There is something steady, real",
        ],
    },
    {
        "section": "Pre-Chorus",
        "lines": [
            "So when the dark comes close",
            "And the worst begins to speak",
            "I will listen for the deeper voice",
            "That tells my soul to keep",
        ],
    },
    {
        "section": "Chorus",
        "lines": [
            "I will stand in the light",
            "Even when my heart is afraid",
            "Even when the road is uncertain",
            "Even when my courage shakes",
            "",
            "I am more than this fear",
            "I am more than this pain",
            "And whatever waits before me",
            "Will not take my faith away",
            "",
            "This trial may test me",
            "But it will not erase me",
            "I will stand in the light",
        ],
    },
    {
        "section": "Verse 2",
        "lines": [
            "I do not need to know the ending",
            "To take the next right breath",
            "I do not need to feel unbroken",
            "To keep walking through the test",
            "",
            "There is strength inside the trembling",
            "There is hope inside the strain",
            "And the soul that has survived so much",
            "Can rise again, again",
        ],
    },
    {
        "section": "Pre-Chorus",
        "lines": [
            "So if my hands are shaking",
            "That does not mean I fall",
            "It means I'm human in the moment",
            "And still answering the call",
        ],
    },
    {
        "section": "Chorus",
        "lines": [
            "I will stand in the light",
            "Even when my heart is afraid",
            "Even when the road is uncertain",
            "Even when my courage shakes",
            "",
            "I am more than this fear",
            "I am more than this pain",
            "And whatever waits before me",
            "Will not take my faith away",
            "",
            "This trial may test me",
            "But it will not erase me",
            "I will stand in the light",
        ],
    },
    {
        "section": "Bridge",
        "lines": [
            "Let truth be louder than panic",
            "Let peace be stronger than dread",
            "Let every thought that rises against me",
            "Lose its power in my head",
            "",
            "I have walked through fire before this",
            "I have made it through the strain",
            "And I will not give this moment",
            "More power than my name",
            "",
            "So breathe, my soul, breathe slowly",
            "Stand, my heart, stand tall",
            "The night may speak in thunder",
            "But it does not speak for all",
        ],
    },
    {
        "section": "Final Chorus",
        "lines": [
            "I will stand in the light",
            "Even when my heart is afraid",
            "Even when the road is uncertain",
            "Even when my courage shakes",
            "",
            "I am more than this fear",
            "I am more than this pain",
            "And whatever waits before me",
            "Will not take my faith away",
            "",
            "This trial may test me",
            "But it will not erase me",
            "I will stand in the light",
        ],
    },
    {
        "section": "Outro",
        "lines": [
            "This fear is real",
            "But it is not my master",
            "Morning is coming",
            "And I will meet it standing",
        ],
    },
]


def get_section_color(section):
    for key, color in SECTION_COLORS.items():
        if key in section:
            return color
    return (208, 216, 232)


def get_font(size, bold=False):
    """Try to load a nice font, fall back to default."""
    font_paths = [
        # macOS fonts
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/Library/Fonts/Georgia Bold.ttf" if bold else "/Library/Fonts/Georgia.ttf",
        # Linux fonts
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def build_timeline():
    """Build a flat list of timed events (section headers + lyric lines)."""
    timeline = []
    t = 2.0  # start after 2 seconds

    for block in LYRICS:
        section = block["section"]
        # Section header
        timeline.append({
            "type": "section",
            "text": section,
            "start": t,
            "color": get_section_color(section),
        })
        t += 1.0

        for line in block["lines"]:
            if line == "":
                t += 0.6
                continue
            timeline.append({
                "type": "line",
                "text": line,
                "start": t,
                "section": section,
                "color": get_section_color(section),
            })
            t += 2.5

        t += 1.5  # pause between sections

    # Add ending
    timeline.append({
        "type": "end",
        "text": "I Will Stand in the Light",
        "start": t + 1.0,
        "color": (240, 192, 64),
    })
    total_duration = t + 5.0
    return timeline, total_duration


def render_frame(frame_num, timeline, title_font, section_font, line_font, small_font):
    """Render a single frame."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    current_time = frame_num / FPS

    # Title screen (first 2 seconds)
    if current_time < 2.0:
        alpha = min(1.0, current_time / 1.5)
        color = tuple(int(c * alpha) for c in (240, 192, 64))
        text = "I Will Stand in the Light"
        bbox = draw.textbbox((0, 0), text, font=title_font)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, HEIGHT // 2 - 40), text, fill=color, font=title_font)
        return img

    # Collect visible lines
    visible = []
    for event in timeline:
        if event["start"] > current_time:
            break
        if event["type"] == "end" and current_time >= event["start"]:
            # Ending title
            alpha = min(1.0, (current_time - event["start"]) / 1.5)
            color = tuple(int(c * alpha) for c in event["color"])
            text = event["text"]
            bbox = draw.textbbox((0, 0), text, font=title_font)
            tw = bbox[2] - bbox[0]
            draw.text(((WIDTH - tw) // 2, HEIGHT // 2 - 40), text, fill=color, font=title_font)
            return img
        visible.append(event)

    if not visible:
        return img

    # Find the current section for the badge
    current_section = None
    for event in reversed(visible):
        if event["type"] == "section":
            current_section = event
            break

    # Calculate layout - show recent lines centered vertically
    display_items = []
    for event in visible:
        elapsed = current_time - event["start"]
        fade = min(1.0, elapsed / (FADE_FRAMES / FPS))
        display_items.append({**event, "fade": fade, "elapsed": elapsed})

    # Keep last ~10 visible lines to avoid overcrowding
    line_items = [d for d in display_items if d["type"] == "line"]
    if len(line_items) > 10:
        line_items = line_items[-10:]

    # Draw section badge at top
    if current_section:
        badge_text = current_section["text"].upper()
        badge_fade = min(1.0, (current_time - current_section["start"]) / 0.5)
        badge_color = tuple(int(c * badge_fade) for c in current_section["color"])
        bbox = draw.textbbox((0, 0), badge_text, font=section_font)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, 60), badge_text, fill=badge_color, font=section_font)

    # Draw lyrics
    line_height = 65
    total_height = len(line_items) * line_height
    start_y = (HEIGHT - total_height) // 2 + 20

    for i, item in enumerate(line_items):
        y = start_y + i * line_height
        fade = item["fade"]
        is_latest = (i == len(line_items) - 1)

        if is_latest:
            # Current line: bright section color
            color = tuple(int(c * fade) for c in item["color"])
            font = line_font
        else:
            # Past lines: dimmed
            dim = max(0.3, 1.0 - (len(line_items) - 1 - i) * 0.1)
            base = (180, 184, 196)
            color = tuple(int(c * dim * fade) for c in base)
            font = line_font

        text = item["text"]
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]

        # Slide up effect
        offset_y = int((1.0 - fade) * 15)
        draw.text(((WIDTH - tw) // 2, y + offset_y), text, fill=color, font=font)

    # Subtle bottom text
    footer = "I Will Stand in the Light"
    footer_color = (40, 40, 60)
    bbox = draw.textbbox((0, 0), footer, font=small_font)
    tw = bbox[2] - bbox[0]
    draw.text(((WIDTH - tw) // 2, HEIGHT - 50), footer, fill=footer_color, font=small_font)

    return img


def main():
    parser = argparse.ArgumentParser(description="Generate lyrics video")
    parser.add_argument("--audio", type=str, help="Path to audio file (.mp3, .wav)")
    parser.add_argument("--output", type=str, default="i_will_stand_in_the_light.mp4", help="Output filename")
    args = parser.parse_args()

    # Check ffmpeg
    if not shutil.which("ffmpeg"):
        print("ERROR: ffmpeg not found. Install it with: brew install ffmpeg")
        return

    print("Building timeline...")
    timeline, duration = build_timeline()

    # If audio provided, use audio duration
    if args.audio:
        if not os.path.exists(args.audio):
            print(f"ERROR: Audio file not found: {args.audio}")
            return
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", args.audio],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            audio_duration = float(result.stdout.strip())
            if audio_duration > duration:
                duration = audio_duration
            print(f"Audio duration: {audio_duration:.1f}s")

    total_frames = int(duration * FPS)
    print(f"Video duration: {duration:.1f}s ({total_frames} frames)")
    print("Loading fonts...")

    title_font = get_font(64, bold=True)
    section_font = get_font(22, bold=True)
    line_font = get_font(44)
    small_font = get_font(18)

    # Render frames and pipe to ffmpeg
    print("Rendering video...")
    tmpdir = tempfile.mkdtemp()

    try:
        # Build ffmpeg command
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{WIDTH}x{HEIGHT}",
            "-pix_fmt", "rgb24",
            "-r", str(FPS),
            "-i", "-",
        ]

        if args.audio:
            ffmpeg_cmd.extend(["-i", args.audio])
            ffmpeg_cmd.extend(["-c:a", "aac", "-b:a", "192k"])

        ffmpeg_cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-shortest" if args.audio else "-t", str(duration) if not args.audio else "",
            args.output,
        ])

        # Clean up empty strings
        ffmpeg_cmd = [c for c in ffmpeg_cmd if c]

        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        for frame_num in range(total_frames):
            img = render_frame(frame_num, timeline, title_font, section_font, line_font, small_font)
            proc.stdin.write(img.tobytes())

            if frame_num % FPS == 0:
                pct = int(frame_num / total_frames * 100)
                print(f"\r  Progress: {pct}% ({frame_num}/{total_frames} frames)", end="", flush=True)

        proc.stdin.close()
        proc.wait()
        print(f"\n\nDone! Video saved to: {args.output}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
