# Manim Animation Patterns Reference

Common patterns for building first-principles explainer videos. All examples use Manim Community v0.19.0+.

## Table of Contents
1. [Setup & Config](#setup--config)
2. [Title Cards](#title-cards)
3. [Pipeline / Flow Diagrams](#pipeline--flow-diagrams)
4. [Paper Figure Display](#paper-figure-display)
5. [Progressive Lists](#progressive-lists)
6. [Comparison Layouts](#comparison-layouts)
7. [Data Visualization](#data-visualization)
8. [Concept Illustrations](#concept-illustrations)
9. [Transitions & Timing](#transitions--timing)

---

## Layout Zones

The frame is 1920x1080 (Manim coordinate range: roughly x=-7 to 7, y=-4 to 4). Divide it into three bands to prevent overlapping:

```
y=3.5  ┌─────────────────────────────────────────┐
       │           TOP: Title + Subtitle           │
y=2.0  ├─────────────────────────────────────────┤
       │                                           │
       │         MIDDLE: Main Visual Content       │
       │    (boxes, diagrams, paper figures)        │
       │                                           │
y=-1.5 ├─────────────────────────────────────────┤
       │       BOTTOM: Results, Takeaways          │
y=-3.5 └─────────────────────────────────────────┘
```

**Golden rules:**
1. Use `next_to()` for relative positioning, not `move_to()` with hardcoded coordinates
2. Max 3-4 visual elements in the middle band at once
3. `FadeOut` previous content before adding new content in the same zone
4. Always leave `buff=0.3` minimum between elements

```python
# Layout template for a typical section
title.to_edge(UP, buff=0.4)                    # y ≈ 3.2
subtitle.next_to(title, DOWN, buff=0.15)       # y ≈ 2.7

# Middle content — use arrange() for groups
boxes = VGroup(box1, box2, box3)
boxes.arrange(RIGHT, buff=1.0)
boxes.move_to(ORIGIN + UP * 0.3)               # centered in middle band

# Descriptions under each box
for box, desc in zip(boxes, descriptions):
    desc.next_to(box, DOWN, buff=0.3)

# Bottom result
result.to_edge(DOWN, buff=0.5)                 # y ≈ -3.0
```

**Before adding new content to a zone, clear it:**
```python
# Clear middle zone before showing new content
self.play(
    *[FadeOut(m) for m in [old_box, old_label, old_arrow]],
    run_time=0.8,
)
self.wait(1)
# Now safe to add new elements in the middle
```

---

## Setup & Config

```python
from __future__ import annotations
from manim import *
import os

config.pixel_height = 1080
config.pixel_width = 1920
config.background_color = "#1a1a2e"

ASSET_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")

def asset(name: str) -> str:
    return os.path.join(ASSET_DIR, name)

# Color palette
BLUE_BOX = "#4a90d9"
GREEN_BOX = "#27ae60"
ORANGE_BOX = "#e67e22"
RED_BOX = "#e74c3c"
PURPLE_BOX = "#8e44ad"
```

---

## Title Cards

Every scene starts with a title (1.5s write) + optional subtitle (0.8s fade), then a 2s pause.

```python
# Simple title
title = Text("The Autonomous-Driving Stack", font_size=44, color=WHITE, weight=BOLD)
title.to_edge(UP, buff=0.5)
self.play(Write(title), run_time=1.5)
self.wait(2)

# Title + subtitle
title = Text("UniAD — Unified Autonomous Driving", font_size=40, color=WHITE, weight=BOLD)
subtitle = Text("CVPR 2023 Best Paper", font_size=24, color=YELLOW)
title.to_edge(UP, buff=0.4)
subtitle.next_to(title, DOWN, buff=0.15)
self.play(Write(title), run_time=1.5)
self.play(FadeIn(subtitle), run_time=0.8)
self.wait(2)
```

---

## Pipeline / Flow Diagrams

For showing step-by-step processes (perception → prediction → planning → control).

### Box helper

```python
def pipeline_box(label: str, color: str, question: str | None = None) -> VGroup:
    rect = RoundedRectangle(
        corner_radius=0.15, width=2.8, height=1.2, color=color,
        fill_opacity=0.25, stroke_width=3,
    )
    title = Text(label, font_size=28, color=WHITE, weight=BOLD)
    title.move_to(rect.get_center())
    grp = VGroup(rect, title)
    if question:
        q = Text(question, font_size=18, color=YELLOW, slant=ITALIC)
        q.next_to(rect, DOWN, buff=0.15)
        grp.add(q)
    return grp
```

### Arrow helper

```python
def connecting_arrow(src: Mobject, dst: Mobject, color=WHITE) -> Arrow:
    return Arrow(
        src.get_right(), dst.get_left(),
        buff=0.1, color=color, stroke_width=3,
        max_tip_length_to_length_ratio=0.15,
    )
```

### Usage — reveal boxes one by one, then arrows

```python
boxes = VGroup(box1, box2, box3, box4)
boxes.arrange(RIGHT, buff=1.0)
boxes.move_to(ORIGIN + UP * 0.3)

for box in boxes:
    self.play(FadeIn(box, shift=UP * 0.3), run_time=1.2)
    self.wait(1.5)

arrows = VGroup(*[connecting_arrow(a[0], b[0]) for a, b in zip(boxes[:-1], boxes[1:])])
for ar in arrows:
    self.play(GrowArrow(ar), run_time=0.8)
self.wait(2)
```

### Vertical module stack (for architectures)

```python
modules = ["TrackFormer", "MapFormer", "MotionFormer", "OccFormer", "Planner"]
colors = [BLUE_BOX, "#3498db", GREEN_BOX, PURPLE_BOX, ORANGE_BOX]
rects = VGroup()
for m, c in zip(modules, colors):
    r = RoundedRectangle(corner_radius=0.1, width=2.4, height=0.6, color=c,
                         fill_opacity=0.25, stroke_width=2)
    t = Text(m, font_size=20, color=WHITE)
    t.move_to(r)
    rects.add(VGroup(r, t))
rects.arrange(DOWN, buff=0.3)
rects.move_to(RIGHT * 3.5)

for rect in rects:
    self.play(FadeIn(rect, shift=LEFT * 0.2), run_time=0.8)
    self.wait(0.8)
```

---

## Paper Figure Display

Show a paper figure full-size, let it sink in, then shrink to the side and annotate.

```python
# Full display
img = ImageMobject(asset("architecture.png"))
img.scale_to_fit_width(10)
img.move_to(ORIGIN)
self.play(FadeIn(img), run_time=1.5)
self.wait(5)  # Let viewer absorb the figure

# Shrink and annotate
self.play(img.animate.scale(0.45).to_edge(LEFT, buff=0.4).shift(DOWN * 0.5), run_time=1)
self.wait(1)
# Now build annotations on the right side of the screen
```

---

## Progressive Lists

Reveal bullet points one at a time, synced with narration.

### Results list (colored)

```python
results = VGroup(
    Text("-28%  planning error", font_size=26, color=GREEN),
    Text("+20%  tracking accuracy", font_size=26, color=GREEN),
    Text("+30%  mapping quality", font_size=26, color=GREEN),
)
results.arrange(DOWN, aligned_edge=LEFT, buff=0.25)
results.to_edge(DOWN, buff=0.6).shift(RIGHT * 1)

for r in results:
    self.play(FadeIn(r, shift=LEFT * 0.3), run_time=0.8)
    self.wait(1)
self.wait(3)
```

### Limitations list

```python
lims = ["Only 4 frames of context", "Camera-only (no LiDAR)", "Too expensive without distillation"]
lim_texts = VGroup(*[Text(f"• {l}", font_size=18, color="#ff6b6b") for l in lims])
lim_texts.arrange(DOWN, aligned_edge=LEFT, buff=0.15)

for lt in lim_texts:
    self.play(FadeIn(lt, shift=LEFT * 0.2), run_time=0.6)
    self.wait(1)
```

### Reasoning chain (tagged steps)

```python
steps = [
    ("R1", "Scene: Urban intersection", BLUE_BOX),
    ("R2", "Critical: Pedestrian detected", RED_BOX),
    ("R3", "Behavior: Crossing left-to-right", GREEN_BOX),
    ("R4", "Decision: YIELD", ORANGE_BOX),
]
step_grp = VGroup()
for tag, text, color in steps:
    tag_t = Text(f"{tag}:", font_size=20, color=color, weight=BOLD)
    body_t = Text(text, font_size=18, color=WHITE)
    row = VGroup(tag_t, body_t).arrange(RIGHT, buff=0.15)
    step_grp.add(row)
step_grp.arrange(DOWN, aligned_edge=LEFT, buff=0.25)

for s in step_grp:
    self.play(FadeIn(s, shift=RIGHT * 0.3), run_time=1)
    self.wait(2)
```

---

## Comparison Layouts

### Side-by-side boxes

```python
# "Old" approach vs "New" approach
old_box = RoundedRectangle(corner_radius=0.1, width=3.5, height=2.5,
                           color=RED_BOX, fill_opacity=0.1, stroke_width=2)
old_title = Text("ADE Metric", font_size=22, color=RED_BOX, weight=BOLD)
old_title.next_to(old_box, UP, buff=0.1)
old_desc = Text("Single ground truth\nFails for multi-modal", font_size=16, color=WHITE)
old_desc.move_to(old_box)

new_box = RoundedRectangle(corner_radius=0.1, width=3.5, height=2.5,
                           color=GREEN_BOX, fill_opacity=0.1, stroke_width=2)
# ... same pattern

old_box.move_to(LEFT * 2.5)
new_box.move_to(RIGHT * 2.5)
```

### Strikethrough comparison

```python
sup = Text("Supervised (VAD): 0.37 m", font_size=28, color="#aaaaaa")
cross = Line(sup.get_left(), sup.get_right(), color=RED, stroke_width=3)
self.play(FadeIn(sup), run_time=0.8)
self.play(Create(cross), run_time=0.5)

better = Text("Self-supervised (S4): 0.31 m", font_size=28, color=GREEN, weight=BOLD)
better.next_to(sup, DOWN, buff=0.35)
self.play(FadeIn(better, shift=LEFT * 0.3), run_time=0.8)
```

---

## Data Visualization

### Power-law curve

```python
axes = Axes(
    x_range=[0, 4, 1], y_range=[0, 2, 0.5],
    x_length=3, y_length=1.5,
    axis_config={"color": WHITE, "stroke_width": 1.5, "include_tip": False},
)
curve = axes.plot(lambda x: 1.8 / (x + 0.5) ** 0.6, x_range=[0.1, 4], color=YELLOW)
label = Text("Loss ~ Compute^(-a)", font_size=20, color=YELLOW)
label.next_to(axes, UP, buff=0.15)

self.play(Create(axes), run_time=0.8)
self.play(Create(curve), FadeIn(label), run_time=1.2)
```

### Waypoint trajectories

```python
waypoints = VGroup()
start = RIGHT * 1.5 + DOWN * 2
for i in range(8):
    dot = Dot(start + RIGHT * i * 0.45 + UP * (0.05 * i ** 1.3),
              radius=0.07, color=YELLOW)
    waypoints.add(dot)

self.play(
    LaggedStart(*[FadeIn(d, scale=0.5) for d in waypoints], lag_ratio=0.15),
    run_time=1.5,
)
```

---

## Concept Illustrations

### Stick figure (pedestrian, person)

```python
head = Circle(radius=0.15, color=WHITE, stroke_width=2).shift(DOWN * 2.2 + LEFT * 3)
body = Line(head.get_bottom(), head.get_bottom() + DOWN * 0.5, color=WHITE, stroke_width=2)
left_leg = Line(body.get_end(), body.get_end() + DL * 0.3, color=WHITE, stroke_width=2)
right_leg = Line(body.get_end(), body.get_end() + DR * 0.3, color=WHITE, stroke_width=2)
left_arm = Line(body.get_center(), body.get_center() + LEFT * 0.3 + DOWN * 0.15, color=WHITE, stroke_width=2)
right_arm = Line(body.get_center(), body.get_center() + RIGHT * 0.3 + DOWN * 0.15, color=WHITE, stroke_width=2)
stick = VGroup(head, body, left_leg, right_leg, left_arm, right_arm)
```

### Bounding box detection

```python
bbox = SurroundingRectangle(target_mobject, color=BLUE_BOX, buff=0.15, stroke_width=2)
label = Text("Detected", font_size=16, color=BLUE_BOX)
label.next_to(bbox, UP, buff=0.05)
self.play(Create(bbox), FadeIn(label), run_time=1)
```

### Architecture — dual system (Think Fast/Slow)

```python
s1_rect = RoundedRectangle(corner_radius=0.15, width=4, height=2.5,
                           color=BLUE_BOX, fill_opacity=0.15, stroke_width=3)
s1_rect.move_to(LEFT * 3.5)
s1_title = Text("System 1: FAST", font_size=24, color=BLUE_BOX, weight=BOLD)
s1_title.next_to(s1_rect, UP, buff=0.1)

s2_rect = RoundedRectangle(corner_radius=0.15, width=4, height=2.5,
                           color=GREEN_BOX, fill_opacity=0.15, stroke_width=3)
s2_rect.move_to(RIGHT * 3.5)
s2_title = Text("System 2: SLOW", font_size=24, color=GREEN_BOX, weight=BOLD)
s2_title.next_to(s2_rect, UP, buff=0.1)

# Connect both to a shared output
output_rect = RoundedRectangle(corner_radius=0.15, width=5, height=1.2,
                               color=PURPLE_BOX, fill_opacity=0.15, stroke_width=3)
output_rect.move_to(DOWN * 2.8)
arr1 = Arrow(s1_rect.get_bottom(), output_rect.get_top() + LEFT * 1.5, buff=0.1, ...)
arr2 = Arrow(s2_rect.get_bottom(), output_rect.get_top() + RIGHT * 1.5, buff=0.1, ...)
```

### Triangle relationship (3 roles)

```python
# Place 3 boxes in a triangle and connect with DoubleArrows
top = RoundedRectangle(...).move_to(UP * 0.3)
bl = RoundedRectangle(...).move_to(DOWN * 1.8 + LEFT * 2.5)
br = RoundedRectangle(...).move_to(DOWN * 1.8 + RIGHT * 2.5)

arrows = VGroup(
    DoubleArrow(top.get_bottom() + DL * 0.1, bl.get_top() + UR * 0.1, ...),
    DoubleArrow(top.get_bottom() + DR * 0.1, br.get_top() + UL * 0.1, ...),
    DoubleArrow(bl.get_right(), br.get_left(), ...),
)
```

---

## Transitions & Timing

### Clearing the screen

```python
# Fade out everything except title
self.play(
    *[FadeOut(m) for m in self.mobjects if m is not title],
    run_time=1,
)
self.wait(1)
```

### Key number reveal (hero stat)

```python
stat = Text("0.32 m Avg L2  (SOTA)", font_size=32, color=GREEN, weight=BOLD)
self.play(FadeIn(stat, scale=1.5), run_time=1)
self.wait(2)
```

### Timing checklist

- Title card: 3-4s total (1.5s write + 0.8s subtitle + 1.5s wait)
- Paper figure: 6-8s (1.5s fade in + 5s absorb + 1s shrink)
- Each bullet/step: 2-3s (0.8s animation + 1-2s wait)
- Section transition: 2s (1s fade out + 1s wait)
- End of scene: 3-4s final wait

### Animation speed guide

| Animation | Typical run_time |
|-----------|-----------------|
| Write(title) | 1.5s |
| FadeIn(subtitle) | 0.8s |
| FadeIn(box, shift=...) | 0.8-1.2s |
| GrowArrow | 0.6-0.8s |
| Create(shape) | 0.8-1.0s |
| LaggedStart (list) | 1.5s total |
| FadeOut (cleanup) | 0.8-1.0s |
