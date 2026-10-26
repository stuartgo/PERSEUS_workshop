"""
Your turn! Copy this file, rename it, and invent a new way to present a paper.

    python examples/starter.py papers/my-paper.pdf

Ideas: a comic strip, a movie trailer, a rap battle between two authors' methods,
a children's bedtime story, a tarot reading, a museum audio guide, a fake product launch...
See the README for more.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel

from paperkit import ask_pdf, generate_image, output_dir, save_wav, speak


class Panel(BaseModel):
    caption: str
    image_prompt: str


class Comic(BaseModel):
    title: str
    panels: list[Panel]


pdf = sys.argv[1] if len(sys.argv) > 1 else sys.exit("usage: python examples/starter.py <paper.pdf>")
out = output_dir(pdf, "starter")

# 1) Ask the model to restructure the paper into whatever shape you need.
comic: Comic = ask_pdf(pdf, "Turn this paper into a 4-panel comic strip that explains its main idea. "
                            "Image prompts: same two characters in every panel, no text in the images.",
                       schema=Comic)

# 2) Turn each piece into media.
for i, panel in enumerate(comic.panels):
    print(f"Panel {i + 1}: {panel.caption}")
    generate_image(panel.image_prompt, out / f"panel_{i + 1}.png", size="1024x1024", quality="low")

# 3) Bonus: a voice reading the captions.
save_wav(speak(" ".join(p.caption for p in comic.panels), voice="coral"), out / "captions.wav")
print(f"Done -> {out}")
