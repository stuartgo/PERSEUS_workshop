"""
Example — PDF -> cartoon comic, written for one specific audience.

    python examples/paper_to_comic.py papers/attention.pdf                    # both audiences
    python examples/paper_to_comic.py papers/attention.pdf --audience business
    python examples/paper_to_comic.py papers/attention.pdf --audience school --quality low
    python examples/paper_to_comic.py papers/attention.pdf --text-only        # script only, no images (cheap)
    python examples/paper_to_comic.py papers/attention.pdf --reuse-script     # keep comic.json, redraw images

Two ready-made audiences show how the same paper becomes two very different comics:
  business  Business people at an "AI in business" conference: adults with deep industry
            knowledge and minimal technical experience. Two A4 pages.
  school    15-year-olds visiting a university science fair who know nothing about AI.
            Two short, simple comic strips.

Pipeline:  PDF --(Responses API, structured output)--> comic script (cast, panels, dialogue, facts)
               --(Images API)--> character sheet --> one picture per panel, drawn from that sheet
               --> comic.html with the exact words in captions and speech bubbles --> comic.pdf
Output:    output/<paper>/comic-<audience>/  (comic.html, comic.pdf, comic.json, script.md, PNGs)

The image model only draws pictures. All words are added in HTML, so they are spelled exactly as
written (image models still garble lettering). To make your own version, edit AUDIENCES below.
"""

import argparse
import base64
import html
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `import paperkit` works

from pydantic import BaseModel, Field

from paperkit import IMAGE_MODEL, ask_pdf, client, generate_image, html_to_pdf, output_dir

# --------------------------------------------------------------------------
# The audiences. This is the part to rewrite first.
# --------------------------------------------------------------------------

AUDIENCES = {
    "business": {
        "persona": """Delegates at a business conference session called "AI in practice: where it pays off".
They are adults (30-60): managers, directors, consultants and founders from logistics, finance, retail,
healthcare administration and manufacturing. They have extensive industry knowledge (budgets, operations,
customers, regulation, change management) but minimal technical experience: they use ChatGPT or Copilot
now and then, have never written code, and switch off at maths or acronyms.
Typical reader: Ingrid, 52, operations director at a regional logistics firm. Her board keeps asking
"what is our AI strategy?". She wants to understand, in business terms, what this research changed: what
problem it solved, what it made faster or cheaper, and why that matters for decisions she makes. She will
read the comic in a coffee break, in about five minutes, and should be able to repeat the main point to
her CEO the next day. She cares about speed, cost, quality, scale and risk, and distrusts hype.""",
        "format": """Two A4 portrait pages, like a short comic feature in a business magazine.
Page 1: the old way of doing things and its bottleneck, then the paper's idea.
Page 2: the results and what changed, ending with a clear takeaway for business.
Mark 1-2 panels per page as `wide` (an establishing shot or the key moment).""",
        "writing": """Plain, confident English. No equations and no jargon. When you must name something
technical, introduce it through an analogy from their working world (an office, a meeting, a warehouse,
a supply chain), then use the term consistently. Treat them as smart, experienced professionals, never
as children. Dry, witty tone, like a good business-magazine cartoon. Narration boxes at most ~30 words,
speech bubbles at most ~20 words, at most 2 bubbles per panel. Be honest about scope: say what the paper
actually tested and do not overclaim. The `takeaway` is one sentence Ingrid could say to her board.""",
        "cast": """2-3 professionals from the readers' own world (different ages and backgrounds), e.g. a
sceptical executive and a colleague who explains. No real people.""",
        "style": """clean editorial magazine cartoon: confident ink lines, flat muted colours (navy, slate
grey, warm ochre, off-white), modern office and city settings, subtle visual humour""",
        "unit": "page",
        "sections": 2,
        "panels": (5, 6),
    },
    "school": {
        "persona": """15-year-olds visiting a university on a science-fair day, wandering between stands with
friends. They know nothing about AI or computer science beyond using apps on their phones (autocorrect,
translation apps, video recommendations, maybe a chatbot) and have no idea how any of it works.
Typical reader: Sam, 15, likes football and gaming, finds most school science "fine, I guess", and will
stop at a stand for one or two minutes if something looks funny or cool. Reads on the move, has a short
attention span, and is allergic to anything that feels like a lesson or tries too hard to sound cool.""",
        "format": """Two short comic strips printed one above the other on a single page, like newspaper strips.
Strip 1: the problem and the big idea, told through an everyday situation.
Strip 2: why it matters, ending on a punchline. Each strip should make sense on its own.""",
        "writing": """Very simple words and short sentences: speech bubbles at most ~12 words, narration at
most ~15 words, at most 2 bubbles per panel. No technical terms; if you need one word from the paper,
explain it in the same panel with an everyday comparison. Use one clear analogy from teenage life
(group chats, games, school, friends). Funny and warm, never babyish, no forced slang.
The `takeaway` is one sentence a 15-year-old could tell a friend.""",
        "cast": """2 teenagers the readers can recognise themselves in, plus optionally one non-human
sidekick (e.g. a small friendly robot). No real people.""",
        "style": """bright, bold cartoon like a modern animated TV series: thick black outlines, saturated
colours, big expressive faces, dynamic camera angles, playful exaggeration""",
        "unit": "strip",
        "sections": 2,
        "panels": (3, 4),
    },
}

