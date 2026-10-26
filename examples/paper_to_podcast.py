"""
Example 2 — PDF -> two-host podcast episode.

    python examples/paper_to_podcast.py papers/my-paper.pdf
    python examples/paper_to_podcast.py papers/my-paper.pdf --minutes 5 --vibe "late-night radio show"
    python examples/paper_to_podcast.py papers/my-paper.pdf --language German

Pipeline:  PDF --(Responses API, structured output)--> script (list of lines per host)
               --(Text-to-speech, one call per line, two voices)--> joined into one WAV
Output:    output/<paper>/podcast/episode.wav (+ episode.mp3 if ffmpeg is installed), script.md
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel, Field

from paperkit import ask_pdf, ffmpeg, has_ffmpeg, output_dir, pcm_seconds, save_wav, silence, speak

# Who is on the show. Change names, voices and personalities freely.
HOSTS = {
    "HOST": {"name": "Maya", "voice": "marin",
             "style": "Curious, warm podcast host. Asks the questions the audience is thinking. "
                      "Reacts with genuine surprise and humour."},
    "GUEST": {"name": "Theo", "voice": "cedar",
              "style": "Enthusiastic expert who has read the paper closely. Explains with analogies, "
                       "speaks clearly, a little nerdy."},
}


class Line(BaseModel):
    speaker: Literal["HOST", "GUEST"]
    text: str = Field(description="What they say. Spoken language, max ~3 sentences.")


class Episode(BaseModel):
    title: str
    lines: list[Line]


PROMPT = """Write the script for a podcast episode about the attached paper.

Show format: {vibe}.
Two speakers:
- HOST = {host_name}: {host_style}
- GUEST = {guest_name}: {guest_style}

Rules:
- About {words} words in total (~{minutes} minutes spoken).
- Open with a hook, explain the problem, the key idea, the evidence, the limitations, and end
  with "why should I care" plus a short sign-off.
- Natural conversation: short turns, interruptions, "wait, so...", follow-up questions.
- Stay faithful to the paper. No invented numbers. Say explicitly when something is a limitation.
- Write for the ear: no bullet points, no URLs, no LaTeX; spell out symbols and abbreviations on first use.
- Language: {language}."""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf")
    parser.add_argument("--minutes", type=float, default=3, help="target length (default 3)")
    parser.add_argument("--vibe", default="friendly science podcast")
    parser.add_argument("--language", default="English")
    parser.add_argument("--pause", type=float, default=0.35, help="seconds of silence between turns")
    args = parser.parse_args()

    out = output_dir(args.pdf, "podcast")
    host, guest = HOSTS["HOST"], HOSTS["GUEST"]

    print("📄 Reading the paper and writing the script...")
    episode: Episode = ask_pdf(args.pdf, PROMPT.format(
        vibe=args.vibe, minutes=args.minutes, words=int(args.minutes * 150), language=args.language,
        host_name=host["name"], host_style=host["style"],
        guest_name=guest["name"], guest_style=guest["style"],
    ), schema=Episode)

    script = f"# {episode.title}\n\n" + "\n\n".join(
        f"**{HOSTS[l.speaker]['name']}:** {l.text}" for l in episode.lines)
    (out / "script.md").write_text(script + "\n", encoding="utf-8")
    print(f"📝 Script: {len(episode.lines)} lines -> {out / 'script.md'}")

    # One TTS call per line, a few in parallel. Order is preserved by map().
    print("🎙️  Recording voices...")

    def record(line: Line) -> bytes:
        who = HOSTS[line.speaker]
        return speak(line.text, voice=who["voice"], instructions=who["style"])

    with ThreadPoolExecutor(max_workers=4) as pool:
        clips = list(pool.map(record, episode.lines))

    gap = silence(args.pause)
    audio = silence(0.5) + gap.join(clips) + silence(1.0)
    wav = save_wav(audio, out / "episode.wav")
    print(f"\n✅ Done: {wav}  ({pcm_seconds(audio) / 60:.1f} min)")

    if has_ffmpeg():
        ffmpeg("-i", str(wav), "-codec:a", "libmp3lame", "-b:a", "128k", str(out / "episode.mp3"))
        print(f"   MP3:  {out / 'episode.mp3'}")


if __name__ == "__main__":
    main()
