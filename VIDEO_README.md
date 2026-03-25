# Lyrics Video Generator

## Setup (Mac)

```bash
brew install python ffmpeg
pip3 install pillow
```

## Usage

Place your audio file (e.g., `song.mp3`) in this folder, then run:

```bash
python3 generate_video.py --audio song.mp3
```

This will create `i_will_stand_in_the_light.mp4` in the same folder.

### Options

```bash
# Custom output filename
python3 generate_video.py --audio song.mp3 --output my_video.mp4

# Without audio (lyrics-only video)
python3 generate_video.py
```
