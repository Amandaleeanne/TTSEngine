from dataclasses import dataclass
from pathlib import Path
from typing import Union

'''
This module defines the type safe command models that a UI or user can call
the dataclasses are headless and are used to pass data between the UI and the backend
to tell the event handler what got updated in the UI.
'''

class EngineCommand:
    """Base class for all commands that can be sent to the engine."""
    pass


# -------- No Data --------
@dataclass(frozen=True)
class Play(EngineCommand):
    pass

@dataclass(frozen=True)
class Pause(EngineCommand):
    pass

@dataclass(frozen=True)
class Stop(EngineCommand):
    pass

#TODO: Add skip forwards / skip backwards

# -------- With Data --------

@dataclass(frozen=True)
class OpenBook(EngineCommand):
    file_path: str

    def __post_init__(self) -> None:
        if not self.file_path.strip():
            raise ValueError("file_path cannot be empty or whitespace.")
        
        path = Path(self.file_path)
        if not path.exists():
            raise FileNotFoundError(f"Book file does not exist at: {self.file_path}")

@dataclass(frozen=True)
class SeekSentence(EngineCommand):
    sentence_index: int

    def __post_init__(self) -> None:
        if self.sentence_index < 0:
            raise ValueError(f"sentence_index must be non-negative, got {self.sentence_index}")

@dataclass(frozen=True)
class SeekChapter(EngineCommand):
    chapter_index: int

    def __post_init__(self) -> None:
        if self.chapter_index < 0:
            raise ValueError(f"chapter_index must be non-negative, got {self.chapter_index}")

@dataclass(frozen=True)
class SeekWord(EngineCommand):
    word_index: int

    def __post_init__(self) -> None:
        if self.word_index < 0:
            raise ValueError(f"word_index must be non-negative, got {self.word_index}")

@dataclass(frozen=True)
class SetSpeed(EngineCommand):
    speed: float

    def __post_init__(self) -> None:
        if not (0.25 <= self.speed <= 4.0):
            raise ValueError(f"Speed rate must be between 0.25 and 4.0, got {self.speed}")

@dataclass(frozen=True)
class SetVoice(EngineCommand):
    voice: str

    def __post_init__(self) -> None:
        if not self.voice.strip():
            raise ValueError("voice cannot be empty or whitespace.")


@dataclass(frozen=True)
class SkipForward(EngineCommand):
    """Request to skip forward by a number of sentences."""
    sentences: int

    def __post_init__(self) -> None:
        if self.sentences <= 0:
            raise ValueError(f"sentences must be a positive integer, got {self.sentences}")


@dataclass(frozen=True)
class SkipBackward(EngineCommand):
    """Request to skip backward by a number of sentences."""
    sentences: int

    def __post_init__(self) -> None:
        if self.sentences <= 0:
            raise ValueError(f"sentences must be a positive integer, got {self.sentences}")

# A type alias representing ANY valid command, for IDEs and TypeCheckers
Command = (
    Play
    | Pause
    | Stop
    | OpenBook
    | SeekSentence
    | SeekChapter
    | SeekWord
    | SetSpeed
    | SetVoice
    | SkipForward
    | SkipBackward
)