PROMPT = """You are an award-winning cartoonist and science communicator.
Read the attached research paper and write a cartoon comic about it for the audience below.

AUDIENCE
{persona}

FORMAT
{format}
Return exactly {sections} sections (one per {unit}), each with {pmin}-{pmax} panels.

WRITING
{writing}

ACCURACY
- Every claim about the research must come from the paper. Use numbers only as the paper states them,
  together with what they are compared against.
- If you mention anything that is not in the paper (for example later products built on the idea), make
  clear in the comic that it came later, and keep it to general, well-known facts.
- The analogy may simplify, but must not say anything false about how the method works.
- List every factual claim you used in `facts`, each with where it comes from (paper section, table, or
  "general knowledge, not from the paper").

CHARACTERS AND PICTURES
- Cast: {cast} Describe each character's look precisely (age, build, skin tone, hair, clothing with
  colours, one distinctive accessory) so an illustrator can draw them identically in every panel.
- For each panel, `scene` describes ONLY what is drawn: setting, which characters, poses, expressions,
  camera angle, props. Keep the main action in the centre of the frame; a caption box is placed over the
  top-left corner and speech bubbles go below the picture.
- No words, letters, numbers, signs or labels inside the pictures; all text is added separately.
  Visual metaphors are welcome (e.g. words shown as blank tiles, connections as glowing threads)."""


class Character(BaseModel):
    name: str
    role: str = Field(description="Their role in the story, max 10 words")
    look: str = Field(description="Precise visual description for the illustrator, 30-50 words")


class Line(BaseModel):
    speaker: str = Field(description="A character name from the cast")
    text: str


class Panel(BaseModel):
    narration: str = Field(description="Caption box text, or '' for none")
    dialogue: list[Line] = Field(description="0-2 speech bubbles")
    characters: list[str] = Field(description="Names of the cast members visible in this panel")
    scene: str = Field(description="What is drawn (no text in the picture), 40-80 words")
    wide: bool = Field(description="True if this panel spans the full width of the page")


class Section(BaseModel):
    heading: str = Field(description="Short heading for this page or strip, max 6 words")
    panels: list[Panel]


class Fact(BaseModel):
    claim: str
    source: str = Field(description="Where in the paper, or 'general knowledge, not from the paper'")


class Comic(BaseModel):
    title: str = Field(description="Catchy comic title, max 8 words")
    tagline: str = Field(description="One-line subtitle, max 15 words")
    key_message: str = Field(description="The one thing the reader should remember tomorrow")
    takeaway: str = Field(description="Final takeaway sentence, printed at the end of the comic")
    paper_citation: str = Field(description="Short citation: 'Authors (Year). Title.'")
    cast: list[Character]
    sections: list[Section]
    facts: list[Fact]


