#!/usr/bin/env python3
"""
Synced Lyrics Video Generator for "I Will Stand in the Light"
Uses timestamps.json (from sync_lyrics.py) to highlight lyrics exactly when sung.

Usage:
    1. First run: python3 sync_lyrics.py --audio "I Will Stand in the Light.mp3"
    2. (Optional) Edit timestamps.json to fine-tune timing
    3. Then run: python3 generate_video_synced.py --audio "I Will Stand in the Light.mp3"

Requirements:
    pip3 install pillow
    brew install ffmpeg
"""

import argparse
import json
import math
import os
import random
import subprocess
import shutil
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
WIDTH = 1920
HEIGHT = 1080
FPS = 30
BG_COLOR = (10, 10, 26)

SECTION_COLORS = {
    "Intro": (144, 184, 240),
    "Verse": (208, 216, 232),
    "Pre-Chorus": (184, 160, 224),
    "Chorus": (240, 192, 64),
    "Bridge": (224, 112, 64),
    "Final Chorus": (240, 192, 64),
    "Outro": (144, 184, 240),
}

VISUAL_KEYWORDS = {
    "night": "stars", "dark": "stars",
    "fear": "shadows", "afraid": "shadows",
    "light": "light_rays", "stand in the light": "light_rays",
    "morning": "sunrise", "mountain": "mountain", "stone": "mountain",
    "shaking": "shake", "trembling": "shake", "courage shakes": "shake",
    "fire": "fire", "walked through fire": "fire",
    "road": "road", "heart": "heartbeat", "soul": "glow_pulse",
    "breathe": "glow_pulse", "thunder": "lightning",
    "hope": "stars_rising", "rise again": "stars_rising",
    "strength": "pulse_ring", "unbroken": "pulse_ring",
    "weight": "falling_particles", "worry": "falling_particles",
    "pain": "falling_particles", "peace": "calm_waves",
    "slowly": "calm_waves", "master": "light_rays",
    "standing": "light_rays", "faith": "light_rays",
    "erase": "dissolve", "test": "pulse_ring",
    "trial": "pulse_ring", "power": "pulse_ring",
}


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def add(self, count, style):
        for _ in range(count):
            self.particles.append({
                "x": random.randint(0, WIDTH),
                "y": random.randint(0, HEIGHT) if style != "rising" else HEIGHT + random.randint(0, 100),
                "vx": random.uniform(-0.5, 0.5),
                "vy": random.uniform(-2.0, -0.5) if style == "rising" else random.uniform(0.3, 1.5),
                "size": random.uniform(1.5, 4.0),
                "life": random.uniform(60, 150),
                "color_base": (255, 220, 150) if style == "rising" else (100, 120, 180),
                "style": style,
            })

    def update_and_draw(self, draw):
        alive = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            if p["life"] > 0 and 0 <= p["x"] <= WIDTH and -50 <= p["y"] <= HEIGHT + 50:
                alpha = min(1.0, p["life"] / 40)
                color = tuple(int(c * alpha) for c in p["color_base"])
                r = int(p["size"])
                draw.ellipse([p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r], fill=color)
                alive.append(p)
        self.particles = alive


particle_system = ParticleSystem()


def get_section_color(section):
    for key, color in SECTION_COLORS.items():
        if key in section:
            return color
    return (208, 216, 232)


def get_font(size, bold=False):
    font_paths = [
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/Library/Fonts/Georgia Bold.ttf" if bold else "/Library/Fonts/Georgia.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def detect_visual(line_text):
    text_lower = line_text.lower()
    for keyword, effect in sorted(VISUAL_KEYWORDS.items(), key=lambda x: -len(x[0])):
        if keyword in text_lower:
            return effect
    return None


# --- Visual effect functions (same as before) ---

def draw_stars(draw, t, intensity=1.0):
    rng = random.Random(12345)
    for _ in range(60):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, int(HEIGHT * 0.7))
        twinkle = 0.3 + 0.7 * abs(math.sin(t * 2 + rng.random() * 10))
        brightness = int(200 * twinkle * intensity)
        size = rng.randint(1, 3)
        draw.ellipse([x - size, y - size, x + size, y + size], fill=(brightness, brightness, int(brightness * 1.1)))


