#!/usr/bin/env python3
"""
Generate narration audio from a script.md file using ElevenLabs TTS.

Usage:
    python generate_audio.py <script.md> <output_dir>

Requires ELEVENLABS_API_KEY environment variable.
"""

import os
import re
import sys
import requests


VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # Sarah
BASE_URL = "https://api.elevenlabs.io/v1"
MODEL_ID = "eleven_turbo_v2_5"


def parse_script(script_path: str) -> dict[str, str]:
    """Extract scene narrations from script.md.

    Handles narration blocks that may contain internal double quotes
    by finding the opening quote after **Narration:** and the closing
    quote before the next scene header (or end of file).
    """
    with open(script_path) as f:
        content = f.read()

    scenes = {}
    # Split by scene headers, then extract narration from each chunk
    scene_splits = re.split(r'(## Scene (\d+):)', content)

    # scene_splits: [preamble, header1, num1, body1, header2, num2, body2, ...]
    i = 1
    while i < len(scene_splits) - 2:
        scene_num = int(scene_splits[i + 1])
        body = scene_splits[i + 2]

        # Find narration: everything between first " and last " after **Narration:**
        narr_match = re.search(r'\*\*Narration:\*\*\s*\n"(.+)"', body, re.DOTALL)
        if narr_match:
            narration = narr_match.group(1).strip()
            narration = " ".join(narration.split())
            scenes[f"scene_{scene_num}"] = narration

        i += 3

    return scenes


def generate_audio(scene_name: str, text: str, output_dir: str, api_key: str) -> None:
    """Generate audio for a single scene."""
    url = f"{BASE_URL}/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }

    print(f"Generating {scene_name}...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        print(f"  ERROR {response.status_code}: {response.text}")
        sys.exit(1)

    output_path = os.path.join(output_dir, f"{scene_name}.mp3")
    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"  Saved {output_path} ({len(response.content)} bytes)")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <script.md> <output_dir>")
        sys.exit(1)

    script_path = sys.argv[1]
    output_dir = sys.argv[2]

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY environment variable not set")
        sys.exit(1)

    if not os.path.exists(script_path):
        print(f"ERROR: Script not found: {script_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    scenes = parse_script(script_path)
    if not scenes:
        print("ERROR: No scenes found in script. Expected format:")
        print('  ## Scene 1: Title\\n**Narration:**\\n"Text here"')
        sys.exit(1)

    print(f"Found {len(scenes)} scenes")
    for scene_name, text in sorted(scenes.items()):
        generate_audio(scene_name, text, output_dir, api_key)

    print("Done!")


if __name__ == "__main__":
    main()
