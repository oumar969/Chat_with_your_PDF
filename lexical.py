"""Small CPU-only BM25 index for memory-constrained demo hosting."""

import math
import re
from collections import Counter, defaultdict

from rag import normalize_text

STOPWORDS = set(
    "a an the of is are in to and hvad hvordan hvilken hvilke med er en et det de den og i på til fra for som betyder mente".split()
)


def tokens(text):
    return [word for word in re.findall(r"[^\W_]+", normalize_text(text).casefold()) if word not in STOPWORDS]


class LexicalIndex:
    def __init__(self, chunks):
        self.lengths = []
        self.postings = defaultdict(list)
        for index, chunk in enumerate(chunks):
            counts = Counter(tokens(chunk.text))
            self.lengths.append(sum(counts.values()))
            for word, frequency in counts.items():
                self.postings[word].append((index, frequency))
        self.average = sum(self.lengths) / max(1, len(self.lengths)) or 1

    def search(self, question, limit=12):
        if limit < 1:
            return []
        scores = defaultdict(float)
        count = len(self.lengths)
        for word in set(tokens(question)):
            posting = self.postings.get(word, [])
            weight = math.log(1 + (count - len(posting) + 0.5) / (len(posting) + 0.5))
            for index, frequency in posting:
                norm = 1.2 * (0.25 + 0.75 * self.lengths[index] / self.average)
                scores[index] += weight * frequency * 2.2 / (frequency + norm)
        return [str(index) for index in sorted(scores, key=lambda index: (-scores[index], index))[:limit]]
