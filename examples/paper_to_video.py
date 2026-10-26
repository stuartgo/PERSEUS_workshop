"""
Example 3 — PDF -> short narrated explainer video.

    python examples/paper_to_video.py papers/my-paper.pdf                    # Sora clips (slow, pricier)
    python examples/paper_to_video.py papers/my-paper.pdf --mode slides      # still images + zoom (fast, cheap)
    python examples/paper_to_video.py papers/my-paper.pdf --shots 4 --vertical --style "claymation"

Pipeline:
    PDF --(Responses API, structured output)--> storyboard: N shots, each = visual prompt + narration
        --(Videos API / Sora)  or  (Images API, --mode slides)--> one visual per shot
        --(Text-to-speech)--> one narration clip per shot
        --(ffmpeg)--> shots stitched into one MP4
Output:    output/<paper>/video/video.mp4  (+ storyboard.md and all intermediate files)

Needs ffmpeg. Sora renders take a few minutes each; all shots render in parallel.
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel, Field

from paperkit import (ask_pdf, ffmpeg, generate_image, has_ffmpeg, output_dir, pcm_seconds,
                      save_wav, speak, start_video, wait_for_video)

NARRATOR = "Energetic, clear documentary narrator. Builds curiosity, lands the punchline of each sentence."


class Shot(BaseModel):
    visual_prompt: str = Field(description="Detailed visual description of this shot: subject, setting, "
                                           "camera movement, lighting, one clear action.")
    narration: str = Field(description="Voice-over spoken during this shot.")


class Storyboard(BaseModel):
    title: str
    visual_style: str = Field(description="One sentence describing the shared look of all shots")
    shots: list[Shot]


PROMPT = """Turn the attached paper into a {shots}-shot explainer video storyboard.

- Shot 1 hooks the viewer with the problem; the middle shots show the key idea and the evidence;
  the last shot says why it matters.
- Visual style for every shot: {style}. Keep characters, colours and setting consistent across shots
  so it feels like one film. Visual metaphors beat literal diagrams.
- Visuals must contain NO on-screen text, NO logos, NO real or famous people, NO copyrighted characters.
- Narration per shot: at most {words} words (it must fit in about {seconds} seconds), spoken English,
  no symbols or citations. Stay faithful to the paper; do not invent numbers."""


def fit_narration(text: str, max_seconds: float | None) -> bytes:
    """Speak the narration; if it runs longer than the shot, re-speak it a little faster."""
    pcm = speak(text, voice=ARGS.voice, instructions=NARRATOR)
    if max_seconds and pcm_seconds(pcm) > max_seconds:
        speed = min(1.35, pcm_seconds(pcm) / max_seconds * 1.03)
        pcm = speak(text, voice=ARGS.voice, instructions=NARRATOR, speed=speed)
    return pcm


def still_shot(i: int, shot: Shot, style: str, narration: Path, duration: float, out: Path) -> Path:
    """Fallback / cheap mode: a generated still with a slow Ken Burns zoom."""
    w, h = (720, 1280) if ARGS.vertical else (1280, 720)
    img_size = "1024x1536" if ARGS.vertical else "1536x1024"
    image = generate_image(f"{shot.visual_prompt}\nStyle: {style}", out / f"still_{i:02d}.png", size=img_size)
    frames = int(duration * 30) + 1
    # crop to the target aspect ratio, upscale for a smooth zoom, then zoom slowly towards the centre
    vf = (f"[0:v]scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
          f"zoompan=z='min(zoom+0.0007,1.12)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":s={w}x{h}:fps=30,format=yuv420p[v];[1:a]apad[a]")
    shot_path = out / f"shot_{i:02d}.mp4"
    ffmpeg("-loop", "1", "-framerate", "30", "-i", str(image), "-i", str(narration),
           "-filter_complex", vf, "-map", "[v]", "-map", "[a]", "-t", f"{duration:.2f}",
           *ENCODE, str(shot_path))
    return shot_path


def sora_shot(i: int, clip: Path, narration: Path, seconds: float, out: Path) -> Path:
    """Lay the narration over a Sora clip (optionally keeping Sora's own audio quietly underneath)."""
    if ARGS.keep_sora_audio:
        audio = "[0:a]volume=0.25[bg];[1:a]apad[vo];[bg][vo]amix=inputs=2:duration=first:normalize=0[a]"
    else:
        audio = "[1:a]apad[a]"
    shot_path = out / f"shot_{i:02d}.mp4"
    ffmpeg("-i", str(clip), "-i", str(narration), "-filter_complex", audio,
           "-map", "0:v", "-map", "[a]", "-t", f"{seconds}", *ENCODE, str(shot_path))
    return shot_path


# Same codec settings for every shot so they can be concatenated without re-encoding.
ENCODE = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
          "-c:a", "aac", "-ar", "48000", "-ac", "2"]


