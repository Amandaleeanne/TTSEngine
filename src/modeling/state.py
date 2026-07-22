from dataclasses import dataclass, field
from typing import Optional
from .models import *

'''
This module defines the state of the current document loaded within the engine, which includes the current document tree placement, 
playback status, and settings.
'''

@dataclass(frozen=True)
class State:
    document: Optional[Document] = None
    file_path: Optional[str] = None
    
    # Hierarchy indices
    current_chapter_index: int = 0
    current_paragraph_index: int = 0
    current_sentence_index: int = 0
    current_word_index: int = 0
    
    # Playback status & settings
    is_playing: bool = False
    speed: float = 1.0
    voice: str = "en-US-AvaNeural"

    @property
    def is_loaded(self) -> bool:
        """Helper to quickly check if a document is active."""
        return self.document is not None

    @property
    def current_chapter(self) -> Optional[Chapter]:
        """Returns the active Chapter object"""
        if not self.document:
            return None
        if 0 <= self.current_chapter_index < len(self.document.chapters):
            return self.document.chapters[self.current_chapter_index]
        return None

    @property
    def current_paragraph(self) -> Optional[Paragraph]:
        """Returns the active Paragraph object"""
        chapter = self.current_chapter
        if not chapter:
            return None
        if 0 <= self.current_paragraph_index < len(chapter.paragraphs):
            return chapter.paragraphs[self.current_paragraph_index]
        return None

    @property
    def current_sentence(self) -> Optional[Sentence]:
        """Returns the active Sentence object by global sentence index."""
        paragraph = self.current_paragraph
        if not paragraph:
            return None

        for sentence in paragraph.sentences:
            if sentence.sentence_index == self.current_sentence_index:
                return sentence
        return None

    @property
    def current_word(self) -> Optional[Word]:
        """Returns the active Word object"""
        sentence = self.current_sentence
        if not sentence:
            return None
        # Filter or find the word matching current_word_index from sentence.words
        for word in sentence.words:
            if word.word_index == self.current_word_index:
                return word
        return None