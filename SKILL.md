---
name: first-principles-explainer
description: >
  Build animated first-principles explanation videos from technical topics and source materials (papers, articles, URLs).
  Uses Manim for animation, ElevenLabs for narration, and FFmpeg for assembly. Use this skill whenever the user wants to
  create an explainer video, technical animation, or visual walkthrough of a concept — even if they don't say "video" explicitly.
  Trigger on phrases like "explain X visually", "make a video about", "animate how X works", "create an explainer for",
  "first principles video", or when they provide papers/topics and want a visual explanation.
---

# First Principles Explainer Video

Create polished, multi-scene explanation videos that break down technical concepts from first principles. Each video combines Manim animations, professional narration, and paper figures into a cohesive visual story.

## Pipeline Overview

The pipeline has 6 phases. Execute them in order, using subagents to parallelize where noted.

```
Research → Script → Assets → Animate → Voice → Assemble
```

## Phase 1: Research

**Goal:** Build deep understanding of the topic from source materials.

1. Read any papers, URLs, or files the user provides
2. Use WebSearch/WebFetch to fill gaps — find key papers, blog posts, and figures
3. Identify the **narrative arc**: what's the core idea, what came before, what's the progression, what's the payoff?
4. Aim for 5-8 scenes that build understanding incrementally

Present a **scene outline** to the user before proceeding:

```
Scene 1: [Title] (0:00–1:30) — [one-line summary]
Scene 2: [Title] (1:30–3:00) — [one-line summary]
...
```

Each scene should be 45-60 seconds of narration (~120-150 words). Total video: 5-10 minutes.

Wait for user approval before moving on.

## Phase 2: Script

**Goal:** Write narration that a viewer can follow without any prior knowledge of the topic.

Write `script.md` in the project directory with this structure:

```markdown
# [Topic] Explainer Video Script

## Scene 1: [Title] (0:00–1:30)
**Narration:**
"[Full narration text]"

## Scene 2: [Title] (1:30–3:00)
**Narration:**
"[Full narration text]"
```

### Writing principles

- **Build from what the viewer already knows.** Start every scene by connecting to familiar concepts before introducing new ones. "Every self-driving car answers four questions" is better than "The autonomous driving stack consists of four modules."
- **One idea per scene.** Each scene has a single takeaway. If you're explaining two things, that's two scenes.
- **Concrete before abstract.** Show the specific example first, then generalize. "A pedestrian steps off the curb..." before "This modular pipeline..."
- **Use numbers sparingly but precisely.** When you cite a metric, make it land: "28% lower planning error" not "significant improvement."
- **Transitions are bridges.** End each scene by hinting at the next scene's problem: "...but information gets lost at every boundary" naturally leads to "UniAD asked: what if we connect all these modules?"
- **Conversational, not academic.** Write for someone listening, not reading. Short sentences. Active voice. Questions to create engagement.

Present the script to the user for review before proceeding.

## Phase 3: Assets

**Goal:** Collect visual assets — paper figures, diagrams, screenshots — that the animations will reference.

Create an `assets/` directory in the project folder. Spawn subagents in parallel to find and download relevant images:

- **Paper figures:** Architecture diagrams, result tables, comparison charts from the source papers. Use WebSearch to find paper figures, then WebFetch to download them.
- **Diagrams:** Look for blog posts or presentations that have clean diagrams of the concepts.
- **Screenshots:** For software/tool demos, capture relevant UI screenshots.

Save all assets as PNG files with descriptive names (e.g., `uniad_pipeline.png`, `scaling_laws_loss.png`).

Each scene should have 0-2 asset images. Not every scene needs one — Manim-generated visuals are often better for conceptual explanations. Use paper figures when showing:
- Architecture diagrams that are too complex to recreate
- Quantitative results / comparison tables
- Real-world examples (photos of scenarios, datasets)

## Phase 4: Animate

**Goal:** Write Manim scenes that visually reinforce the narration, timed to match the audio duration.

Create `scenes/[topic]_scenes.py`. Read `references/manim_patterns.md` (bundled with this skill) for the animation vocabulary and patterns to use.

### Scene structure

Every scene class follows this pattern:

```python
class Scene1_Title(Scene):
    def construct(self):
        # 1. Title card (0-3s)
        # 2. Main visual build-up, timed to narration (3s–end-5s)
        # 3. Key takeaway / summary moment (last 3-5s)
```