def main() -> None:
    global ARGS
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pdf")
    parser.add_argument("--mode", choices=["sora", "slides"], default="sora")
    parser.add_argument("--shots", type=int, default=3)
    parser.add_argument("--seconds", choices=["4", "8", "12"], default="8", help="length of each Sora clip")
    parser.add_argument("--style", default="warm, playful 3D animation with soft lighting")
    parser.add_argument("--voice", default="cedar")
    parser.add_argument("--vertical", action="store_true", help="9:16 for reels/shorts")
    parser.add_argument("--keep-sora-audio", action="store_true", help="mix Sora's sound under the narration")
    ARGS = parser.parse_args()

    if not has_ffmpeg():
        sys.exit("This example needs ffmpeg to stitch the video together. See README -> Setup.")

    out = output_dir(ARGS.pdf, "video")
    seconds = int(ARGS.seconds)
    words = int(seconds * 2.3) if ARGS.mode == "sora" else 35

    print("📄 Reading the paper and writing the storyboard...")
    board: Storyboard = ask_pdf(ARGS.pdf, PROMPT.format(
        shots=ARGS.shots, style=ARGS.style, words=words, seconds=seconds if ARGS.mode == "sora" else 15,
    ), schema=Storyboard)
    (out / "storyboard.md").write_text(f"# {board.title}\n\nStyle: {board.visual_style}\n\n" + "\n\n".join(
        f"## Shot {i + 1}\n**Visual:** {s.visual_prompt}\n\n**Narration:** {s.narration}"
        for i, s in enumerate(board.shots)) + "\n", encoding="utf-8")
    print(f"🎬 {len(board.shots)} shots -> {out / 'storyboard.md'}")

    # Start all Sora renders first so they run in parallel while we record narration.
    jobs: dict[int, str] = {}
    if ARGS.mode == "sora":
        size = "720x1280" if ARGS.vertical else "1280x720"
        for i, shot in enumerate(board.shots):
            try:
                jobs[i] = start_video(f"{shot.visual_prompt}\nStyle: {board.visual_style}",
                                      seconds=ARGS.seconds, size=size)
                print(f"  ▶ shot {i + 1}: render started")
            except Exception as err:  # e.g. a prompt rejected by moderation
                print(f"  ⚠ shot {i + 1}: could not start Sora ({err}); will use a still image instead")

    print("🎙️  Recording narration...")
    max_len = seconds - 0.3 if ARGS.mode == "sora" else None
    with ThreadPoolExecutor(max_workers=4) as pool:
        pcms = list(pool.map(lambda s: fit_narration(s.narration, max_len), board.shots))
    narrations = [save_wav(pcm, out / f"narration_{i:02d}.wav") for i, pcm in enumerate(pcms)]

    print("🎞️  Building shots...")
    shot_files = []
    for i, shot in enumerate(board.shots):
        if i in jobs:
            try:
                clip = wait_for_video(jobs[i], out / f"sora_{i:02d}.mp4", label=f"shot {i + 1}")
                shot_files.append(sora_shot(i, clip, narrations[i], seconds, out))
                continue
            except Exception as err:
                print(f"  ⚠ shot {i + 1}: {err} — falling back to a still image")
        duration = seconds if ARGS.mode == "sora" else pcm_seconds(pcms[i]) + 0.6
        shot_files.append(still_shot(i, shot, board.visual_style, narrations[i], duration, out))

    concat_list = out / "shots.txt"
    concat_list.write_text("".join(f"file '{p.name}'\n" for p in shot_files))
    final = out / "video.mp4"
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(final))
    print(f"\n✅ Done: {final}")


if __name__ == "__main__":
    main()
