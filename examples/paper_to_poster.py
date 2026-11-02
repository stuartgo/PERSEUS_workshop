"""
Example 1 — PDF -> scientific (conference) poster.

    python examples/paper_to_poster.py papers/my-paper.pdf
    python examples/paper_to_poster.py papers/my-paper.pdf --orientation landscape
    python examples/paper_to_poster.py papers/my-paper.pdf --mode image --quality low

Two modes:
  layout  (default)  The image model only draws the overview figure; the text (title, authors,
                     Introduction / Methods / Results / Conclusions / References) is laid out
                     in an HTML page with exact text. Also exported to poster.pdf (A0) via headless Chrome.
  image              The image model draws the WHOLE poster, text included. Quick to preview,
                     but a scientific poster has a lot of text and small text can come out wrong.

Pipeline:  PDF --(Responses API, structured output)--> poster content
               --(Images API)--> figure.png + poster.html   or   poster.png
Output:    output/<paper>/poster/
"""

import argparse
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `import paperkit` works

from pydantic import BaseModel, Field

from paperkit import ask_pdf, generate_image, html_to_pdf, output_dir


class KeyNumber(BaseModel):
    value: str = Field(description="A headline number FROM THE PAPER, e.g. '28.4', '3.2x', '-41%'")
    label: str = Field(description="What it measures, max 8 words, e.g. 'BLEU on WMT14 En-De'")


class Poster(BaseModel):
    title: str = Field(description="The paper's title (shorten only if longer than ~15 words)")
    authors: str = Field(description="Author names as listed in the paper, comma-separated")
    affiliations: str = Field(description="Institutions, semicolon-separated, or '' if not given")
    takeaway: str = Field(description="The one-sentence take-home message of the paper, max 25 words")
    introduction: list[str] = Field(description="2-4 bullets: background, the gap/problem, why it matters")
    objectives: list[str] = Field(description="1-3 bullets: the research question(s) / aims")
    methods: list[str] = Field(description="3-5 bullets: data, approach, experimental setup")
    results: list[str] = Field(description="3-5 bullets: main quantitative findings, with numbers")
    key_numbers: list[KeyNumber] = Field(description="1-3 of the most important results")
    conclusions: list[str] = Field(description="2-4 bullets: what the results mean, limitations, future work")
    references: list[str] = Field(description="2-4 key references cited in the paper, short form "
                                              "'Author et al., Year. Title. Venue.'")
    figure_concept: str = Field(description="A schematic overview figure of the method / study design "
                                            "(like a graphical abstract): components, flow, layout, colours. "
                                            "It must work WITHOUT any text labels.")
    figure_caption: str = Field(description="Caption for that figure, starting 'Figure 1.', max 30 words")


PROMPT = """You are an experienced researcher preparing a conference poster for a paper.

Read the attached paper and write the content for a scientific poster in this style: {style}.
- Audience: {audience}.
- Follow the standard academic poster structure: Introduction, Objectives, Methods, Results,
  Conclusions, References.
- Use concise bullet points (max ~25 words each), not paragraphs. Keep the technical terminology
  of the field, but define unusual abbreviations once.
- Be accurate: every claim, number, author and reference must come from the paper. Do not invent
  results; quote numbers with their units and the comparison they refer to.
- The figure should be a clean schematic of the method or study design, as in a graphical abstract,
  not a reproduction of a results chart. No real people, no logos."""


def bullets_text(items: list[str]) -> str:
    return "\n".join(f'    • "{x}"' for x in items)


def image_prompt(p: Poster, style: str, orientation: str) -> str:
    """Everything the image model needs to draw the full poster, with the exact text to render."""
    numbers = "\n".join(f'    "{k.value}" — "{k.label}"' for k in p.key_numbers)
    sections = [("Introduction", p.introduction), ("Objectives", p.objectives), ("Methods", p.methods),
                ("Results", p.results), ("Conclusions", p.conclusions), ("References", p.references)]
    body = "\n".join(f'- Section "{name}":\n{bullets_text(items)}' for name, items in sections)
    return f"""A finished academic conference poster, {orientation} orientation, in a multi-column grid
layout. Style: {style}.

Header band across the top:
- Title (largest text): "{p.title}"
- Authors: "{p.authors}"
- Affiliations (smaller): "{p.affiliations}"

A highlighted take-home message box: "{p.takeaway}"

Section blocks with clear headings and bullet points, render this text exactly and spelled correctly:
{body}

In the Methods area, a schematic figure: {p.figure_concept}
Caption under it: "{p.figure_caption}"

In the Results area, large highlighted key numbers:
{numbers}

White or very light background, high contrast, consistent fonts, aligned columns, generous spacing,
legible text, no other text or logos."""


def render_html(p: Poster, style: str, orientation: str) -> str:
    """Layout mode: exact text in an A0 HTML poster around the generated figure. Print to PDF."""
    e = html.escape
    w, h = (841, 1189) if orientation == "portrait" else (1189, 841)
    cols = 3 if orientation == "portrait" else 4

    def section(name: str, items: list[str], extra: str = "") -> str:
        lis = "".join(f"<li>{e(x)}</li>" for x in items)
        return f"<section><h2>{e(name)}</h2><ul>{lis}</ul>{extra}</section>"

    figure = (f"<figure><img src='figure.png' alt=''><figcaption>{e(p.figure_caption)}</figcaption></figure>")
    numbers = "".join(f"<div class='num'><b>{e(k.value)}</b><span>{e(k.label)}</span></div>"
                      for k in p.key_numbers)
    refs = "".join(f"<li>{e(r)}</li>" for r in p.references)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(p.title)}</title>