def draw_light_rays(draw, t, intensity=1.0):
    cx, cy = WIDTH // 2, HEIGHT
    for i in range(12):
        angle = (i / 12) * math.pi - math.pi / 2 + math.sin(t * 0.5) * 0.05
        length = 500 + 200 * math.sin(t * 1.5 + i)
        pulse = 0.5 + 0.5 * math.sin(t * 2 + i * 0.5)
        alpha = int(40 * pulse * intensity)
        ex = cx + math.cos(angle) * length
        ey = cy + math.sin(angle) * length
        draw.line([(cx, cy), (ex, ey)], fill=(alpha, int(alpha * 0.8), int(alpha * 0.3)), width=3)
        for offset in range(-8, 9, 4):
            ex2 = cx + math.cos(angle + offset * 0.003) * length * 0.8
            ey2 = cy + math.sin(angle + offset * 0.003) * length * 0.8
            faint = max(0, alpha // 3)
            draw.line([(cx, cy), (ex2, ey2)], fill=(faint, int(faint * 0.7), int(faint * 0.2)), width=1)


def draw_sunrise(draw, t, intensity=1.0):
    cx, cy = WIDTH // 2, HEIGHT + 100
    for r in range(400, 50, -10):
        alpha = int((1.0 - r / 400) * 60 * intensity)
        pulse = 0.8 + 0.2 * math.sin(t * 1.0)
        alpha = int(alpha * pulse)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(alpha, int(alpha * 0.6), int(alpha * 0.2)))


