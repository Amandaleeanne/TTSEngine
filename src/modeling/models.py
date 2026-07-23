from dataclasses import dataclass, field
from functools import cached_property

'''
This module defines the models in a documents structure according to the tree hierarchy.
Document (title, chapters)
  └── Chapter (title, paragraphs, chapter_index)
        └── Paragraph (sentences, paragraph_index)
              └── Sentence (text, words, sentence_index)
                    └── Word (text, start_time, end_time, word_index)

The chapter, paragraph, sentence, and word indices are used to identify the position of each element in the document's structure. 
The word_index and sentence_index are global indices that identify the position of the word and sentence in the entire document, 
while the other indices are local to their respective parent elements.

Models also contain helper properties to get the first and last indices of their child elements, as well as methods to get the chapter and paragraph indices for a given sentence index in O(1) time.
'''

@dataclass(frozen=True)
class Word:
    text: str
    start_time: float
    end_time: float
    word_index: int #index in the global document word list
    sentence_index: int = -1

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

@dataclass(frozen=True)
class Sentence:
    text: str
    words: tuple[Word, ...]
    sentence_index: int #index of the sentence in the paragraph (Global)
    @property
    def first_word_index(self) -> int:
        return self.words[0].word_index if self.words else -1

    @property
    def last_word_index(self) -> int:
        return self.words[-1].word_index if self.words else -1

@dataclass(frozen=True)
class Paragraph:
    sentences: tuple[Sentence, ...]
    paragraph_index: int #index of the paragraph in the chapter

    @property
    def first_sentence_index(self) -> int:
        return self.sentences[0].sentence_index if self.sentences else -1

    @property
    def last_sentence_index(self) -> int:
        return self.sentences[-1].sentence_index if self.sentences else -1

@dataclass(frozen=True)
class Chapter:
    title: str
    paragraphs: tuple[Paragraph, ...]
    chapter_index: int #index of the chapter in the document

    @property
    def first_paragraph_index(self) -> int:
        return self.paragraphs[0].paragraph_index if self.paragraphs else -1

    @property
    def last_paragraph_index(self) -> int:
        return self.paragraphs[-1].paragraph_index if self.paragraphs else -1

#Something smells stinky here...
@dataclass(frozen=True)
class Document:
    title: str
    chapters: tuple[Chapter, ...]
    
    # Internal lookup tables mapping global indices -> parent indices for looking up the tree
    _sentence_to_chapter: dict[int, int] = field(default_factory=dict, init=False, repr=False)
    _sentence_to_paragraph: dict[int, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        sentence_to_chap = {}
        sentence_to_para = {}

        # Traverse the hierarchy once at load time to build the $O(1)$ later index
        for chap_idx, chapter in enumerate(self.chapters):
            for para_idx, paragraph in enumerate(chapter.paragraphs):
                for sentence in paragraph.sentences:
                    sentence_idx = sentence.sentence_index
                    sentence_to_chap[sentence_idx] = chap_idx
                    sentence_to_para[sentence_idx] = para_idx

        # Assign to frozen attributes
        object.__setattr__(self, "_sentence_to_chapter", sentence_to_chap)
        object.__setattr__(self, "_sentence_to_paragraph", sentence_to_para)

        # Populate each Word.sentence_index for quick reverse lookups in tests
        for chapter in self.chapters:
            for paragraph in chapter.paragraphs:
                for sentence in paragraph.sentences:
                    for word in sentence.words:
                        try:
                            object.__setattr__(word, "sentence_index", sentence.sentence_index)
                        except Exception:
                            # Best-effort; if a word is not writable for some reason, skip
                            pass

    def get_chapter_index_for_sentence(self, sentence_index: int) -> int:
        """Returns the chapter index for a given sentence index"""
        return self._sentence_to_chapter.get(sentence_index, -1)

    def get_paragraph_index_for_sentence(self, sentence_index: int) -> int:
        """Returns the paragraph index for a given sentence index"""
        return self._sentence_to_paragraph.get(sentence_index, -1)

    @property
    def total_chapters(self) -> int:
        return len(self.chapters)

    @property
    def total_sentences(self) -> int:
        return len(self._sentence_to_chapter)
    
    #YOU SMELL STINKY!!!! (idk how to fix you...)
    @cached_property
    def all_sentences(self) -> tuple['Sentence', ...]:
        """Flattens all sentences across chapters and paragraphs in reading order."""
        sentences = []
        for chapter in self.chapters:
            for paragraph in chapter.paragraphs:
                sentences.extend(paragraph.sentences)
        return tuple(sentences)

    @cached_property
    def total_words(self) -> int:
        """Helper for total word count across the entire document."""
        return sum(len(sentence.words) for sentence in self.all_sentences)
    