<!-- style requested: {e(style)} -->
<style>
 @page {{ size: {w}mm {h}mm; margin: 0 }}
 :root {{ --ink:#1b1f24; --muted:#5b6470; --paper:#ffffff; --brand:#16324f; --accent:#d9822b; --tint:#eef3f8 }}
 * {{ box-sizing:border-box }}
 body {{ margin:0; background:#ccc; font-family:"Source Sans 3","Helvetica Neue",Arial,sans-serif; color:var(--ink) }}
 /* All sizes are in cqw (% of poster width), so screen preview and A0 print look the same. */
 .poster {{ container-type:inline-size; width:min(100vw, {w}mm); aspect-ratio:{w}/{h}; margin:0 auto;
           background:var(--paper); display:flex; flex-direction:column; overflow:hidden }}
 .inner {{ flex:1; min-height:0; display:flex; flex-direction:column; gap:1.4cqw; padding:2cqw }}
 header {{ background:var(--brand); color:#fff; padding:2.2cqw 2.5cqw; text-align:center }}
 h1 {{ font-size:3.6cqw; line-height:1.1; margin:0 0 .5em }}
 .authors {{ font-size:1.6cqw; margin:0 }}
 .affil {{ font-size:1.2cqw; margin:.3em 0 0; opacity:.8 }}
 .takeaway {{ background:var(--tint); border-left:.6cqw solid var(--accent); padding:1.2cqw 1.6cqw;
             font-size:1.75cqw; font-weight:600; line-height:1.3 }}
 .grid {{ flex:1; min-height:0; column-count:{cols}; column-gap:2cqw; column-fill:auto }}
 section {{ break-inside:avoid; margin:0 0 1.6cqw }}
 h2 {{ font-size:1.9cqw; color:var(--brand); margin:0 0 .5em; padding-bottom:.25em; border-bottom:.25cqw solid var(--accent) }}
 ul {{ margin:0; padding-left:1.2em }}
 li {{ font-size:1.25cqw; line-height:1.4; margin:0 0 .45em }}
 figure {{ margin:1cqw 0 0 }}
 figure img {{ width:100%; display:block; border:1px solid #dde3ea; border-radius:.4cqw }}
 figcaption {{ font-size:1cqw; color:var(--muted); margin-top:.5em; line-height:1.35 }}
 .nums {{ display:flex; gap:1cqw; margin:0 0 1cqw }}
 .num {{ flex:1; background:var(--tint); border-radius:.4cqw; padding:1cqw; text-align:center }}
 .num b {{ display:block; font-size:3cqw; color:var(--accent); line-height:1 }}
 .num span {{ display:block; font-size:1cqw; margin-top:.4em; color:var(--muted) }}
 .refs li {{ font-size:.95cqw; color:var(--muted) }}
 @media print {{ body {{ background:none }} .poster {{ width:{w}mm; height:{h}mm }} }}
</style></head><body><div class="poster">
 <header><h1>{e(p.title)}</h1><p class="authors">{e(p.authors)}</p>
  {f"<p class='affil'>{e(p.affiliations)}</p>" if p.affiliations else ""}</header>
 <div class="inner">
  <div class="takeaway">{e(p.takeaway)}</div>
  <div class="grid">
   {section("Introduction", p.introduction)}
   {section("Objectives", p.objectives)}
   {section("Methods", p.methods, figure)}
   <section><h2>Results</h2><div class="nums">{numbers}</div><ul>{"".join(f"<li>{e(x)}</li>" for x in p.results)}</ul></section>
   {section("Conclusions", p.conclusions)}
   <section class="refs"><h2>References</h2><ul>{refs}</ul></section>
  </div>
 </div>
</div></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf")
    parser.add_argument("--mode", choices=["layout", "image"], default="layout")
    parser.add_argument("--orientation", choices=["portrait", "landscape"], default="portrait",
                        help="A0 portrait (3 columns) or landscape (4 columns)")
    parser.add_argument("--style", default="clean, modern academic conference poster, white background, "
                                            "navy and orange accents, flat vector schematics")
    parser.add_argument("--audience", default="researchers at a conference poster session, from the same "
                                              "broad field but not specialists in this topic")
    parser.add_argument("--quality", choices=["low", "medium", "high"], default="high",
                        help="image quality; 'low' is much cheaper for drafts")
    args = parser.parse_args()

    out = output_dir(args.pdf, "poster")
    size = "1024x1536" if args.orientation == "portrait" else "1536x1024"

    print("📄 Reading the paper and writing the poster content...")
    poster: Poster = ask_pdf(args.pdf, PROMPT.format(style=args.style, audience=args.audience), schema=Poster)
    (out / "poster.json").write_text(poster.model_dump_json(indent=2), encoding="utf-8")

    if args.mode == "image":
        print("🎨 Drawing the poster (this can take a minute)...")
        prompt = image_prompt(poster, args.style, args.orientation)
        (out / "image_prompt.txt").write_text(prompt, encoding="utf-8")
        result = generate_image(prompt, out / "poster.png", size=size, quality=args.quality)
    else:
        print("🎨 Drawing the overview figure...")
        # The figure sits inside one column, so a landscape image fits best in either orientation.
        generate_image(f"A clean scientific schematic figure for a research poster: {poster.figure_concept}\n"
                       f"Style: {args.style}. Plain white background. No text, no letters, no numbers, no logos.",
                       out / "figure.png", size="1536x1024", quality=args.quality)
        result = out / "poster.html"
        result.write_text(render_html(poster, args.style, args.orientation), encoding="utf-8")
        if html_to_pdf(result, out / "poster.pdf"):
            print("   Also saved poster.pdf (A0, ready to print).")

    print(f"\n✅ Done: {result}\n")
    print(poster.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
