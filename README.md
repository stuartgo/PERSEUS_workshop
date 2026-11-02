# 📄➡️🎬 Paper Remix

**Take a research paper and present it to a general public or high-school audience, using an LLM to help you build the material.**

---

## The task

You are presenting your work to a **general public / high-school student audience**. "General public" is far too broad to write for, so:

1. **Choose a paper** (your own work).
2. **Define two specific target audiences** within the general public / high-school crowd. The more specific, the better. For example:
   - 14-year-olds in a school science club
   - Final-year students deciding what to study at university
   - Parents at a school open evening
   - Retirees at a public library talk
   - Local journalists
3. **Choose a format** (poster, podcast, video, comic, quiz, something else) and **create two versions** of the same work, one for each audience. Use the same format for both so the differences come from the audience, not the medium.
4. **Compare and discuss** the two versions with the group (see the discussion points below).

Describe each audience to the LLM in as much detail as you can: age, what they already know, why they would care, how much time and attention they have, what tone works for them.

**Tools:** you can use the NTNU chat at <https://chat.hpc.ntnu.no/> to generate the code, or any other LLM of your choice. We also provide **OpenAI API keys** with tokens you can use in the code you generate, so you can create whatever you like (text, images, speech, video).

---

## Prompting tips

The output is only as good as the brief. A good prompt usually includes:

- **A persona for the audience:** age, prior knowledge, interests, why they are there, how long they will pay attention. Invent a typical member of the audience and describe them.
- **The one main message:** what should they remember tomorrow? You can ask the model to help first: "Read this paper and suggest three possible key messages for this audience", then pick one (or rewrite it) and use it in the real prompt.
- **What to keep and what to drop:** which results, terms or caveats must stay, and which details can go.
- **Tone, format and length:** playful or serious, how many minutes or words, any style rules (no jargon, one analogy, a question to open with).
- **Accuracy rules:** "Only use facts from the paper. Flag anything you are unsure about."

Iterate: read the output, say specifically what is wrong ("too childish", "the second point is misleading"), and ask again.

---

## Examples

The scripts in `examples/` are **starting points, not solutions**. They are written for a generic audience. Read them, copy one, and change it so it makes something for *your* audience. The prompt at the top of each script is the part to rewrite first. [`paperkit.py`](paperkit.py) has the shared building blocks (read a PDF, generate images, speech and video); [`examples/starter.py`](examples/starter.py) is a minimal template.

### 🖼️ Poster: `examples/paper_to_poster.py`

A poster with title, take-home message, sections, key numbers and an overview figure. Outputs `poster.html` and `poster.pdf` (A0).

```bash
python examples/paper_to_poster.py papers/my-paper.pdf --audience "14-year-olds in a school science club" --style "bold, colourful, playful"
```

Useful options: `--audience`, `--style`, `--orientation portrait|landscape`, `--quality low` (cheap drafts), `--mode image` (the whole poster as one image).

### 🎙️ Podcast: `examples/paper_to_podcast.py`

A two-voice conversation about the paper, voiced and joined into one episode. Outputs `episode.wav`/`.mp3` and `script.md`.

```bash
python examples/paper_to_podcast.py papers/my-paper.pdf --minutes 5 --vibe "friendly radio show for teenagers"
```

Edit the `HOSTS` dict to change the speakers' names, voices and personalities.

### 🎬 Video: `examples/paper_to_video.py`

A short narrated explainer: a storyboard, one visual per shot, narration, stitched into an MP4. Outputs `video.mp4` and `storyboard.md`.

```bash
python examples/paper_to_video.py papers/my-paper.pdf --mode slides --shots 4 --style "hand-drawn cartoon"
```

`--mode slides` (still images, fast and cheap) is best for iterating. Sora clips take 5–10 minutes.

### Other formats

Anything you can ask an LLM to write, you can build on. Some ideas:

- 🦸 **Comic strip** with consistent characters
- 🌙 **Bedtime story** or picture book
- 🎞️ **Movie trailer** or 📺 **news broadcast**
- 🧠 **Quiz** or flashcards
- 🏛️ **Museum-style audio guide**
- 🎙️ **Debate** between an enthusiast and a sceptic

Copy `examples/starter.py` as a template.

---

## Discussion points

Once you have both versions, look at what the LLM actually produced and discuss:

- **Audience:** What did the LLM change between the two versions (vocabulary, tone, examples, length, what was left out)? Did it match what you had in mind for each group? Did it fall back on stereotypes?
- **Prompting:** How much detail about the audience did you need to give before the output felt right? What did you have to correct by hand?
- **Communication:** What does each audience need to *take away*? Is that the same thing as what you, as the researcher, think is important?
- **Accuracy:** Is each version still true to the paper? Where did simplifying slip into oversimplifying, or into errors? How would you check?
- **Format:** Did the format suit each audience? Would they actually read, listen to or watch it?
- **Authorship:** Whose work is this? Would you put your name on it, and would you tell the audience an LLM helped make it?
- **Trust:** What does it mean for the public to receive science communication written by an LLM? What are the benefits and risks?