def draw_mountain(draw, t, intensity=1.0):
    alpha = int(60 * intensity)
    color = (20 + alpha // 4, 20 + alpha // 6, 30 + alpha // 3)
    peaks = [(0, HEIGHT), (200, HEIGHT - 200), (400, HEIGHT - 350), (600, HEIGHT - 280),
             (800, HEIGHT - 420), (960, HEIGHT - 500), (1120, HEIGHT - 380), (1300, HEIGHT - 300),
             (1500, HEIGHT - 360), (1700, HEIGHT - 250), (1920, HEIGHT - 180), (1920, HEIGHT)]
    draw.polygon(peaks, fill=color)
    peaks2 = [(0, HEIGHT), (100, HEIGHT - 100), (350, HEIGHT - 200), (600, HEIGHT - 150),
              (900, HEIGHT - 250), (1200, HEIGHT - 180), (1500, HEIGHT - 220), (1800, HEIGHT - 140),
              (1920, HEIGHT - 100), (1920, HEIGHT)]
    draw.polygon(peaks2, fill=(15, 15, 22))


def draw_fire(draw, t, intensity=1.0):
    rng = random.Random(int(t * 10))
    for _ in range(40):
        base_x = WIDTH // 2 + rng.randint(-300, 300)
        base_y = HEIGHT - rng.randint(0, 400)
        flicker = rng.random()
        size = int(3 + flicker * 8)
        r_val = int(min(255, (200 + 55 * flicker) * intensity))
        g_val = int(min(255, (80 + 120 * flicker) * intensity))
        b_val = int(min(255, (10 + 20 * flicker) * intensity))
        y_offset = int(math.sin(t * 5 + flicker * 20) * 30)
        x_offset = int(math.sin(t * 3 + flicker * 15) * 15)
        fx, fy = base_x + x_offset, base_y + y_offset - int(t * 20 % 200)
        if 0 < fy < HEIGHT:
            draw.ellipse([fx - size, fy - size, fx + size, fy + size], fill=(r_val, g_val, b_val))


def draw_road(draw, t, intensity=1.0):
    alpha = int(50 * intensity)
    vx, vy = WIDTH // 2, HEIGHT // 3
    color = (alpha, alpha, int(alpha * 1.2))
    draw.line([(vx, vy), (WIDTH // 2 - 500, HEIGHT)], fill=color, width=2)
    draw.line([(vx, vy), (WIDTH // 2 + 500, HEIGHT)], fill=color, width=2)
    for i in range(12):
        prog = i / 12
        py = int(vy + (HEIGHT - vy) * prog)
        dash_len = int(5 + prog * 25)
        da = int(alpha * (0.3 + 0.7 * prog))
        anim = int((t * 60) % 40)
        py += anim
        if py < HEIGHT:
            draw.line([(vx, py), (vx, py + dash_len)], fill=(da, da, int(da * 1.1)), width=2)


def draw_heartbeat(draw, t, intensity=1.0):
    cx, cy = WIDTH // 2, HEIGHT // 2
    pulse = abs(math.sin(t * 3.0))
    for ring in range(3):
        r = int(50 + ring * 80 + pulse * 40)
        alpha = int(max(0, (80 - ring * 25) * intensity * pulse))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(alpha, int(alpha * 0.3), int(alpha * 0.3)), width=2)


def draw_glow_pulse(draw, t, intensity=1.0):
    cx, cy = WIDTH // 2, HEIGHT // 2
    pulse = 0.5 + 0.5 * math.sin(t * 2.0)
    for r in range(250, 30, -15):
        alpha = int((1.0 - r / 250) * 35 * pulse * intensity)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(int(alpha * 0.8), int(alpha * 0.6), alpha))


def draw_lightning(draw, t, intensity=1.0):
    flash = abs(math.sin(t * 8))
    if flash > 0.92:
        alpha = int(120 * intensity)
        rng = random.Random(int(t * 100))
        x = rng.randint(WIDTH // 4, 3 * WIDTH // 4)
        points = [(x, 0)]
        y = 0
        while y < HEIGHT * 0.7:
            y += rng.randint(20, 60)
            x += rng.randint(-40, 40)
            points.append((x, y))
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=(alpha, alpha, int(alpha * 1.2)), width=3)
            draw.line([points[i], points[i + 1]], fill=(alpha // 3, alpha // 3, alpha // 2), width=8)


def draw_stars_rising(draw, t, intensity=1.0):
    particle_system.add(2, "rising")
    particle_system.update_and_draw(draw)


def draw_pulse_ring(draw, t, intensity=1.0):
    cx, cy = WIDTH // 2, HEIGHT // 2
    cycle = (t * 1.5) % 3.0
    if cycle < 2.5:
        r = int(cycle / 2.5 * 400)
        alpha = int((1.0 - cycle / 2.5) * 80 * intensity)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(alpha, int(alpha * 0.8), int(alpha * 0.5)), width=3)


def draw_falling_particles(draw, t, intensity=1.0):
    particle_system.add(1, "falling")
    particle_system.update_and_draw(draw)


def draw_calm_waves(draw, t, intensity=1.0):
    for wave in range(4):
        points = []
        y_base = HEIGHT // 2 + wave * 60 - 90
        for x in range(0, WIDTH + 10, 10):
            y = y_base + int(math.sin(x * 0.005 + t * 1.5 + wave * 0.8) * (20 + wave * 10))
            points.append((x, y))
        alpha = int((40 - wave * 8) * intensity)
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=(int(alpha * 0.5), int(alpha * 0.7), alpha), width=2)


def draw_dissolve(draw, t, intensity=1.0):
    rng = random.Random(int(t * 5))
    for _ in range(100):
        x, y = rng.randint(0, WIDTH), rng.randint(0, HEIGHT)
        size = rng.randint(2, 6)
        alpha = int(rng.randint(20, 60) * intensity)
        draw.rectangle([x, y, x + size, y + size], fill=(alpha, alpha, alpha))


def draw_shadows(draw, t, intensity=1.0):
    pulse = 0.6 + 0.4 * math.sin(t * 1.5)
    for i in range(20):
        alpha = int((20 - i) * 3 * pulse * intensity)
        c = max(0, int(alpha * 0.15))
        draw.rectangle([0, 0, i * 15, HEIGHT], fill=(alpha // 4, 0, c))
        draw.rectangle([WIDTH - i * 15, 0, WIDTH, HEIGHT], fill=(alpha // 4, 0, c))
        draw.rectangle([0, 0, WIDTH, i * 8], fill=(alpha // 4, 0, c))


EFFECT_FUNCTIONS = {
    "stars": draw_stars, "light_rays": draw_light_rays, "sunrise": draw_sunrise,
    "mountain": draw_mountain, "fire": draw_fire, "road": draw_road,
    "heartbeat": draw_heartbeat, "glow_pulse": draw_glow_pulse, "lightning": draw_lightning,
    "stars_rising": draw_stars_rising, "pulse_ring": draw_pulse_ring,
    "falling_particles": draw_falling_particles, "calm_waves": draw_calm_waves,
    "dissolve": draw_dissolve, "shadows": draw_shadows, "shake": draw_pulse_ring,
}


def load_timestamps(path):
    with open(path) as f:
        data = json.load(f)
    # Add visual effect detection
    for entry in data:
        entry["visual"] = detect_visual(entry["text"])
        entry["color"] = get_section_color(entry["section"])
    return data


def render_frame(frame_num, timestamps, audio_duration, title_font, section_font, line_font, small_font):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    current_time = frame_num / FPS

    particle_system.update_and_draw(draw)

    # Find first lyric start time for title screen duration
    first_start = timestamps[0]["start"] if timestamps else 2.0
    title_duration = max(2.0, first_start - 0.5)

    # Title screen
    if current_time < title_duration:
        alpha = min(1.0, current_time / 1.5)
        # Fade out near end of title
        if current_time > title_duration - 1.0:
            alpha *= max(0, (title_duration - current_time))
        color = tuple(int(c * alpha) for c in (240, 192, 64))
        text = "I Will Stand in the Light"
        bbox = draw.textbbox((0, 0), text, font=title_font)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, HEIGHT // 2 - 40), text, fill=color, font=title_font)
        draw_glow_pulse(draw, current_time, 0.5 * alpha)
        return img

    # End screen (after last lyric)
    last_end = timestamps[-1]["end"] if timestamps else audio_duration
    if current_time > last_end + 2.0:
        elapsed = current_time - (last_end + 2.0)
        alpha = min(1.0, elapsed / 1.5)
        color = tuple(int(c * alpha) for c in (240, 192, 64))
        draw_light_rays(draw, current_time, alpha)
        draw_sunrise(draw, current_time, alpha * 0.7)
        text = "I Will Stand in the Light"
        bbox = draw.textbbox((0, 0), text, font=title_font)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, HEIGHT // 2 - 40), text, fill=color, font=title_font)
        return img

    # --- Find the currently active line index ---
    active_idx = None
    for i, ts in enumerate(timestamps):
        start = ts["start"]
        end = ts.get("end", start + 2.0)
        if start <= current_time <= end + 0.5:
            active_idx = i
    # If between lines, show the most recent one as active
    if active_idx is None:
        for i, ts in enumerate(timestamps):
            if ts["start"] <= current_time:
                active_idx = i
            else:
                break

    if active_idx is None:
        active_idx = 0

    # --- Build visible window: 3 past lines, active line, 3 upcoming lines ---
    LINES_BEFORE = 3
    LINES_AFTER = 3
    window_start = max(0, active_idx - LINES_BEFORE)
    window_end = min(len(timestamps), active_idx + LINES_AFTER + 1)
    visible_lines = []

    for i in range(window_start, window_end):
        ts = timestamps[i]
        start = ts["start"]
        end = ts.get("end", start + 2.0)
        is_active = (i == active_idx) and (current_time >= start - 0.3)
        is_past = current_time > end + 0.5
        is_upcoming = current_time < start - 0.3

        # Fade: past and active lines are fully visible, upcoming lines are dim
        if is_upcoming:
            fade = 0.25
        elif is_active:
            fade = min(1.0, max(0.3, (current_time - start + 0.3) / 0.4))
        else:
            fade = 1.0

        visible_lines.append({
            **ts,
            "fade": fade,
            "is_active": is_active,
            "is_past": is_past,
            "is_upcoming": is_upcoming,
            "idx": i,
        })

    # --- Draw visual effects for the active line ---
    for vl in visible_lines:
        if vl["is_active"] and vl.get("visual"):
            fn = EFFECT_FUNCTIONS.get(vl["visual"])
            if fn:
                fn(draw, current_time, 0.8)
            break

    # --- Draw section badge ---
    current_section = timestamps[active_idx]["section"]
    badge_text = current_section.upper()
    badge_color = get_section_color(current_section)
    bbox = draw.textbbox((0, 0), badge_text, font=section_font)
    tw = bbox[2] - bbox[0]
    draw.text(((WIDTH - tw) // 2, 60), badge_text, fill=badge_color, font=section_font)

    # --- Draw lyrics with active line centered ---
    line_height = 72
    total_height = len(visible_lines) * line_height

    # Find position of active line in the visible list
    active_pos_in_list = 0
    for i, vl in enumerate(visible_lines):
        if vl["is_active"]:
            active_pos_in_list = i
            break

    # Center the active line vertically
    center_y = HEIGHT // 2
    start_y = center_y - active_pos_in_list * line_height - line_height // 2

    for i, vl in enumerate(visible_lines):
        y = start_y + i * line_height
        fade = vl["fade"]
        is_active = vl["is_active"]

        text = vl["text"]
        bbox = draw.textbbox((0, 0), text, font=line_font)
        tw = bbox[2] - bbox[0]
        x = (WIDTH - tw) // 2

        if is_active:
            # ACTIVE LINE: bright section color with glow background
            color = tuple(int(c * fade) for c in vl["color"])
            gc = vl["color"]
            glow_color = (gc[0] // 4, gc[1] // 4, gc[2] // 4)
            draw.rounded_rectangle(
                [x - 30, y - 10, x + tw + 30, y + 55],
                radius=14, fill=glow_color
            )
            draw.text((x, y), text, fill=color, font=line_font)
        elif vl["is_past"]:
            # Past lines: visible but dimmed
            age_factor = max(0.25, 1.0 - (active_idx - vl["idx"]) * 0.2)
            base = (150, 155, 170)
            color = tuple(int(c * age_factor) for c in base)
            draw.text((x, y), text, fill=color, font=line_font)
        else:
            # Upcoming lines: dim, waiting
            color = (50, 52, 65)
            draw.text((x, y), text, fill=color, font=line_font)

    # Footer
    footer = "I Will Stand in the Light"
    footer_color = (35, 35, 55)
    bbox = draw.textbbox((0, 0), footer, font=small_font)
    tw = bbox[2] - bbox[0]
    draw.text(((WIDTH - tw) // 2, HEIGHT - 50), footer, fill=footer_color, font=small_font)

    return img


def main():
    parser = argparse.ArgumentParser(description="Generate synced lyrics video")
    parser.add_argument("--audio", type=str, required=True, help="Path to audio file")
    parser.add_argument("--timestamps", type=str, default="timestamps.json", help="Timestamps JSON file")
    parser.add_argument("--output", type=str, default="i_will_stand_in_the_light_synced.mp4", help="Output filename")
    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        print("ERROR: ffmpeg not found. Install it with: brew install ffmpeg")
        return

    if not os.path.exists(args.audio):
        print(f"ERROR: Audio file not found: {args.audio}")
        return

    if not os.path.exists(args.timestamps):
        print(f"ERROR: Timestamps file not found: {args.timestamps}")
        print("Run sync_lyrics.py first to generate it:")
        print(f'  python3 sync_lyrics.py --audio "{args.audio}"')
        return

    print("Loading timestamps...")
    timestamps = load_timestamps(args.timestamps)
    print(f"Loaded {len(timestamps)} lyric lines with timing")

    # Get audio duration
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", args.audio],
        capture_output=True, text=True
    )
    audio_duration = float(result.stdout.strip()) if result.returncode == 0 else 300.0
    print(f"Audio duration: {audio_duration:.1f}s")

    total_frames = int(audio_duration * FPS)
    print(f"Video: {total_frames} frames at {FPS}fps")
    print("Loading fonts...")

    title_font = get_font(64, bold=True)
    section_font = get_font(22, bold=True)
    line_font = get_font(44)
    small_font = get_font(18)

    print("Rendering synced video...")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24",
        "-r", str(FPS), "-i", "-",
        "-i", args.audio, "-c:a", "aac", "-b:a", "192k",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p", "-shortest",
        args.output,
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    for frame_num in range(total_frames):
        img = render_frame(frame_num, timestamps, audio_duration, title_font, section_font, line_font, small_font)
        proc.stdin.write(img.tobytes())

        if frame_num % FPS == 0:
            pct = int(frame_num / total_frames * 100)
            print(f"\r  Progress: {pct}% ({frame_num}/{total_frames} frames)", end="", flush=True)

    proc.stdin.close()
    proc.wait()
    print(f"\n\nDone! Video saved to: {args.output}")
    print("Lyrics are now synced to your audio!")


if __name__ == "__main__":
    main()
