# TTSEngine

A UI-independent, event-driven "reader engine" for building text-to-speech reading applications in Python.

TTSEngine doesn't play audio or synthesize speech itself. Instead, it owns the **document model, reading position, and playback state**, and **emits typed events** when that state changes (sentence advanced, chapter changed, playback started, etc.). Any frontend — a terminal UI, a desktop app, a screen reader, or an actual TTS provider — subscribes to those events and reacts however it wants. This keeps the engine reusable across many different consumers instead of being tied to one UI or one TTS backend.

> This project was originally created as a sub-project of a larger TTS/accessibility application.

## Status

This is an early-stage / work-in-progress library. The core data model, command layer, event layer, and navigation logic are implemented and unit-tested. **TTS synthesis, audio playback, and document loading (EPUB/PDF/TXT parsing) are not implemented yet** — those are the pieces external consumers are expected to plug in (see [Roadmap](#roadmap--not-yet-implemented) and [Known Issues](#known-issues)).

## Architecture

```
Frontend / TTS Provider / Audio Player
              |
       Commands (Play, Pause, SeekSentence, SetVoice, ...)
              |
              v
          Controller  ---- updates ---->  State (immutable snapshot)
              |
       Events (PlaybackStarted, SentenceChanged, SpeedSet, ...)
              |
              v
Frontend / TTS Provider / Audio Player  (subscribed listeners)
```

- **Commands** are typed, validated requests sent *into* the engine (e.g. `Play()`, `SeekSentence(5)`).
- The **Controller** receives commands, applies navigation rules, and produces a new immutable `State`.
- **Events** are typed notifications sent *out* of the engine to any subscribed callback (e.g. `SentenceChanged(sentence_index=5)`).
- The **Document** model is a fixed hierarchy: `Document → Chapter → Paragraph → Sentence → Word`, with O(1) reverse lookups from a sentence index to its parent chapter/paragraph.

## Installation

```bash
git clone https://github.com/Amandaleeanne/TTSEngine.git
cd TTSEngine
pip install -e .
pip install -r requirements.txt  # installs pytest and any development requirements
```

Because this repository uses a `src/` layout, either install the package editably or run code from the repository root with `PYTHONPATH=src`.

```bash
PYTHONPATH=src python3 your_script.py
PYTHONPATH=src pytest
```

The package has no third-party runtime dependencies — it's pure standard-library Python (3.10+, for `match`/`case` and `dataclasses`).

## Project Structure

```
src/
  modeling/
    models.py       # Document, Chapter, Paragraph, Sentence, Word (frozen dataclasses)
    state.py         # State: current position, playback status, speed/voice settings
  communication/
    commands.py      # Typed commands sent into the engine (Play, SeekSentence, SetVoice, ...)
    events.py         # Typed events emitted by the engine (PlaybackStarted, SentenceChanged, ...)
  actions/
    navigation.py    # Pure functions: State -> State (seek_to_sentence, next_chapter, ...)
    controller.py     # Controller: routes commands, updates State, emits events
docs/
  design.md          # Full design document / intended architecture
examples/
  create_book.py      # Example of constructing a Document (currently out of date, see below)
tests/                 # pytest suite covering models, state, commands, events, navigation, controller
```

## Quick Start

```python
from modeling.models import Document, Chapter, Paragraph, Sentence, Word
from modeling.state import State
from communication.commands import Play, Pause, SeekSentence, SetSpeed
from actions.controller import Controller

# 1. Build a document (see examples/text_to_document.py for a real loader)
w0 = Word(text="Hello", start_time=0.0, end_time=0.5, word_index=0)
w1 = Word(text="world", start_time=0.5, end_time=1.0, word_index=1)
sentence = Sentence(text="Hello world.", words=(w0, w1), sentence_index=0)
paragraph = Paragraph(sentences=(sentence,), paragraph_index=0)
chapter = Chapter(title="Chapter 1", paragraphs=(paragraph,), chapter_index=0)
document = Document(title="My Book", chapters=(chapter,))

# 2. Create the controller with that document loaded into state
controller = Controller(initial_state=State(document=document))

# 3. Subscribe to events (this is what a TTS provider / UI would do)
controller.subscribe(lambda event: print("EVENT:", event))

# 4. Drive the engine with commands
controller.handle_command(Play())
controller.handle_command(SeekSentence(sentence_index=0))
controller.handle_command(SetSpeed(speed=1.25))
controller.handle_command(Pause())

print(controller.state.current_sentence.text)  # "Hello world."
```

> **Note on imports:** run this from the repository root with both the repo root *and* `src/` on `PYTHONPATH` (see [Known Issues](#known-issues) for why, and how to simplify this).

```bash
PYTHONPATH=".:src" python3 your_script.py
```

## Core Concepts

### Document model (`modeling/models.py`)

Frozen dataclasses forming a fixed hierarchy:

| Class | Key fields | Notes |
|---|---|---|
| `Word` | `text`, `start_time`, `end_time`, `word_index` | `word_index` is a global index across the whole document |
| `Sentence` | `text`, `words`, `sentence_index` | `sentence_index` is global; exposes `first_word_index` / `last_word_index` |
| `Paragraph` | `sentences`, `paragraph_index` | `paragraph_index` is local to its chapter |
| `Chapter` | `title`, `paragraphs`, `chapter_index` | `chapter_index` is local to the document |
| `Document` | `title`, `chapters` | Builds an internal `sentence_index -> (chapter_index, paragraph_index)` lookup table on construction, so `get_chapter_index_for_sentence()` / `get_paragraph_index_for_sentence()` are O(1) |

### State (`modeling/state.py`)

`State` is an immutable snapshot of everything the engine currently knows: which document is loaded, where the reader currently is (`current_chapter_index`, `current_sentence_index`, `current_word_index`), and playback settings (`is_playing`, `speed`, `voice`). It exposes computed properties (`current_chapter`, `current_sentence`, `current_word`, `is_loaded`) that resolve the current position against the loaded `Document`, returning `None` safely if the position is out of range.

### Commands (`communication/commands.py`)

Commands are validated at construction time (`__post_init__`) — e.g. `SetSpeed` rejects values outside `0.25`–`4.0`, `SeekSentence`/`SeekChapter`/`SeekWord` reject negative indices, and `OpenBook` checks the file actually exists on disk.

| Command | Purpose |
|---|---|
| `Play()`, `Pause()`, `Stop()` | Playback control |
| `OpenBook(file_path)` | Request to load a document (see [Known Issues](#known-issues) — not yet wired up) |
| `SeekSentence(sentence_index)` | Jump to a specific sentence |
| `SeekChapter(chapter_index)` | Jump to the start of a specific chapter |
| `SeekWord(word_index)` | Jump to / highlight a specific word |
| `SetSpeed(speed)` | Change playback rate (`0.25`–`4.0`) |
| `SetVoice(voice)` | Change the active voice string |

### Events (`communication/events.py`)

Events are what subscribers receive back from the `Controller`.

| Event | Fired when |
|---|---|
| `PlaybackStarted` / `PlaybackPaused` / `PlaybackStopped` | Playback state changes |
| `ChapterChanged(chapter_index)` | The current chapter changes |
| `SentenceChanged(sentence_index)` | The current sentence changes |
| `WordHighlighted(word_index)` | The current word changes |
| `SpeedSet(speed)` / `VoiceSet(voice)` | A setting changes |
| `BookLoaded(file_path, document)` | A document finishes loading (not yet emitted — see below) |
| `ErrorOccurred(message)` | A command raised an exception while being handled |

### Controller (`actions/controller.py`)

The `Controller` is the single entry point: call `controller.subscribe(callback)` to listen for events, and `controller.handle_command(command)` to change state. It never talks to a UI, an audio backend, or a TTS provider directly — it only accepts commands and emits events.

### Navigation helpers (`actions/navigation.py`)

Pure functions of the form `State -> State`, used internally by the `Controller` but usable directly if you want to compute a new state without going through commands/events:

`seek_to_sentence`, `next_sentence`, `previous_sentence`, `seek_to_chapter`, `next_chapter`, `previous_chapter`, `seek_to_word`. All seeking is clamped to valid document bounds and correctly resolves parent chapter/paragraph indices.

## Known Issues

While reviewing the current source for this README, bugs were found that will affect anyone trying to use the engine as-is:


1. **`OpenBook` doesn't actually load anything.** The command validates that the file exists, but `Controller.handle_command`'s `case OpenBook(): pass` is a no-op — no `Document` is built, no `BookLoaded` event is emitted, and `State.document` never gets set from a file path. A document provider (TXT/EPUB/PDF parser) still needs to be built and wired in here.


## Roadmap / Not Yet Implemented

Per `docs/design.md`, the intended full system also includes pieces not yet in this repo:

- **TTS provider interface** — an abstract `synthesize(text) -> audio + word timings` boundary (Edge TTS, Piper, Azure, ElevenLabs, local models, etc.)
- **Audio backend** — play/pause/stop/seek over an actual audio stream (pygame, VLC, system audio, etc.)
- **Document providers** — TXT/EPUB/PDF/Markdown loaders that produce a `Document`
- **Persistence** — saving/restoring library position, bookmarks, and settings
- **Caching strategy** — synthesizing only the current chapter / a sliding window of nearby sentences instead of a whole book at once

## Running Tests

```bash
pip install -e .
pytest
```

If you don't install the package editably, run pytest from the repository root with `PYTHONPATH=src`:

```bash
PYTHONPATH=src pytest
```

## License

GPL-3.0 — see [LICENSE](LICENSE).