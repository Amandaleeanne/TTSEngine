import dataclasses
from typing import Optional
from modeling.state import State


'''
This module provides pure state-transition functions for navigating through
a document hierarchy. Every function takes a State and returns a NEW State instance.

handles logic and math for questions such as:

"If I seek to Sentence 42, what are the new chapter, paragraph, sentence, and word indices?"

"If I move to the next sentence, what is the new State?"

"If I'm at the very last sentence and try to move forward, what happens?" (Boundary handling)
'''

def seek_to_sentence(state: State, target_sentence_index: int) -> State:
    """Returns a new State updated to target_sentence_index and its parent containers."""
    doc = state.document
    if not doc or doc.total_sentences == 0:
        return state

    # Clamp index to valid document bounds [0, total_sentences - 1]
    clamped_index = max(0, min(target_sentence_index, doc.total_sentences - 1))

    # O(1) reverse lookups on Document
    chap_idx = doc.get_chapter_index_for_sentence(clamped_index)
    para_idx = doc.get_paragraph_index_for_sentence(clamped_index)

    # Resolve active sentence to grab its first word index
    target_word_index = state.current_word_index
    if 0 <= chap_idx < len(doc.chapters):
        chapter = doc.chapters[chap_idx]
        if 0 <= para_idx < len(chapter.paragraphs):
            paragraph = chapter.paragraphs[para_idx]
            # Find matching sentence inside paragraph
            for sentence in paragraph.sentences:
                if sentence.sentence_index == clamped_index:
                    target_word_index = sentence.first_word_index
                    break

    return dataclasses.replace(
        state,
        current_sentence_index=clamped_index,
        current_paragraph_index=para_idx,
        current_chapter_index=chap_idx,
        current_word_index=target_word_index,
    )


def next_sentence(state: State) -> State:
    """Advances state by one sentence."""
    return seek_to_sentence(state, state.current_sentence_index + 1)


def previous_sentence(state: State) -> State:
    """Moves state back by one sentence."""
    return seek_to_sentence(state, state.current_sentence_index - 1)


def seek_to_chapter(state: State, target_chapter_index: int) -> State:
    """Jump to the very start of a specific chapter."""
    doc = state.document
    if not doc or not doc.chapters:
        return state

    clamped_chap_idx = max(0, min(target_chapter_index, len(doc.chapters) - 1))
    target_chapter = doc.chapters[clamped_chap_idx]

    # Resolve first global sentence index of target chapter
    first_sentence_idx = 0
    if target_chapter.paragraphs and target_chapter.paragraphs[0].sentences:
        first_sentence_idx = target_chapter.paragraphs[0].sentences[0].sentence_index

    return seek_to_sentence(state, first_sentence_idx)


def next_chapter(state: State) -> State:
    """Advances state to the beginning of the next chapter."""
    return seek_to_chapter(state, state.current_chapter_index + 1)


def previous_chapter(state: State) -> State:
    """Moves state to the beginning of the previous chapter."""
    return seek_to_chapter(state, state.current_chapter_index - 1)

def seek_to_word(state: State, word_index: int) -> State:
    """Seeks to a specific global word index and re-anchors sentence/chapter state."""
    if not state.is_loaded or state.document is None:
        return state

    total_words = state.document.total_words
    if total_words == 0:
        return state

    # Clamp word index within valid range [0, total_words - 1]
    clamped_index = max(0, min(word_index, total_words - 1))

    # Find the sentence containing this global word index safely
    target_sentence_index = None
    for s_idx, sentence in enumerate(state.document.all_sentences):
        if not sentence.words:
            continue
            
        first_w = sentence.words[0].word_index
        last_w = sentence.words[-1].word_index
        
        if first_w <= clamped_index <= last_w:
            target_sentence_index = s_idx
            break

    # Re-anchor sentence, paragraph, and chapter indices
    if target_sentence_index is not None:
        state = seek_to_sentence(state, target_sentence_index)

    # Preserve exact word position (since seek_to_sentence defaults to first word of sentence)
    return dataclasses.replace(state, current_word_index=clamped_index)