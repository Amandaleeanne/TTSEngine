# TTSEngine — Example Use Cases

TTSEngine's job is narrow on purpose: it tracks *where you are* in a document and *what the playback settings are*, and it tells subscribers when that changes. It doesn't synthesize speech or play audio. Every example below shows a different way that narrow job turns into something useful once a real frontend, TTS provider, or audio backend is plugged in.

All examples were tested against the current source. Run them with `src/` on `PYTHONPATH`:

```bash
PYTHONPATH="src" python3 your_script.py
```

## 1. Audiobook-style seeking (skip forward/back, jump chapters)

A common audiobook UI need: "skip forward 3 sentences" or "jump to Chapter 1" buttons, without the UI knowing anything about how chapters/sentences/words relate to each other.

```python
from modeling.models import Document, Chapter, Paragraph, Sentence, Word
from modeling.state import State
from actions.controller import Controller

document = build_demo_document()  # returns a Document, see models.py
controller = Controller(initial_state=State(document=document))

def skip_forward(controller, n_sentences=5):
    target = controller.state.current_sentence_index + n_sentences
    controller.seek_sentence(target)

controller.play()
skip_forward(controller, n_sentences=3)
print(controller.state.current_chapter.title, controller.state.current_sentence.text)

controller.seek_chapter(0)  # jump back to Chapter 1
controller.pause()
```

`seek_to_sentence` clamps out-of-range targets to the nearest valid sentence and automatically resolves the correct chapter/paragraph, so "skip forward" never has to worry about crossing a chapter boundary.

## 2. Building a `Document` from plain text

Document providers (TXT/EPUB/PDF loaders) aren't built into the engine yet, so any consumer that wants to load real content needs to construct a `Document` itself. Here's a minimal loader that splits raw text into paragraphs and sentences and assigns the global indices the engine expects:

```python
import re
from modeling.models import Document, Chapter, Paragraph, Sentence, Word

def text_to_document(title: str, raw_text: str) -> Document:
    global_sentence_idx = 0
    global_word_idx = 0
    paragraphs = []

    for para_text in [p.strip() for p in raw_text.split("\n\n") if p.strip()]:
        sentences = []
        for sent_text in re.split(r"(?<=[.!?]) +", para_text):
            sent_text = sent_text.strip()
            if not sent_text:
                continue
            words = []
            for tok in sent_text.split():
                words.append(Word(text=tok, start_time=0.0, end_time=0.0, word_index=global_word_idx))
                global_word_idx += 1
            sentences.append(Sentence(text=sent_text, words=tuple(words), sentence_index=global_sentence_idx))
            global_sentence_idx += 1
        paragraphs.append(Paragraph(sentences=tuple(sentences), paragraph_index=len(paragraphs)))

    chapter = Chapter(title=title, paragraphs=tuple(paragraphs), chapter_index=0)
    return Document(title=title, chapters=(chapter,))

text = """The sun rose slowly. Birds began to sing.

A new day had begun."""

doc = text_to_document("My Sample Chapter", text)
print(doc.total_sentences)  # 3
```

`start_time`/`end_time` are left at `0.0` here since real timing only exists once a TTS provider has synthesized the audio (see example 3) — the engine itself doesn't generate timing data.

## 3. Wiring engine events to a real TTS provider

This is the engine's core purpose, spelled out: "a python engine that signals events for other TTS applications to pick up and use." The engine tells you *what sentence is now current*; a separate TTS provider (Edge TTS, Piper, pyttsx3, ElevenLabs, etc.) turns that into audio.

```python
from communication.events import SentenceChanged
from actions.controller import Controller
from modeling.state import State

controller = Controller(initial_state=State(document=document))

def on_event(event):
    if isinstance(event, SentenceChanged):
        sentence = controller.state.current_sentence
        if sentence:
            # Hand off to whatever TTS backend you're using, e.g.:
            #   audio, word_timings = my_tts_provider.synthesize(sentence.text)
            #   audio_player.play(audio)
            print(f"[TTS] synthesizing: {sentence.text!r}")

controller.subscribe(on_event)
controller.play()
controller.seek_sentence(2)
```

Because the engine only emits an event and never calls a TTS library directly, you can swap providers (or run several — e.g. one for audio, one for live captions) without touching engine code.

> The controller only emits `SentenceChanged` when the sentence index actually changes — seeking to `0` on a document that's already at sentence `0` won't fire anything, which is why this example seeks to sentence `2`.

## 4. Word-by-word highlighting for a reading UI

Screen readers and read-along UIs need to highlight the exact word being spoken. Once a TTS provider reports word timing, the engine's `SeekWord` command / `WordHighlighted` event can drive that highlight independent of the UI framework:

```python
from communication.events import WordHighlighted
from actions.controller import Controller
from modeling.state import State

controller = Controller(initial_state=State(document=document))

def highlight_word(event):
    if isinstance(event, WordHighlighted):
        word = controller.state.current_word
        if word:
            print(f"Highlighting: '{word.text}' (index {word.word_index})")

controller.subscribe(highlight_word)

# Simulating word-boundary callbacks coming from a TTS engine mid-sentence:
for word_index in range(0, 4):
    controller.seek_word(word_index)
```

A terminal UI would print styled text here; a web frontend would update a DOM highlight class; a screen reader integration would move its cursor — the engine doesn't care which.

## 5. Saving and restoring a reading position (bookmarks)

`State` carries everything needed to resume exactly where a reader left off. Since `State` and its fields are plain, serializable values, persistence is just reading them out and back in — no engine-specific save format required:

```python
import json
from communication.commands import SeekSentence, SetSpeed, SetVoice
from actions.controller import Controller
from modeling.state import State

controller = Controller(initial_state=State(document=document))
controller.handle_command(SeekSentence(sentence_index=1))
controller.handle_command(SetSpeed(speed=1.5))
controller.handle_command(SetVoice(voice="en-GB-SoniaNeural"))

bookmark = {
    "sentence_index": controller.state.current_sentence_index,
    "speed": controller.state.speed,
    "voice": controller.state.voice,
}
with open("bookmark.json", "w") as f:
    json.dump(bookmark, f)

# --- later, in a new session ---
with open("bookmark.json") as f:
    restored = json.load(f)

new_controller = Controller(initial_state=State(document=document))
new_controller.handle_command(SeekSentence(sentence_index=restored["sentence_index"]))
new_controller.handle_command(SetSpeed(speed=restored["speed"]))
new_controller.handle_command(SetVoice(voice=restored["voice"]))

print(new_controller.state.current_sentence.text, new_controller.state.speed)
# -> "Sentence 1" 1.5
```

## 6. Multiple frontends sharing one engine instance

Because the `Controller` just fans events out to every subscriber, several consumers can watch the same reading session simultaneously — e.g. a desktop window and a companion screen-reader integration:

```python
from communication.commands import Play, SeekSentence
from actions.controller import Controller
from modeling.state import State

controller = Controller(initial_state=State(document=document))

def desktop_ui(event):
    print("[UI]", event)

def accessibility_bridge(event):
    print("[a11y]", event)

controller.subscribe(desktop_ui)
controller.subscribe(accessibility_bridge)

controller.handle_command(Play())
controller.handle_command(SeekSentence(sentence_index=2))
```

Both subscribers receive every event, and neither knows the other exists — this is the "UI independence" goal from `docs/design.md` in practice.

---

For the `build_demo_document()` helper used above, see `tests/test_actions.py`'s `multi_chapter_doc` fixture, which builds a 3-chapter, 2-sentences-per-chapter document — or construct one the same way as the Quick Start example in `README.md`.