from reader.models import (
    Word,
    Sentence,
    Paragraph,
    Chapter,
    Document,
)


words = (
    Word("The", 0),
    Word("quick", 1),
    Word("fox", 2),
)


sentence = Sentence(
    text="The quick fox.",
    words=words,
    index=0,
)


paragraph = Paragraph(
    sentences=(sentence,),
    index=0,
)


chapter = Chapter(
    title="Chapter One",
    paragraphs=(paragraph,),
    index=0,
)


book = Document(
    title="Example Book",
    chapters=(chapter,),
)


print(book)