### Timing rules

- Each `self.wait(N)` and `self.play(..., run_time=N)` adds to the scene clock
- Target total scene duration to match narration length (45-60s)
- Leave ~2s padding at the end for the audio to finish
- Use `self.wait()` generously between visual beats — let the narration breathe

### Global config

Always set at the top of the file:

```python
config.pixel_height = 1080
config.pixel_width = 1920
config.background_color = "#1a1a2e"
```

### Color palette

Use this consistent palette across all scenes:

```python
BLUE_BOX = "#4a90d9"    # Primary / input / perception
GREEN_BOX = "#27ae60"   # Positive / output / results
ORANGE_BOX = "#e67e22"  # Secondary / planning / action
RED_BOX = "#e74c3c"     # Warning / limitation / control
PURPLE_BOX = "#8e44ad"  # Special / decoder / advanced
```

### Layout and positioning — CRITICAL

The most common failure mode is **overlapping text and boxes**. Elements pile on top of each other because positions aren't planned carefully. Follow these rules strictly:

**Use a zone system.** Divide the 1920x1080 frame into three horizontal bands:
- **Top band** (y: 2.0 to 3.5): Title and subtitle ONLY. Use `to_edge(UP, buff=0.4)`.
- **Middle band** (y: -1.5 to 2.0): Main visual content. This is where diagrams, boxes, and illustrations go.
- **Bottom band** (y: -3.5 to -1.5): Key takeaways, results, labels. Use `to_edge(DOWN, buff=0.5)`.

**Never place content without checking what's already there.** Before adding a new element:
- If it goes in the middle band, make sure to `shift()` or `next_to()` relative to existing elements
- If previous content is still on screen, either `FadeOut` it first or explicitly position the new content to avoid it

**Use `next_to()` instead of absolute coordinates.** Hardcoded positions like `move_to(RIGHT * 3 + UP * 1.5)` are fragile — if the element above changes size, things overlap. Instead:
```python
# GOOD: relative positioning
description.next_to(box, DOWN, buff=0.3)
result.next_to(description, DOWN, buff=0.2)

# BAD: absolute positioning that overlaps
description.move_to(UP * 0.5)  # might overlap with box above
result.move_to(DOWN * 0.3)      # might overlap with description
```

**Limit content per screen.** A single screen should have at most:
- 1 title/subtitle
- 3-4 boxes or visual elements in the middle
- 1 label or result at the bottom
- If you need more, clear the screen first with `FadeOut`

**Test positioning mentally.** Before writing animation code for a section, sketch the layout:
```python
# Layout plan for this section:
# TOP:    title at y=3.0
# MIDDLE: three boxes side by side at y=0.5 (total width ~10 units, centered)
# BELOW:  descriptions under each box at y=-0.5
# BOTTOM: result text at y=-2.5
```

### LaTeX gotcha

**Never use `Tex()` or `MathTex()` unless the user confirms LaTeX is installed.** Many systems don't have LaTeX. Always use `Text()` for labels and descriptions. For math expressions, write them as plain text:
```python
# GOOD: works everywhere
Text("Q × K^T / √d_k", font_size=24)

# BAD: requires LaTeX installation
MathTex(r"\frac{QK^T}{\sqrt{d_k}}")
```

### Visual design principles

- **Progressive revelation.** Don't show everything at once. Build diagrams piece by piece, synchronized with narration. When the narrator says "perception detects them," that's when the bounding box appears.
- **Paper figures as anchors.** Load a paper figure with `ImageMobject`, display it full-size for 4-6 seconds so the viewer can absorb it, then shrink it to one side and build explanatory annotations next to it.
- **Whitespace matters.** Don't crowd the frame. The 1920x1080 canvas is generous — use it. Leave at least 0.3 units of buffer between elements.
- **Consistent visual language.** Same colors mean the same things across scenes. Same animation patterns (FadeIn for new concepts, GrowArrow for connections, LaggedStart for lists).
- **Clean up before building.** When transitioning to a new section within a scene, `FadeOut` the previous elements before adding new ones. Don't layer new content on top of old content.

## Phase 5: Voice

**Goal:** Generate professional narration audio for each scene.

Run the bundled `scripts/generate_audio.py` script. It reads `script.md`, extracts narration per scene, and calls ElevenLabs TTS API.

