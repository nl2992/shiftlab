"""Assemble the three hand-made-style composites: the illustrated scenes were generated (Codex native image generation,
prompts in assets_raw/*_prompt.txt) and the data panels, drawn in Python by fig_panels.py, are pasted into the reserved
areas. Writes fig_overview.{png,pdf} and fig_pipeline.{png,pdf}."""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
RAW = HERE / "assets_raw"


def paste_fit(base, panel, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    pw, ph = panel.size
    s = min(w / pw, h / ph)
    p = panel.resize((int(pw * s), int(ph * s)), Image.LANCZOS)
    base.alpha_composite(p, (x0 + (w - p.size[0]) // 2, y0 + (h - p.size[1]) // 2))


def save(im, name):
    rgb = im.convert("RGB")
    rgb.save(HERE / f"{name}.png", dpi=(300, 300))
    rgb.save(HERE / f"{name}.pdf", resolution=300)


# overview: chart into the reserved panel b
ov = Image.open(RAW / "overview_gen1.png").convert("RGBA")
paste_fit(ov, Image.open(RAW / "panel_exceedance.png").convert("RGBA"), (1148, 190, 1655, 822))
save(ov, "fig_overview")

# pipeline: four motifs into the four reserved areas
pl = Image.open(RAW / "pipeline_gen1.png").convert("RGBA")
for k, x0 in enumerate((17, 517, 1016, 1515)):
    paste_fit(pl, Image.open(RAW / f"motif_{k + 1}.png").convert("RGBA"), (x0 + 22, 188, x0 + 430, 478))
save(pl, "fig_pipeline")
# the mechanism figure is now one canvas, see fig_mechanism_scene.py
print("composed")
