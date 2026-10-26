"""
Example 1 — PDF -> social/blog post with a generated cover image.

    python examples/paper_to_post.py papers/my-paper.pdf
    python examples/paper_to_post.py papers/my-paper.pdf --format "LinkedIn post" --audience "product managers"
    python examples/paper_to_post.py papers/my-paper.pdf --format "Twitter/X thread" --no-image

Pipeline:  PDF --(Responses API, structured output)--> post  --(Images API)--> cover.png
Output:    output/<paper>/post/post.md, post.html, cover.png
"""

import argparse
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # so `import paperkit` works

from pydantic import BaseModel, Field

from paperkit import ask_pdf, generate_image, output_dir


class Post(BaseModel):
    title: str = Field(description="Catchy headline, max ~12 words")
    hook: str = Field(description="One or two sentences that make people stop scrolling")
    body_markdown: str = Field(description="The post itself, in Markdown")
    key_takeaways: list[str] = Field(description="3-5 one-line takeaways")
    hashtags: list[str]
    image_prompt: str = Field(description="Prompt for an eye-catching cover illustration. "
                                          "No text, no logos, no real people.")


PROMPT = """You are a science communicator who turns research papers into posts people actually read.

Read the attached paper and write a {format} for {audience}.
- Lead with why it matters, not with the method.
- Be accurate: do not invent results, numbers or claims that are not in the paper.
- Explain one concrete example or analogy from the paper.
- Mention the paper's title and authors once.
- Tone: {tone}.
- Length: whatever fits the format (a thread = 5-8 short numbered posts separated by blank lines).
Also propose a cover illustration that captures the core idea visually."""


def render_html(post: Post, cover: str | None) -> str:
    """A tiny self-contained page so you can show the post on a projector."""
    import re
    body = html.escape(post.body_markdown)
    body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", body)
    paragraphs = "".join(f"<p>{p.replace(chr(10), '<br>')}</p>" for p in body.split("\n\n") if p.strip())
    takeaways = "".join(f"<li>{html.escape(t)}</li>" for t in post.key_takeaways)
    tags = " ".join(f"#{html.escape(t.lstrip('#'))}" for t in post.hashtags)
    img = f'<img src="{cover}" alt="cover">' if cover else ""
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(post.title)}</title>
<style>
 body{{font:18px/1.6 Georgia,serif;max-width:720px;margin:40px auto;padding:0 16px;color:#222;background:#fbfaf7}}
 img{{width:100%;border-radius:12px}} h1{{font-family:system-ui,sans-serif;line-height:1.2}}
 .hook{{font-size:1.2em;font-style:italic}} .tags{{color:#2a6;font-family:system-ui}}
 aside{{background:#f0eee8;padding:12px 20px;border-radius:12px}}
</style></head><body>
{img}<h1>{html.escape(post.title)}</h1><p class="hook">{html.escape(post.hook)}</p>
{paragraphs}<aside><strong>Takeaways</strong><ul>{takeaways}</ul></aside>
<p class="tags">{tags}</p></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf")
    parser.add_argument("--format", default="blog post", help='e.g. "blog post", "LinkedIn post", "Twitter/X thread"')
    parser.add_argument("--audience", default="curious non-experts")
    parser.add_argument("--tone", default="enthusiastic but precise")
    parser.add_argument("--no-image", action="store_true", help="skip the cover image (faster, cheaper)")
    args = parser.parse_args()

    out = output_dir(args.pdf, "post")

    print("📄 Reading the paper and writing the post...")
    post: Post = ask_pdf(args.pdf, PROMPT.format(format=args.format, audience=args.audience, tone=args.tone),
                         schema=Post)

    cover = None
    if not args.no_image:
        print("🎨 Generating cover image...")
        generate_image(post.image_prompt, out / "cover.png")
        cover = "cover.png"

    md = f"# {post.title}\n\n" + (f"![cover]({cover})\n\n" if cover else "")
    md += f"_{post.hook}_\n\n{post.body_markdown}\n\n**Takeaways**\n"
    md += "".join(f"- {t}\n" for t in post.key_takeaways)
    md += "\n" + " ".join(f"#{t.lstrip('#')}" for t in post.hashtags) + "\n"
    (out / "post.md").write_text(md, encoding="utf-8")
    (out / "post.html").write_text(render_html(post, cover), encoding="utf-8")

    print(f"\n✅ Done: {out / 'post.html'}  (open it in a browser)\n")
    print(md)


if __name__ == "__main__":
    main()