# --------------------------------------------------------------------------
# Pictures
# --------------------------------------------------------------------------

PANEL_SIZE = "1536x1024"


def cast_text(comic: Comic, names: list[str] | None = None) -> str:
    chars = [c for c in comic.cast if names is None or c.name in names] or comic.cast
    return "\n".join(f"- {c.name}: {c.look}" for c in chars)


def draw_cast_sheet(comic: Comic, style: str, path: Path, quality: str) -> Path:
    prompt = (f"Character reference sheet for a cartoon comic. Style: {style}.\n"
              f"Draw each character full body, front view, standing side by side, evenly spaced, "
              f"on a plain white background:\n{cast_text(comic)}\n"
              "No text, no names, no labels, no letters.")
    return generate_image(prompt, path, size=PANEL_SIZE, quality=quality)


def draw_panel(comic: Comic, panel: Panel, style: str, sheet: Path, path: Path, quality: str) -> Path:
    """Draw one panel, passing the character sheet as a reference image so the cast stays consistent."""
    def prompt(reference: bool) -> str:
        how = ("The attached image is the character sheet: draw these characters exactly as they look there"
               if reference else "Draw the characters exactly as described")
        return (f"A single comic panel. Style: {style}.\n"
                f"{how} (same faces, hair, skin tone, clothes and colours).\n"
                f"Characters in this panel:\n{cast_text(comic, panel.characters)}\n"
                f"Scene: {panel.scene}\n"
                "Keep the main action in the centre. No text, letters, numbers, speech bubbles, captions, "
                "signs or panel borders in the image.")

    try:
        with open(sheet, "rb") as ref:
            result = client().images.edit(model=IMAGE_MODEL, image=[ref], prompt=prompt(True),
                                          size=PANEL_SIZE, quality=quality)
        path.write_bytes(base64.b64decode(result.data[0].b64_json))
        return path
    except Exception as err:  # e.g. the image model does not accept reference images
        print(f"   (reference drawing failed for {path.name}: {err}; drawing from the text only)")
        return generate_image(prompt(False), path, size=PANEL_SIZE, quality=quality)


# --------------------------------------------------------------------------
# Layout: exact text in HTML around the pictures, printed to PDF
# --------------------------------------------------------------------------

def fill_rows(panels: list[Panel]) -> None:
    """In a 2-column page, widen a panel that would otherwise sit alone in its row."""
    col = 0
    for i, p in enumerate(panels):
        if p.wide:
            col = 0
            continue
        next_wide = i + 1 == len(panels) or panels[i + 1].wide
        if col == 0 and next_wide:
            p.wide = True
        else:
            col = 1 - col


def render_html(comic: Comic, unit: str, folder: Path) -> str:
    e = html.escape
    strips = unit == "strip"

    def panel_html(s: int, i: int, p: Panel) -> str:
        img = folder / f"panel_{s + 1}_{i + 1}.png"
        art = (f"<img src='{img.name}' alt=''>" if img.exists()
               else f"<div class='placeholder'>{e(p.scene)}</div>")
        cap = f"<div class='caption'>{e(p.narration)}</div>" if p.narration else ""
        talk = "".join(f"<div class='bubble'><b>{e(l.speaker)}</b> {e(l.text)}</div>" for l in p.dialogue)
        wide = " wide" if p.wide and not strips else ""
        return (f"<div class='panel{wide}'><div class='art'>{art}{cap}</div>"
                f"{f'<div class=talk>{talk}</div>' if talk else ''}</div>")

    def section_html(s: int, sec: Section) -> str:
        if not strips:
            fill_rows(sec.panels)
        cols = f"style='grid-template-columns:repeat({len(sec.panels)},1fr)'" if strips else ""
        panels = "".join(panel_html(s, i, p) for i, p in enumerate(sec.panels))
        return f"<div class='section'><h2>{e(sec.heading)}</h2><div class='grid' {cols}>{panels}</div></div>"

    header = f"<header><h1>{e(comic.title)}</h1><p>{e(comic.tagline)}</p></header>"
    footer = (f"<footer><div class='takeaway'>{e(comic.takeaway)}</div>"
              f"<small>Based on {e(comic.paper_citation)} Script and pictures made with AI.</small></footer>")
    sections = [section_html(s, sec) for s, sec in enumerate(comic.sections)]
    if strips:  # both strips on one landscape page
        sheets = [header + "".join(sections) + footer]
    else:       # one A4 page per section
        sheets = [(header if s == 0 else "") + sec + (footer if s == len(sections) - 1 else "")
                  for s, sec in enumerate(sections)]
    w, h = (297, 210) if strips else (210, 297)
    base = 3.6 if strips else 3.1  # text size in mm

    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(comic.title)}</title>
