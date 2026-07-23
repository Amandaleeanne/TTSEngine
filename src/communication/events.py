from dataclasses import dataclass
from modeling.models import Document

'''
This module defines the backend events emitted by the engine to update the frontend.
'''

class EngineEvent:
    """Base class for all events emitted by the engine."""
    pass


@dataclass(frozen=True)
class ErrorOccurred(EngineEvent):
    message: str


# --- Playback Events ---
@dataclass(frozen=True)
class PlaybackStarted(EngineEvent):
    pass

@dataclass(frozen=True)
class PlaybackPaused(EngineEvent):
    pass

@dataclass(frozen=True)
class PlaybackStopped(EngineEvent):
    pass


# --- Position and Textual Syncing Events ---
@dataclass(frozen=True)
class WordHighlighted(EngineEvent):
    word_index: int

@dataclass(frozen=True)
class SentenceChanged(EngineEvent):
    sentence_index: int

@dataclass(frozen=True)
class ChapterChanged(EngineEvent):
    chapter_index: int

@dataclass(frozen=True)
class ParagraphChanged(EngineEvent):
    paragraph_index: int


# --- Book and Setting Events ---
@dataclass(frozen=True)
class BookLoaded(EngineEvent):
    file_path: str
    document: Document

@dataclass(frozen=True)
class SpeedSet(EngineEvent):
    speed: float

@dataclass(frozen=True)
class VoiceSet(EngineEvent):
    voice: str

@dataclass(frozen=True)
class ProgressChanged(EngineEvent):
    """Emitted when playback or reading progress percentage updates."""
    progress_percentage: float  # 0.0 to 100.0


@dataclass(frozen=True)
class PlaybackFinished(EngineEvent):
    """Emitted when the engine reaches the end of the document."""
    total_sentences_read: int


# Master Type Union
Event = (
    ErrorOccurred
    | PlaybackStarted
    | PlaybackPaused
    | PlaybackStopped
    | ProgressChanged
    | WordHighlighted
    | SentenceChanged
    | ParagraphChanged
    | ChapterChanged
    | BookLoaded
    | SpeedSet
    | VoiceSet
    | PlaybackFinished
)