#!/usr/bin/env python3
"""
Assemble final explainer video from Manim scenes and audio.

Usage:
    python assemble_video.py <project_dir> [--topic <topic_name>]

Steps:
1. Render each Manim scene class
2. Merge video + audio per scene
3. Concatenate all scenes into final video

Requires: manim, ffmpeg
"""

import os
import re
import subprocess
import sys
import argparse


def find_scene_classes(scenes_dir: str) -> list:
    """Find all Scene classes in the scenes directory, return (file, class_name, scene_num) tuples.

    Extracts the scene number from class names like Scene1_Title, Scene2_QKV, etc.
    Falls back to declaration order if no number is found.
    Sorts by scene number to ensure correct audio pairing.
    """
    if not os.path.isdir(scenes_dir):
        print(f"ERROR: scenes directory not found: {scenes_dir}")
        sys.exit(1)

    results = []
    for fname in sorted(os.listdir(scenes_dir)):
        if not fname.endswith(".py"):
            continue
        filepath = os.path.join(scenes_dir, fname)
        with open(filepath) as f:
            content = f.read()
        for match in re.finditer(r"class (\w+)\(Scene\)", content):
            class_name = match.group(1)
            # Extract scene number from class name (e.g., Scene1_Title -> 1)
            num_match = re.search(r'(\d+)', class_name)
            scene_num = int(num_match.group(1)) if num_match else len(results) + 1
            results.append((filepath, class_name, scene_num))

    # Sort by scene number for correct audio pairing
    results.sort(key=lambda x: x[2])
    return results


def find_rendered_video(scenes_dir: str, class_name: str) -> str:
    """Find the rendered video file for a scene class.

    Searches both the scenes/media/ directory (when manim is run from scenes/)
    and the project-level media/ directory (when manim is run from project root).
    """
    search_dirs = [
        os.path.join(scenes_dir, "media", "videos"),
        os.path.join(os.path.dirname(scenes_dir), "media", "videos"),
    ]
    for media_dir in search_dirs:
        if not os.path.exists(media_dir):
            continue
        for root, dirs, files in os.walk(media_dir):
            for f in files:
                if f == f"{class_name}.mp4":
                    return os.path.join(root, f)
    return None


def render_scene(filepath: str, class_name: str, scenes_dir: str) -> bool:
    """Render a single Manim scene from the scenes directory."""
    print(f"Rendering {class_name}...")
    result = subprocess.run(
        ["python3", "-m", "manim", "render", "-qh", filepath, class_name],
        capture_output=True,
        text=True,
        cwd=scenes_dir,  # Run from scenes/ so media/ lands in scenes/media/
    )
    if result.returncode != 0:
        print(f"  ERROR rendering {class_name}:")
        print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
        return False
    print(f"  Rendered {class_name}")
    return True


def merge_video_audio(video_path: str, audio_path: str, output_path: str) -> bool:
    """Merge a video file with an audio file."""
    print(f"Merging {os.path.basename(output_path)}...")
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[-300:]}")
        return False
    return True


def concatenate_videos(video_paths: list, output_path: str, project_dir: str) -> bool:
    """Concatenate multiple videos using ffmpeg concat demuxer."""
    concat_file = os.path.join(project_dir, "concat_list.txt")
    with open(concat_file, "w") as f:
        for vp in video_paths:
            f.write(f"file '{vp}'\n")

    print(f"Concatenating {len(video_paths)} scenes...")
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr[-300:]}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Assemble explainer video")
    parser.add_argument("project_dir", help="Project directory")
    parser.add_argument("--topic", help="Topic name for output filename", default=None)
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    scenes_dir = os.path.join(project_dir, "scenes")
    audio_dir = os.path.join(project_dir, "audio")
    combined_dir = os.path.join(project_dir, "combined")

    os.makedirs(combined_dir, exist_ok=True)

    # Step 1: Find and render scenes (sorted by scene number)
    scene_classes = find_scene_classes(scenes_dir)
    if not scene_classes:
        print("ERROR: No Scene classes found in scenes/")
        sys.exit(1)

    print(f"Found {len(scene_classes)} scenes")
    for filepath, class_name, scene_num in scene_classes:
        if not render_scene(filepath, class_name, scenes_dir):
            print(f"Failed to render {class_name}, aborting.")
            sys.exit(1)

    # Step 2: Merge video + audio for each scene
    combined_paths = []
    for filepath, class_name, scene_num in scene_classes:
        video_path = find_rendered_video(scenes_dir, class_name)
        if not video_path:
            print(f"ERROR: Could not find rendered video for {class_name}")
            sys.exit(1)

        # Match audio by scene number extracted from class name
        audio_path = os.path.join(audio_dir, f"scene_{scene_num}.mp3")
        if not os.path.exists(audio_path):
            print(f"WARNING: No audio for scene {scene_num} ({class_name}), using video only")
            combined_paths.append(video_path)
            continue

        output_path = os.path.join(combined_dir, f"scene_{scene_num}.mp4")
        if not merge_video_audio(video_path, audio_path, output_path):
            print(f"Failed to merge scene {scene_num}, aborting.")
            sys.exit(1)
        combined_paths.append(output_path)

    # Step 3: Concatenate all scenes
    topic = args.topic
    if not topic:
        for fname in os.listdir(scenes_dir):
            if fname.endswith("_scenes.py"):
                topic = fname.replace("_scenes.py", "")
                break
        if not topic:
            topic = os.path.basename(project_dir)

    output_path = os.path.join(project_dir, f"{topic}_explainer.mp4")
    if not concatenate_videos(combined_paths, output_path, project_dir):
        print("Failed to concatenate scenes.")
        sys.exit(1)

    print(f"\nDone! Final video: {output_path}")


if __name__ == "__main__":
    main()