<link href="https://fonts.googleapis.com/css2?family=Bangers&family=Comic+Neue:wght@400;700&display=swap" rel="stylesheet">
<style>
 @page {{ size: {w}mm {h}mm; margin: 0 }}
 * {{ box-sizing: border-box }}
 body {{ margin: 0; background: #888; font-family: "Comic Neue", "Comic Sans MS", sans-serif; color: #111 }}
 .sheet {{ width: {w}mm; height: {h}mm; margin: 8mm auto; padding: 9mm; background: #fff;
          display: flex; flex-direction: column; gap: 3mm; overflow: hidden; break-after: page }}
 header h1 {{ font-family: Bangers, Impact, sans-serif; font-weight: 400; letter-spacing: .04em;
             font-size: {base * 3}mm; margin: 0; line-height: 1 }}
 header p {{ margin: 1mm 0 0; font-size: {base * 1.15}mm; font-weight: 700 }}
 .section {{ flex: 1; min-height: 0; display: flex; flex-direction: column; gap: 1.5mm }}
 h2 {{ font-family: Bangers, Impact, sans-serif; font-weight: 400; letter-spacing: .04em;
       font-size: {base * 1.5}mm; margin: 0 }}
 .grid {{ flex: 1; min-height: 0; display: grid; grid-template-columns: 1fr 1fr;
         grid-auto-rows: minmax(0, 1fr); gap: 3mm }}
 .panel {{ border: .7mm solid #111; display: flex; flex-direction: column; min-height: 0; overflow: hidden }}
 .panel.wide {{ grid-column: span 2 }}
 .art {{ flex: 1; min-height: 12mm; position: relative; background: #eee }}
 .art img {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover }}
 .placeholder {{ position: absolute; inset: 0; padding: 8mm 3mm 3mm; font-size: {base * .8}mm; color: #666 }}
 .caption {{ position: absolute; top: 0; left: 0; max-width: 80%; background: #fff4b8;
            border-right: .5mm solid #111; border-bottom: .5mm solid #111; padding: 1mm 1.6mm;
            font-size: {base}mm; line-height: 1.2 }}
 .talk {{ display: flex; flex-direction: column; gap: 1mm; padding: 1.4mm; border-top: .5mm solid #111 }}
 .bubble {{ background: #fff; border: .4mm solid #111; border-radius: 3mm; padding: .8mm 2mm;
           font-size: {base}mm; line-height: 1.2 }}
 .bubble b {{ font-size: {base * .8}mm; text-transform: uppercase; margin-right: 1mm }}
 footer {{ display: flex; flex-direction: column; gap: 1mm }}
 .takeaway {{ background: #111; color: #fff; padding: 2mm 3mm; font-size: {base * 1.15}mm; font-weight: 700 }}
 footer small {{ font-size: {base * .7}mm; color: #555 }}
 @media print {{ body {{ background: none }} .sheet {{ margin: 0 }} }}
</style></head><body>
{"".join(f"<div class='sheet'>{s}</div>" for s in sheets)}
</body></html>"""


def script_md(comic: Comic, audience: str) -> str:
    """A plain-text version of the comic, handy for checking accuracy and comparing audiences."""
    lines = [f"# {comic.title}", f"*{comic.tagline}*", "", f"Audience: **{audience}**", "",
             f"**Key message:** {comic.key_message}", "", "## Cast"]
    lines += [f"- **{c.name}** ({c.role}): {c.look}" for c in comic.cast]
    for s, sec in enumerate(comic.sections, 1):
        lines += ["", f"## {s}. {sec.heading}"]
        for i, p in enumerate(sec.panels, 1):
            lines += ["", f"**Panel {i}**" + (" (wide)" if p.wide else ""), f"> Scene: {p.scene}"]
            if p.narration:
                lines.append(f"- Caption: {p.narration}")
            lines += [f"- {l.speaker}: {l.text}" for l in p.dialogue]
    lines += ["", f"**Takeaway:** {comic.takeaway}", "", "## Facts used (check these against the paper!)"]
    lines += [f"- {f.claim} *({f.source})*" for f in comic.facts]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------

def make_comic(pdf: str, audience: str, quality: str, text_only: bool, reuse_script: bool) -> None:
    aud = AUDIENCES[audience]
    out = output_dir(pdf, f"comic-{audience}")
    script_path = out / "comic.json"

    if reuse_script and script_path.exists():
        print(f"📄 [{audience}] Reusing {script_path}")
        comic = Comic.model_validate_json(script_path.read_text(encoding="utf-8"))
    else:
        print(f"📄 [{audience}] Reading the paper and writing the comic script...")
        pmin, pmax = aud["panels"]
        prompt = PROMPT.format(persona=aud["persona"], format=aud["format"], writing=aud["writing"],
                               cast=aud["cast"], sections=aud["sections"], unit=aud["unit"],
                               pmin=pmin, pmax=pmax)
        comic = ask_pdf(pdf, prompt, schema=Comic)
        script_path.write_text(comic.model_dump_json(indent=2), encoding="utf-8")
    (out / "script.md").write_text(script_md(comic, audience), encoding="utf-8")

    if not text_only:
        print(f"🎨 [{audience}] Drawing the character sheet...")
        sheet = draw_cast_sheet(comic, aud["style"], out / "characters.png", quality)
        jobs = [(p, out / f"panel_{s + 1}_{i + 1}.png")
                for s, sec in enumerate(comic.sections) for i, p in enumerate(sec.panels)]
        print(f"🎨 [{audience}] Drawing {len(jobs)} panels (a few at a time)...")
        with ThreadPoolExecutor(max_workers=4) as pool:
            for path in pool.map(lambda j: draw_panel(comic, j[0], aud["style"], sheet, j[1], quality), jobs):
                print(f"   {path.name}")

    page = out / "comic.html"
    page.write_text(render_html(comic, aud["unit"], out), encoding="utf-8")
    pdf_out = html_to_pdf(page, out / "comic.pdf")
    print(f"✅ [{audience}] {pdf_out or page}  (text version: {out / 'script.md'})\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf")
    parser.add_argument("--audience", choices=[*AUDIENCES, "both"], default="both")
    parser.add_argument("--quality", choices=["low", "medium", "high"], default="medium",
                        help="image quality; 'low' is much cheaper for drafts")
    parser.add_argument("--text-only", action="store_true",
                        help="write the script and a layout with placeholders, but draw no images")
    parser.add_argument("--reuse-script", action="store_true",
                        help="reuse an existing comic.json instead of asking the model again")
    args = parser.parse_args()

    audiences = list(AUDIENCES) if args.audience == "both" else [args.audience]
    for audience in audiences:
        make_comic(args.pdf, audience, args.quality, args.text_only, args.reuse_script)


if __name__ == "__main__":
    main()