```bash
python <skill-path>/scripts/generate_audio.py <project-dir>/script.md <project-dir>/audio/
```

The script requires the `ELEVENLABS_API_KEY` environment variable. If not set, prompt the user to provide it.

This produces `audio/scene_1.mp3`, `audio/scene_2.mp3`, etc.

After generating audio, check each file's duration:

```bash
for f in <project-dir>/audio/*.mp3; do
  echo "$f: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")s"
done
```

If any audio duration differs significantly (>5s) from the scene animation duration, adjust the Manim scene timing (add/remove `self.wait()` calls) to match.

## Phase 6: Assemble

**Goal:** Combine animations + audio into the final video.

Run the bundled assembly script:

```bash
python <skill-path>/scripts/assemble_video.py <project-dir>
```

This script:
1. Renders each Manim scene: `manim render -qh scenes/[topic]_scenes.py SceneClassName`
2. Merges each rendered video with its audio: `ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac combined/scene_N.mp4`
3. Concatenates all combined scenes into the final video using ffmpeg concat demuxer
4. Outputs `<topic>_explainer.mp4`

If Manim rendering fails, read the error carefully — common issues:
- Missing fonts: use `Text()` not `Tex()` unless LaTeX is installed
- Asset not found: check the `ASSET_DIR` path
- Memory issues with complex scenes: simplify animations or split the scene

## Project Directory Structure

When the skill is done, the project directory should look like:

```
<project-dir>/
├── script.md                    # Narration script
├── scenes/
│   └── <topic>_scenes.py        # Manim source code
│   └── media/                   # Manim render output (auto-generated)
├── assets/                      # Paper figures, diagrams (PNG)
├── audio/                       # Generated narration (MP3)
├── combined/                    # Per-scene video+audio (MP4)
├── concat_list.txt              # FFmpeg concat file (auto-generated)
└── <topic>_explainer.mp4        # Final output video
```

## Gotchas: Audio-Animation Sync

This is the single biggest source of broken videos. The audio and animation are produced independently, then merged — so if they're different lengths, things go wrong in two ways:

### Problem 1: Scene finishes before the audio

The animation ends but the narrator is still talking. FFmpeg uses `-shortest`, so the audio gets cut off. Or worse, the video re-renders or loops trying to fill the gap.

**How to prevent it:**
- After generating audio, measure each scene's audio duration with `ffprobe`
- Compare to the Manim scene's total animation time (sum of all `run_time` + `self.wait()` values)
- The animation should be **2-3 seconds longer** than the audio — the padding at the end is intentional so the last visual has a moment to breathe
- If the animation is shorter than the audio, add `self.wait()` calls — especially at the end of the scene

### Problem 2: Animation moves ahead of narration

The visual for "step 3" appears while the narrator is still explaining "step 2." This happens when `self.wait()` pauses between visual beats are too short.

**How to prevent it:**
- Map each narration sentence to the visual beat it corresponds to. Count the words in each sentence — at ~150 words/minute speaking rate, a 20-word sentence takes ~8 seconds
- The `self.wait()` after each visual beat should be long enough for the narrator to finish the corresponding sentence
- Rule of thumb: **1 second of wait per 2.5 words of narration** for that beat, minus the animation's `run_time`
- When in doubt, add more wait time. A pause in the animation feels natural; an animation that races ahead of narration feels broken

### The sync workflow

After both audio and scenes are written:

```
1. Generate audio files
2. Measure audio durations (ffprobe)
3. Calculate animation durations (sum run_time + wait)
4. Compare per-scene: animation_duration should be >= audio_duration + 2s
5. Adjust self.wait() values until they match
6. Re-render only the scenes that changed
```

The bundled `assemble_video.py` uses `-shortest` in the merge step, which trims the longer track. This is a safety net, not the solution — if you're relying on `-shortest` to fix major mismatches, the sync will be off.

## Subagent Strategy

Parallelize aggressively across independent work:

- **Research phase:** Spawn one subagent per source paper/URL to summarize
- **Asset phase:** Spawn one subagent per scene to find relevant images
- **Rendering phase:** Each Manim scene can be rendered independently

Sequential dependencies:
- Script depends on research
- Animation depends on script + assets
- Audio depends on script
- Assembly depends on animation + audio

So animation and audio can run in parallel once the script is finalized.
