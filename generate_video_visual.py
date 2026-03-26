#!/usr/bin/env python3
"""
Enhanced Lyrics Video Generator for "I Will Stand in the Light"
Generates an .mp4 video with animated lyrics AND visual effects tied to the lyrics.

Usage:
    python3 generate_video_visual.py --audio "I Will Stand in the Light.mp3"
    python3 generate_video_visual.py --audio song.mp3 --output my_video.mp4

Requirements:
    pip3 install pillow
    brew install ffmpeg
"""

import argparse
import math
import os
import random
import subprocess
import shutil
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# --- Configuration ---
WIDTH = 1920
HEIGHT = 1080
FPS = 30
BG_COLOR = (10, 10, 26)
FADE_FRAMES = int(0.8 * FPS)

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
    {"section": "Intro", "lines": [
        "This fear is real",
        "This night is long",
        "But something deeper calls me on",
    ]},
    {"section": "Verse 1", "lines": [
        "Monday morning waits before me",
        "Like a mountain made of stone",
        "And I feel the weight of worry",
        "Like I have to stand alone",
        "",
        "But somewhere underneath the shaking",
        "Under all the fear I feel",
        "There is something still unbroken",
        "There is something steady, real",
    ]},
    {"section": "Pre-Chorus", "lines": [
        "So when the dark comes close",
        "And the worst begins to speak",
        "I will listen for the deeper voice",
        "That tells my soul to keep",
    ]},
    {"section": "Chorus", "lines": [
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
    ]},
    {"section": "Verse 2", "lines": [
        "I do not need to know the ending",
        "To take the next right breath",
        "I do not need to feel unbroken",
        "To keep walking through the test",
        "",
        "There is strength inside the trembling",
        "There is hope inside the strain",
        "And the soul that has survived so much",
        "Can rise again, again",
    ]},
    {"section": "Pre-Chorus", "lines": [
        "So if my hands are shaking",
        "That does not mean I fall",
        "It means I'm human in the moment",
        "And still answering the call",
    ]},
    {"section": "Chorus", "lines": [
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
    ]},
    {"section": "Bridge", "lines": [
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
    ]},
    {"section": "Final Chorus", "lines": [
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
    ]},
    {"section": "Outro", "lines": [
        "This fear is real",
        "But it is not my master",
        "Morning is coming",
        "And I will meet it standing",
    ]},
]

# --- Visual effect keyword mappings ---
VISUAL_KEYWORDS = {
    "night": "stars",
    "dark": "stars",
    "fear": "shadows",
    "afraid": "shadows",
    "light": "light_rays",
    "stand in the light": "light_rays",
    "morning": "sunrise",
    "mountain": "mountain",
    "stone": "mountain",
    "shaking": "shake",
    "trembling": "shake",
    "courage shakes": "shake",
    "fire": "fire",
    "walked through fire": "fire",
    "road": "road",
    "heart": "heartbeat",
    "soul": "glow_pulse",
    "breathe": "glow_pulse",
    "thunder": "lightning",
    "rain": "rain",
    "hope": "stars_rising",
    "rise again": "stars_rising",
    "strength": "pulse_ring",
    "unbroken": "pulse_ring",
    "weight": "falling_particles",
    "worry": "falling_particles",
    "pain": "falling_particles",
    "peace": "calm_waves",
    "slowly": "calm_waves",
    "master": "light_rays",
    "standing": "light_rays",
    "faith": "light_rays",
    "erase": "dissolve",
    "test": "pulse_ring",
    "trial": "pulse_ring",
    "power": "pulse_ring",
}


# --- Persistent particle systems ---
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
                "max_life": 150,
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


# --- Seeded random for reproducible visuals ---
vis_random = random.Random(42)


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
    """Detect which visual effect to use based on lyrics keywords."""
    text_lower = line_text.lower()
    # Check longer phrases first
    for keyword, effect in sorted(VISUAL_KEYWORDS.items(), key=lambda x: -len(x[0])):
        if keyword in text_lower:
            return effect
    return None


# --- Visual effect drawing functions ---

