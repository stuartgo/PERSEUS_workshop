"""
paperkit — the small set of building blocks every example uses.

Read this file first: it is ~150 lines and shows every OpenAI call the
workshop needs. Import it in your own scripts:

    from paperkit import ask_pdf, generate_image, speak, start_video, wait_for_video

Models are read from .env so you can swap them without touching code.
"""

from __future__ import annotations

import base64
import os
import re
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path
from typing import Optional, Type, TypeVar

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-6.1-sol")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
VIDEO_MODEL = os.getenv("OPENAI_VIDEO_MODEL", "sora-2")

ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = ROOT / "output"

# The speech endpoint's "pcm" format: raw 24 kHz, 16-bit, mono samples.
PCM_RATE, PCM_WIDTH, PCM_CHANNELS = 24_000, 2, 1

T = TypeVar("T", bound=BaseModel)
_client: Optional[OpenAI] = None


def client() -> OpenAI:
    """One shared client. Reads OPENAI_API_KEY from the environment / .env."""
    global _client
    if _client is None:
        if not os.getenv("OPENAI_API_KEY"):
            sys.exit("OPENAI_API_KEY is not set. Copy .env.example to .env and paste your key.")
        _client = OpenAI()
    return _client


# --------------------------------------------------------------------------
# 1. Reading the paper  (Responses API + PDF as input_file)
# --------------------------------------------------------------------------

def pdf_part(pdf_path: str | Path) -> dict:
    """Turn a PDF on disk into a content part the model can read (text + page images)."""
    path = Path(pdf_path)
    if not path.exists():
        sys.exit(f"PDF not found: {path}")
    data = base64.b64encode(path.read_bytes()).decode()
    return {
        "type": "input_file",
        "filename": path.name,
        "file_data": f"data:application/pdf;base64,{data}",
    }


def ask_pdf(pdf_path: str | Path, instructions: str, schema: Type[T] | None = None) -> T | str:
    """
    Ask the model something about a PDF.

    - Without `schema`: returns plain text.
    - With a Pydantic `schema`: returns a filled-in instance of it (structured output),
      which is the easiest way to get a script / storyboard / poster you can loop over.
    """
    messages = [{
        "role": "user",
        "content": [pdf_part(pdf_path), {"type": "input_text", "text": instructions}],
    }]
    if schema is None:
        return client().responses.create(model=TEXT_MODEL, input=messages).output_text
    response = client().responses.parse(model=TEXT_MODEL, input=messages, text_format=schema)
    if response.output_parsed is None:
        sys.exit("The model did not return the expected structure (it may have refused). Try again or tweak the prompt.")
    return response.output_parsed


def ask(prompt: str) -> str:
    """Plain text in, plain text out — no PDF."""
    return client().responses.create(model=TEXT_MODEL, input=prompt).output_text


# --------------------------------------------------------------------------
# 2. Images  (Images API)
# --------------------------------------------------------------------------

def generate_image(prompt: str, out_path: str | Path, size: str = "1536x1024",
                   quality: str = "medium") -> Path:
    """Generate one image and save it as PNG. quality: low | medium | high (cost scales with it)."""
    result = client().images.generate(model=IMAGE_MODEL, prompt=prompt, size=size, quality=quality)
    out_path = Path(out_path)
    out_path.write_bytes(base64.b64decode(result.data[0].b64_json))
    return out_path


# --------------------------------------------------------------------------
# 3. Voices  (Text-to-speech API)
# --------------------------------------------------------------------------

def speak(text: str, voice: str = "marin", instructions: str | None = None,
          speed: float = 1.0) -> bytes:
    """
    Text -> raw PCM audio bytes (24 kHz, 16-bit mono).
    `instructions` steers delivery ("warm, amused, a bit conspiratorial").
    Voices: alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, verse, marin, cedar.
    Max 4096 characters per call.
    """
    extra = {"instructions": instructions} if instructions else {}
    response = client().audio.speech.create(
        model=TTS_MODEL, voice=voice, input=text, response_format="pcm", speed=speed, **extra
    )
    return response.content


def pcm_seconds(pcm: bytes) -> float:
    return len(pcm) / (PCM_RATE * PCM_WIDTH * PCM_CHANNELS)


def silence(seconds: float) -> bytes:
    return b"\x00" * (int(PCM_RATE * seconds) * PCM_WIDTH * PCM_CHANNELS)


def save_wav(pcm: bytes, out_path: str | Path) -> Path:
    """Wrap raw PCM in a WAV header. Concatenate PCM chunks first to join clips."""
    out_path = Path(out_path)
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(PCM_CHANNELS)
        w.setsampwidth(PCM_WIDTH)
        w.setframerate(PCM_RATE)
        w.writeframes(pcm)
    return out_path


# --------------------------------------------------------------------------
# 4. Video  (Videos API / Sora) — jobs are asynchronous: start, then wait
# --------------------------------------------------------------------------

def start_video(prompt: str, seconds: str = "8", size: str = "1280x720") -> str:
    """Kick off a Sora render and return its job id. seconds: "4" | "8" | "12"."""
    job = client().videos.create(model=VIDEO_MODEL, prompt=prompt, seconds=seconds, size=size)
    return job.id


def wait_for_video(video_id: str, out_path: str | Path, label: str = "") -> Path:
    """Poll a render until it finishes, then download the MP4. Renders take minutes."""
    while True:
        job = client().videos.retrieve(video_id)
        if job.status == "completed":
            break
        if job.status == "failed":
            reason = getattr(job, "error", None)
            raise RuntimeError(f"Video {label or video_id} failed: {reason}")
        print(f"  {label or video_id}: {job.status} {getattr(job, 'progress', 0) or 0}%", flush=True)
        time.sleep(10)
    out_path = Path(out_path)
    client().videos.download_content(video_id, variant="video").write_to_file(out_path)
    return out_path


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def output_dir(pdf_path: str | Path, kind: str) -> Path:
    """output/<paper-name>/<kind>/ — created if missing."""
    slug = re.sub(r"[^a-z0-9]+", "-", Path(pdf_path).stem.lower()).strip("-") or "paper"
    path = OUTPUT_ROOT / slug / kind
    path.mkdir(parents=True, exist_ok=True)
    return path


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def ffmpeg(*args: str) -> None:
    """Run ffmpeg quietly; show its error output if it fails."""
    if not has_ffmpeg():
        sys.exit("This step needs ffmpeg. Install it (see README) and try again.")
    result = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")


def find_chrome() -> Optional[str]:
    """Path to a Chrome / Chromium / Edge binary, or None."""
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome", "microsoft-edge"):
        if path := shutil.which(name):
            return path
    for path in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                 "/Applications/Chromium.app/Contents/MacOS/Chromium",
                 "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"):
        if os.path.exists(path):
            return path
    return None


def html_to_pdf(html_path: str | Path, pdf_path: str | Path) -> Optional[Path]:
    """Print an HTML file to PDF with headless Chrome, honouring its @page size.
    Returns the PDF path, or None (with a hint) if Chrome is not installed or fails."""
    chrome = find_chrome()
    if not chrome:
        print("   (No Chrome/Chromium found, so no PDF. Open the HTML and Print -> Save as PDF instead.)")
        return None
    html_path, pdf_path = Path(html_path).resolve(), Path(pdf_path).resolve()
    result = subprocess.run([chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                             f"--print-to-pdf={pdf_path}", html_path.as_uri()],
                            capture_output=True, text=True)
    if result.returncode != 0 or not pdf_path.exists():
        print(f"   (PDF export failed: {result.stderr.strip()[-300:]})")
        return None
    return pdf_path
