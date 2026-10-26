"""
Example 1 — PDF -> poster.

    python examples/paper_to_poster.py papers/my-paper.pdf
    python examples/paper_to_poster.py papers/my-paper.pdf --style "1970s sci-fi movie poster"
    python examples/paper_to_poster.py papers/my-paper.pdf --mode layout --style "clean Swiss design"

Two modes:
  image   (default)  The image model draws the WHOLE poster, text included. Most striking;
                     small text can occasionally come out wrong, so keep it short.
  layout             The image model only draws the illustration; the text is laid out in an
                     HTML page (exact text, print to PDF/A3 from your browser).

Pipeline:  PDF --(Responses API, structured output)--> poster content
               --(Images API)--> poster.png   or   illustration.png + poster.html
Output:    output/<paper>/poster/
"""

import argparse
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `import paperkit` works

from pydantic import BaseModel, Field

from paperkit import ask_pdf, generate_image, output_dir


class Block(BaseModel):
    heading: str = Field(description="1-4 words")
    text: str = Field(description="One short sentence, max ~18 words")


class Poster(BaseModel):
    title: str = Field(description="Punchy poster title, max 6 words")
    tagline: str = Field(description="One line that sells the idea, max 12 words")
    big_number: str = Field(description="The single most striking number/result FROM THE PAPER with a few "
                                        "words of context (e.g. '3x faster training'), or '' if none")
    blocks: list[Block] = Field(description="Exactly 3 blocks: The problem / The idea / The result (or similar)")
    credit: str = Field(description="Paper title, first author et al., year")
    visual_concept: str = Field(description="The central illustration: one strong visual metaphor for the "
                                            "paper's idea. Describe subject, composition, colours.")


PROMPT = """You design posters that make people want to read a research paper.

Read the attached paper and write the content for a poster in this style: {style}.
- Audience: {audience}.
- Very little text: posters are read from 3 metres away. Respect the word limits.
- Be accurate: every claim and number must come from the paper.
- The visual concept should be a bold, memorable metaphor, not a chart or a diagram from the paper.
  No real people, no logos."""


def image_prompt(p: Poster, style: str) -> str:
    """Everything the image model needs to draw the full poster, with the exact text to render."""
    blocks = "\n".join(f'  - heading "{b.heading}" with text "{b.text}"' for b in p.blocks)
    big = f'\n- A large highlighted figure: "{p.big_number}"' if p.big_number else ""
    return f"""A finished, professionally designed portrait poster. Style: {style}.

Central illustration: {p.visual_concept}

Render this text exactly, spelled correctly, with a clear typographic hierarchy:
- Title (largest): "{p.title}"
- Tagline under the title: "{p.tagline}"{big}
- Three small info blocks near the bottom:
{blocks}
- Small credit line at the very bottom: "{p.credit}"

Generous margins, strong composition, legible text, no other text or logos."""


def render_html(p: Poster, style: str) -> str:
    """Layout mode: exact text in HTML around the generated illustration. Print to PDF for A3/A2."""
    e = html.escape
    blocks = "".join(f"<div class='block'><h3>{e(b.heading)}</h3><p>{e(b.text)}</p></div>" for b in p.blocks)
    big = f"<div class='big'>{e(p.big_number)}</div>" if p.big_number else ""
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(p.title)}</title>
<!-- style requested: {e(style)} -->
<style>
 @page {{ size: A3 portrait; margin: 0 }}
 :root {{ --ink:#141414; --paper:#f6f1e7; --accent:#e4572e }}
 * {{ box-sizing:border-box }}
 body {{ margin:0; background:#ccc; font-family: "Helvetica Neue", Arial, sans-serif; color:var(--ink) }}
 .poster {{ width:min(100vw, 297mm); aspect-ratio: 297/420; margin:0 auto; background:var(--paper);
           display:flex; flex-direction:column; padding:4%; gap:2.5% }}
 .art {{ flex:1; min-height:0; border-radius:8px; overflow:hidden }}
 .art img {{ width:100%; height:100%; object-fit:cover; display:block }}
 h1 {{ font-size:clamp(28px,7vw,92px); line-height:.95; margin:0; letter-spacing:-.02em; text-transform:uppercase }}
 .tag {{ font-size:clamp(14px,2.4vw,30px); margin:.4em 0 0 }}
 .big {{ font-size:clamp(20px,4.5vw,58px); font-weight:800; color:var(--accent) }}
 .blocks {{ display:grid; grid-template-columns:repeat(3,1fr); gap:3%; border-top:3px solid var(--ink); padding-top:2% }}
 .block h3 {{ margin:0 0 .3em; font-size:clamp(12px,1.8vw,22px); text-transform:uppercase; color:var(--accent) }}
 .block p {{ margin:0; font-size:clamp(11px,1.5vw,18px); line-height:1.35 }}
 .credit {{ font-size:clamp(9px,1.1vw,13px); opacity:.7 }}
 @media print {{ body {{ background:none }} .poster {{ width:297mm; height:420mm }} }}
</style></head><body><div class="poster">
 <div><h1>{e(p.title)}</h1><p class="tag">{e(p.tagline)}</p></div>
 <div class="art"><img src="illustration.png" alt=""></div>
 {big}<div class="blocks">{blocks}</div><div class="credit">{e(p.credit)}</div>
</div></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf")
    parser.add_argument("--mode", choices=["image", "layout"], default="image")
    parser.add_argument("--style", default="bold modern science-festival poster, flat illustration, vivid colours")
    parser.add_argument("--audience", default="curious non-experts walking past")
    parser.add_argument("--quality", choices=["low", "medium", "high"], default="high",
                        help="image quality; 'low' is much cheaper for drafts")
    args = parser.parse_args()

    out = output_dir(args.pdf, "poster")

    print("📄 Reading the paper and writing the poster content...")
    poster: Poster = ask_pdf(args.pdf, PROMPT.format(style=args.style, audience=args.audience), schema=Poster)
    (out / "poster.json").write_text(poster.model_dump_json(indent=2), encoding="utf-8")

    if args.mode == "image":
        print("🎨 Drawing the poster (this can take a minute)...")
        prompt = image_prompt(poster, args.style)
        (out / "image_prompt.txt").write_text(prompt, encoding="utf-8")
        result = generate_image(prompt, out / "poster.png", size="1024x1536", quality=args.quality)
    else:
        print("🎨 Drawing the illustration...")
        generate_image(f"{poster.visual_concept}\nStyle: {args.style}. No text, no letters, no logos.",
                       out / "illustration.png", size="1024x1536", quality=args.quality)
        result = out / "poster.html"
        result.write_text(render_html(poster, args.style), encoding="utf-8")
        print("   Tip: open it in a browser and Print -> Save as PDF (A3) for a print-ready poster.")

    print(f"\n✅ Done: {result}\n")
    print(poster.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
