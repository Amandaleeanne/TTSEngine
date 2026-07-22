# Reader Engine Design Document

## Project: Accessible Reader Engine

## Status

Design Draft

## Purpose

The Reader Engine is the core library responsible for transforming documents into synchronized speech experiences.

The engine provides:

- Document loading and normalization
- Reading position management
- Sentence and word synchronization
- Text-to-speech coordination
- Playback control
- Navigation
- State management
- Event generation

The engine must not depend on any user interface.

Possible consumers:

- Terminal UI
- Desktop GUI
- Web interface
- Screen reader integration
- Mobile applications
- External automation tools

---

# Core Design Principles

## 1. UI Independence

The engine must never know:

- Which UI is being used
- How text is displayed
- How buttons are implemented
- How keyboard input works

The engine only exposes:

- Commands
- State
- Events

---

## 2. Provider Independence

The engine must not depend on a specific:

- TTS provider
- Document format
- Audio backend

Examples:

TTS providers:

- Edge TTS
- Piper
- Azure Speech
- ElevenLabs
- Local models

Document providers:

- TXT
- EPUB
- PDF
- Markdown
- HTML

---

## 3. Event Driven Architecture

The engine communicates through events.

Example:

```
TTS Provider
     |
     v
Playback Controller
     |
     v
Event Bus
     |
     v
Frontend
```

The frontend reacts to events.

---

# High-Level Architecture

```
                 Commands

Frontend --------------------+
                            |
                            v

                    Reader Engine

                            |
          +-----------------+----------------+
          |                 |                |
          v                 v                v

   Document Model    Playback Engine    Navigation

                            |
                            v

                       TTS Provider

                            |
                            v

                         Audio
```

---

# Main Components

## ReaderEngine

The main coordinator.

Responsibilities:

- Manage application state
- Route commands
- Coordinate playback
- Manage document lifecycle
- Publish events


Example:

```python
engine.open_document(book)

engine.play()

engine.pause()

engine.seek_sentence(25)
```

---

# Document Model

The engine works with a normalized document structure.

The original format does not matter.

Everything becomes:

```
Document

 └── Chapter

      └── Section

           └── Paragraph

                └── Sentence

                     └── Word
```

---

# Document Object

Example:

```python
Document(
    id="book123",
    title="Example Book",
    chapters=[]
)
```

Properties:

```
id
title
author
chapters
metadata
```

---

# Chapter

Represents a major document division.

Properties:

```
id
title
sections
start_position
end_position
```

---

# Paragraph

Properties:

```
id
text
sentences
```

---

# Sentence

The primary navigation unit.

Properties:

```
id

text

word_start_index

word_end_index

paragraph_id
```

Example:

```python
Sentence(
    id=42,
    text="The quick brown fox jumps.",
    word_start_index=300,
    word_end_index=305
)
```

---

# Word

The smallest synchronized unit.

Properties:

```
id

text

global_index

sentence_id

start_time

end_time
```

Example:

```python
Word(
    id=301,
    text="brown",
    sentence_id=42
)
```

---

# Why Sentence Level Navigation?

The engine intentionally supports:

- Sentence seeking
- Paragraph seeking
- Chapter seeking

It does not require arbitrary word seeking.

Reasons:

- More natural for readers
- Easier TTS synchronization
- Faster seeking
- Less audio regeneration
- Better accessibility experience

---

# Playback Controller

Responsible for:

- Starting playback
- Pausing playback
- Stopping playback
- Seeking
- Speed changes
- Tracking progress


State:

```
STOPPED

PLAYING

PAUSED

BUFFERING

ERROR
```

---

# Playback Commands

Commands are requests sent to the engine.

---

## Open Document

```python
OpenDocument(path)
```

---

## Playback

```python
Play()

Pause()

Stop()
```

---

## Navigation

```python
NextSentence()

PreviousSentence()

SeekSentence(id)

SeekChapter(id)
```

---

## Settings

```python
SetSpeed(rate)

SetVoice(voice)

SetVolume(level)
```

---

# Engine State

The engine maintains a single source of truth.

Example:

```python
ReaderState(
    document_id="book1",
    chapter=2,
    sentence=45,
    word=612,
    status="playing",
    speed=1.25,
    voice="en-US-Aria"
)
```

---

# Events

Events communicate changes.

All events should be strongly typed.

Avoid:

```python
{
 "event":"word_changed"
}
```

Prefer:

```python
@dataclass
class WordChanged:
    word_id:int
    sentence_id:int
    text:str
```

---

# Core Events

## Document Events

```python
DocumentLoaded

DocumentClosed

DocumentError
```

---

## Playback Events

```python
PlaybackStarted

PlaybackPaused

PlaybackStopped

PlaybackFinished
```

---

## Navigation Events

```python
ChapterChanged

SentenceChanged

WordChanged
```

---

## State Events

```python
SpeedChanged

VoiceChanged

ProgressChanged
```

---

# Example Event Flow

A sentence begins:

```
Edge TTS
   |
   v
WordBoundary("The")
   |
   v
Playback Controller
   |
   v
WordChanged(
    sentence=10,
    word=55
)
   |
   v
Frontend updates
```

---

# TTS Provider Interface

The engine communicates through an abstract interface.

Example:

```python
class TTSProvider:

    def synthesize(
        self,
        text
    ):
        pass
```

---

Provider responsibilities:

- Generate audio
- Provide timing metadata
- Report errors


The provider should return:

```
Audio Stream

+

Word Timing Data
```

Example:

```python
SpeechResult(

audio_file="sentence.mp3",

words=[
    WordTiming(
        text="hello",
        start=0.0,
        end=0.3
    )
]

)
```

---

# Audio Backend

Separate from TTS.

Responsibilities:

- Play audio
- Pause
- Resume
- Stop
- Seek

Possible implementations:

- pygame
- VLC
- system audio
- browser audio

Interface:

```python
class AudioPlayer:

    play()

    pause()

    stop()

    seek(position)
```

---

# Document Provider Interface

Documents are loaded through providers.

Example:

```python
class DocumentProvider:

    load(path)->Document
```

---

Possible providers:

```
TXTProvider

EPUBProvider

PDFProvider

MarkdownProvider
```

---

# Caching Strategy

The engine should not synthesize an entire book at once.

Recommended approach:

Cache:

- Current chapter
- Nearby sentences
- Recent playback history


Example:

```
Current sentence

Previous 5 sentences

Next 10 sentences
```

---

# Navigation System

Navigation operates on document structure.

Supported:

```
next word

next sentence

previous sentence

next paragraph

previous paragraph

next chapter

previous chapter
```

---

# Persistence

The engine should support saving:

```
Library location

Current document

Current chapter

Current sentence

Playback speed

Voice preference

Bookmarks
```

Example:

```json
{
 "book":"example.epub",
 "chapter":5,
 "sentence":120,
 "speed":1.2
}
```

---

# Error Handling

All errors become events.

Examples:

```
DocumentLoadFailed

TTSError

AudioError

ProviderUnavailable
```

The UI decides how to display them.

---

# Testing Strategy

The engine must be testable without:

- Audio hardware
- UI
- Network access


Tests:

## Navigation

```
Open document

Seek sentence

Verify position
```


## Playback

```
Play

Receive events

Pause
```


## Providers

```
Load file

Validate document model
```

---

# Future Extensions

Potential additions:

- Offline TTS
- Multiple voices
- Translation mode
- Annotation system
- Dictionary lookup
- Search indexing
- AI summaries
- Reading statistics
- Multi-user profiles
- Plugin ecosystem

---

# Recommended Initial Implementation Order

## Phase 1

Create:

- Document model
- Event system
- Command system
- Reader state


## Phase 2

Implement:

- TXT provider
- Basic navigation


## Phase 3

Implement:

- TTS provider
- Word timing
- Playback controller


## Phase 4

Implement:

- Persistence
- EPUB support
- PDF support


## Phase 5

Create frontends:

- Textual
- Desktop GUI
- Web

---

# Final Goal

The Reader Engine should become a reusable accessibility library.

The UI is replaceable.

The TTS provider is replaceable.

The document format is replaceable.

The engine remains the stable foundation.