def draw_stars(draw, t, intensity=1.0):
    """Twinkling stars for night/dark."""
    rng = random.Random(12345)
    for _ in range(60):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, int(HEIGHT * 0.7))
        twinkle = 0.3 + 0.7 * abs(math.sin(t * 2 + rng.random() * 10))
        brightness = int(200 * twinkle * intensity)
        size = rng.randint(1, 3)
        color = (brightness, brightness, int(brightness * 1.1))
        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)


def draw_light_rays(draw, t, intensity=1.0):
    """Golden light rays from center/bottom."""
    cx = WIDTH // 2
    cy = HEIGHT
    num_rays = 12
    for i in range(num_rays):
        angle = (i / num_rays) * math.pi - math.pi / 2 + math.sin(t * 0.5) * 0.05
        length = 500 + 200 * math.sin(t * 1.5 + i)
        pulse = 0.5 + 0.5 * math.sin(t * 2 + i * 0.5)
        alpha = int(40 * pulse * intensity)
        ex = cx + math.cos(angle) * length
        ey = cy + math.sin(angle) * length
        color = (alpha, int(alpha * 0.8), int(alpha * 0.3))
        draw.line([(cx, cy), (ex, ey)], fill=color, width=3)
        # Second layer wider
        for offset in range(-8, 9, 4):
            ex2 = cx + math.cos(angle + offset * 0.003) * length * 0.8
            ey2 = cy + math.sin(angle + offset * 0.003) * length * 0.8
            faint = max(0, alpha // 3)
            draw.line([(cx, cy), (ex2, ey2)], fill=(faint, int(faint * 0.7), int(faint * 0.2)), width=1)


def draw_sunrise(draw, t, intensity=1.0):
    """Warm sunrise glow from bottom center."""
    cx = WIDTH // 2
    cy = HEIGHT + 100
    for r in range(400, 50, -10):
        alpha = int((1.0 - r / 400) * 60 * intensity)
        pulse = 0.8 + 0.2 * math.sin(t * 1.0)
        alpha = int(alpha * pulse)
        color = (alpha, int(alpha * 0.6), int(alpha * 0.2))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def draw_mountain(draw, t, intensity=1.0):
    """Silhouette mountain range."""
    alpha = int(60 * intensity)
    color = (20 + alpha // 4, 20 + alpha // 6, 30 + alpha // 3)
    # Main mountain
    peaks = [
        (0, HEIGHT), (200, HEIGHT - 200), (400, HEIGHT - 350),
        (600, HEIGHT - 280), (800, HEIGHT - 420), (960, HEIGHT - 500),
        (1120, HEIGHT - 380), (1300, HEIGHT - 300), (1500, HEIGHT - 360),
        (1700, HEIGHT - 250), (1920, HEIGHT - 180), (1920, HEIGHT),
    ]
    draw.polygon(peaks, fill=color)
    # Foreground mountain (darker)
    color2 = (15, 15, 22)
    peaks2 = [
        (0, HEIGHT), (100, HEIGHT - 100), (350, HEIGHT - 200),
        (600, HEIGHT - 150), (900, HEIGHT - 250), (1200, HEIGHT - 180),
        (1500, HEIGHT - 220), (1800, HEIGHT - 140), (1920, HEIGHT - 100), (1920, HEIGHT),
    ]
    draw.polygon(peaks2, fill=color2)


def draw_fire(draw, t, intensity=1.0):
    """Fire/flame particles rising from bottom."""
    rng = random.Random(int(t * 10))
    for _ in range(40):
        base_x = WIDTH // 2 + rng.randint(-300, 300)
        base_y = HEIGHT - rng.randint(0, 400)
        flicker = rng.random()
        size = int(3 + flicker * 8)
        # Fire colors: yellow core to red edges
        r_val = int(min(255, (200 + 55 * flicker) * intensity))
        g_val = int(min(255, (80 + 120 * flicker) * intensity))
        b_val = int(min(255, (10 + 20 * flicker) * intensity))
        # Animate upward
        y_offset = int(math.sin(t * 5 + flicker * 20) * 30)
        x_offset = int(math.sin(t * 3 + flicker * 15) * 15)
        fx = base_x + x_offset
        fy = base_y + y_offset - int(t * 20 % 200)
        if 0 < fy < HEIGHT:
            draw.ellipse([fx - size, fy - size, fx + size, fy + size], fill=(r_val, g_val, b_val))


def draw_road(draw, t, intensity=1.0):
    """Perspective road vanishing into distance."""
    alpha = int(50 * intensity)
    vanish_x = WIDTH // 2
    vanish_y = HEIGHT // 3
    # Road edges
    color = (alpha, alpha, int(alpha * 1.2))
    draw.line([(vanish_x, vanish_y), (WIDTH // 2 - 500, HEIGHT)], fill=color, width=2)
    draw.line([(vanish_x, vanish_y), (WIDTH // 2 + 500, HEIGHT)], fill=color, width=2)
    # Center dashes
    for i in range(12):
        prog = i / 12
        px = vanish_x
        py = int(vanish_y + (HEIGHT - vanish_y) * prog)
        dash_len = int(5 + prog * 25)
        dash_alpha = int(alpha * (0.3 + 0.7 * prog))
        dash_color = (dash_alpha, dash_alpha, int(dash_alpha * 1.1))
        # Animate dashes moving toward viewer
        anim_offset = int((t * 60) % 40)
        py += anim_offset
        if py < HEIGHT:
            draw.line([(px, py), (px, py + dash_len)], fill=dash_color, width=2)


def draw_heartbeat(draw, t, intensity=1.0):
    """Pulsing heart / heartbeat rings."""
    cx, cy = WIDTH // 2, HEIGHT // 2
    pulse = abs(math.sin(t * 3.0))
    for ring in range(3):
        r = int(50 + ring * 80 + pulse * 40)
        alpha = int(max(0, (80 - ring * 25) * intensity * pulse))
        color = (alpha, int(alpha * 0.3), int(alpha * 0.3))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)


def draw_glow_pulse(draw, t, intensity=1.0):
    """Soft pulsing glow from center."""
    cx, cy = WIDTH // 2, HEIGHT // 2
    pulse = 0.5 + 0.5 * math.sin(t * 2.0)
    for r in range(250, 30, -15):
        alpha = int((1.0 - r / 250) * 35 * pulse * intensity)
        color = (int(alpha * 0.8), int(alpha * 0.6), alpha)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def draw_lightning(draw, t, intensity=1.0):
    """Lightning flash effect."""
    flash = abs(math.sin(t * 8))
    if flash > 0.92:
        # Bright flash
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
            # Glow
            draw.line([points[i], points[i + 1]], fill=(alpha // 3, alpha // 3, alpha // 2), width=8)


def draw_stars_rising(draw, t, intensity=1.0):
    """Stars/sparks rising upward — hope."""
    particle_system.add(2, "rising")
    particle_system.update_and_draw(draw)


def draw_pulse_ring(draw, t, intensity=1.0):
    """Expanding ring pulse — strength."""
    cx, cy = WIDTH // 2, HEIGHT // 2
    cycle = (t * 1.5) % 3.0
    if cycle < 2.5:
        r = int(cycle / 2.5 * 400)
        alpha = int((1.0 - cycle / 2.5) * 80 * intensity)
        color = (alpha, int(alpha * 0.8), int(alpha * 0.5))
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=3)


def draw_falling_particles(draw, t, intensity=1.0):
    """Particles drifting down — weight/worry."""
    particle_system.add(1, "falling")
    particle_system.update_and_draw(draw)


def draw_calm_waves(draw, t, intensity=1.0):
    """Gentle sine waves — peace."""
    for wave in range(4):
        points = []
        y_base = HEIGHT // 2 + wave * 60 - 90
        for x in range(0, WIDTH + 10, 10):
            y = y_base + int(math.sin(x * 0.005 + t * 1.5 + wave * 0.8) * (20 + wave * 10))
            points.append((x, y))
        alpha = int((40 - wave * 8) * intensity)
        color = (int(alpha * 0.5), int(alpha * 0.7), alpha)
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=color, width=2)


def draw_dissolve(draw, t, intensity=1.0):
    """Dissolving pixel effect."""
    rng = random.Random(int(t * 5))
    for _ in range(100):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, HEIGHT)
        size = rng.randint(2, 6)
        alpha = int(rng.randint(20, 60) * intensity)
        color = (alpha, alpha, alpha)
        draw.rectangle([x, y, x + size, y + size], fill=color)


def draw_shadows(draw, t, intensity=1.0):
    """Creeping shadow edges for fear."""
    # Dark vignette that pulses
    pulse = 0.6 + 0.4 * math.sin(t * 1.5)
    for i in range(20):
        alpha = int((20 - i) * 3 * pulse * intensity)
        color = (0, 0, max(0, int(alpha * 0.15)))
        # Left shadow
        draw.rectangle([0, 0, i * 15, HEIGHT], fill=(alpha // 4, 0, color[2]))
        # Right shadow
        draw.rectangle([WIDTH - i * 15, 0, WIDTH, HEIGHT], fill=(alpha // 4, 0, color[2]))
        # Top shadow
        draw.rectangle([0, 0, WIDTH, i * 8], fill=(alpha // 4, 0, color[2]))


EFFECT_FUNCTIONS = {
    "stars": draw_stars,
    "light_rays": draw_light_rays,
    "sunrise": draw_sunrise,
    "mountain": draw_mountain,
    "fire": draw_fire,
    "road": draw_road,
    "heartbeat": draw_heartbeat,
    "glow_pulse": draw_glow_pulse,
    "lightning": draw_lightning,
    "stars_rising": draw_stars_rising,
    "pulse_ring": draw_pulse_ring,
    "falling_particles": draw_falling_particles,
    "calm_waves": draw_calm_waves,
    "dissolve": draw_dissolve,
    "shadows": draw_shadows,
    "shake": draw_pulse_ring,  # reuse pulse ring for shake
}


def build_timeline():
    timeline = []
    t = 2.0

    for block in LYRICS:
        section = block["section"]
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
            visual = detect_visual(line)
            timeline.append({
                "type": "line",
                "text": line,
                "start": t,
                "section": section,
                "color": get_section_color(section),
                "visual": visual,
            })
            t += 2.5

        t += 1.5

    timeline.append({
        "type": "end",
        "text": "I Will Stand in the Light",
        "start": t + 1.0,
        "color": (240, 192, 64),
    })
    total_duration = t + 5.0
    return timeline, total_duration


def render_frame(frame_num, timeline, title_font, section_font, line_font, small_font):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    current_time = frame_num / FPS

    # --- Always draw ambient background particles ---
    particle_system.update_and_draw(draw)

    # Title screen
    if current_time < 2.0:
        alpha = min(1.0, current_time / 1.5)
        color = tuple(int(c * alpha) for c in (240, 192, 64))
        text = "I Will Stand in the Light"
        bbox = draw.textbbox((0, 0), text, font=title_font)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, HEIGHT // 2 - 40), text, fill=color, font=title_font)
        # Gentle glow for title
        draw_glow_pulse(draw, current_time, 0.5)
        return img

    # Collect visible events
    visible = []
    for event in timeline:
        if event["start"] > current_time:
            break
        if event["type"] == "end" and current_time >= event["start"]:
            alpha = min(1.0, (current_time - event["start"]) / 1.5)
            color = tuple(int(c * alpha) for c in event["color"])
            draw_light_rays(draw, current_time, alpha)
            draw_sunrise(draw, current_time, alpha * 0.7)
            text = event["text"]
            bbox = draw.textbbox((0, 0), text, font=title_font)
            tw = bbox[2] - bbox[0]
            draw.text(((WIDTH - tw) // 2, HEIGHT // 2 - 40), text, fill=color, font=title_font)
            return img
        visible.append(event)

    if not visible:
        return img

    # --- Draw visual effects for active lines ---
    # Find the current (most recent) line and draw its visual
    active_effects = set()
    for event in reversed(visible):
        if event["type"] == "line":
            elapsed = current_time - event["start"]
            if elapsed < 4.0:  # effect lasts 4 seconds
                visual = event.get("visual")
                if visual and visual not in active_effects:
                    intensity = min(1.0, elapsed / 0.5) * max(0.0, 1.0 - elapsed / 4.0)
                    fn = EFFECT_FUNCTIONS.get(visual)
                    if fn:
                        fn(draw, current_time, intensity)
                    active_effects.add(visual)
            if len(active_effects) >= 3:
                break

    # Find current section
    current_section = None
    for event in reversed(visible):
        if event["type"] == "section":
            current_section = event
            break

    # Layout
    display_items = []
    for event in visible:
        elapsed = current_time - event["start"]
        fade = min(1.0, elapsed / (FADE_FRAMES / FPS))
        display_items.append({**event, "fade": fade, "elapsed": elapsed})

    line_items = [d for d in display_items if d["type"] == "line"]
    if len(line_items) > 8:
        line_items = line_items[-8:]

    # Section badge
    if current_section:
        badge_text = current_section["text"].upper()
        badge_fade = min(1.0, (current_time - current_section["start"]) / 0.5)
        badge_color = tuple(int(c * badge_fade) for c in current_section["color"])
        bbox = draw.textbbox((0, 0), badge_text, font=section_font)
        tw = bbox[2] - bbox[0]
        draw.text(((WIDTH - tw) // 2, 60), badge_text, fill=badge_color, font=section_font)

    # Draw lyrics
    line_height = 68
    total_height = len(line_items) * line_height
    start_y = (HEIGHT - total_height) // 2 + 20

    for i, item in enumerate(line_items):
        y = start_y + i * line_height
        fade = item["fade"]
        is_latest = (i == len(line_items) - 1)

        if is_latest:
            # Current line — bright with glow
            color = tuple(int(c * fade) for c in item["color"])
            font = line_font
        else:
            dim = max(0.25, 1.0 - (len(line_items) - 1 - i) * 0.12)
            base = (170, 175, 190)
            color = tuple(int(c * dim * fade) for c in base)
            font = line_font

        text = item["text"]
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]

        offset_y = int((1.0 - fade) * 15)
        x = (WIDTH - tw) // 2

        # Glow behind current line
        if is_latest and fade > 0.5:
            glow_alpha = int(30 * fade)
            gc = item["color"]
            glow_color = (gc[0] // 6, gc[1] // 6, gc[2] // 6)
            draw.rounded_rectangle(
                [x - 20, y + offset_y - 5, x + tw + 20, y + offset_y + 50],
                radius=10, fill=glow_color
            )

        draw.text((x, y + offset_y), text, fill=color, font=font)

    # Footer
    footer = "I Will Stand in the Light"
    footer_color = (35, 35, 55)
    bbox = draw.textbbox((0, 0), footer, font=small_font)
    tw = bbox[2] - bbox[0]
    draw.text(((WIDTH - tw) // 2, HEIGHT - 50), footer, fill=footer_color, font=small_font)

    return img


def main():
    parser = argparse.ArgumentParser(description="Generate enhanced lyrics video with visuals")
    parser.add_argument("--audio", type=str, help="Path to audio file (.mp3, .wav)")
    parser.add_argument("--output", type=str, default="i_will_stand_in_the_light_visual.mp4", help="Output filename")
    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        print("ERROR: ffmpeg not found. Install it with: brew install ffmpeg")
        return

    print("Building timeline with visual effects...")
    timeline, duration = build_timeline()

    # Print detected visuals
    for event in timeline:
        if event["type"] == "line" and event.get("visual"):
            print(f"  [{event['visual']:>18}] {event['text']}")

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
            print(f"\nAudio duration: {audio_duration:.1f}s")

    total_frames = int(duration * FPS)
    print(f"Video duration: {duration:.1f}s ({total_frames} frames)")
    print("Loading fonts...")

    title_font = get_font(64, bold=True)
    section_font = get_font(22, bold=True)
    line_font = get_font(44)
    small_font = get_font(18)

    print("Rendering video with visual effects...")

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24",
        "-r", str(FPS), "-i", "-",
    ]

    if args.audio:
        ffmpeg_cmd.extend(["-i", args.audio, "-c:a", "aac", "-b:a", "192k"])

    ffmpeg_cmd.extend([
        "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p",
    ])

    if args.audio:
        ffmpeg_cmd.append("-shortest")

    ffmpeg_cmd.append(args.output)

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
    print("Visual effects included: stars, light rays, sunrise, mountains, fire,")
    print("road, heartbeat, lightning, rising particles, waves, and more!")


if __name__ == "__main__":
    main()
