

"""

Module with functions for comparing sequence similarity.


"""

from .sequtil import dnarcomp


def seq_substr_score1(
        cand, sources,
        add_complements=True,
        circ_cand=False, circ_sources=False,
        wordlen_min=3, wordlen_max=None,
        scorefunc=None,
        use_wordcount=False
):
    """Calculate similarity score by

    Args:
        cand:
        sources:
        add_complements:

    Returns:

    Implementation alternatives:

    #1: Only generate cand words, then for each word check if word is in any of the sources.

    #2: Generate all words for both cand and sources then use set arithmetic to produce overlap.
        * Con: Requires more memory
        * Pro: Is probably faster.

    """
    if wordlen_max is None:
        wordlen_max = len(cand)
    if isinstance(sources, str):
        sources = [sources]
    if add_complements:
        sources += [dnarcomp(s) for s in sources]
    if scorefunc is None:
        if use_wordcount:
            scorefunc = lambda word, count: count * len(word)**1.2
        else:
            scorefunc = lambda word: len(word)**1.2

    cand_x2 = cand + cand
    cand_words = [cand_x2[i:i+l]
                  for l in range(wordlen_min, wordlen_max+1)
                  for i in range(0, len(cand) - (0 if circ_cand else l))]
    # TODO: Consider grouping cand_words by word length:
    # cand_words_by_len = {
    #     l: [cand_x2[i:i+l] for i in range(0, len(cand) - (0 if circ_cand else l))]
    #     for l in range(wordlen_min, wordlen_max+1)
    # }

    if use_wordcount:
        if circ_sources:
            circ_sources_by_wordlen = [[s+s[:i] for s in sources] for i in range(wordlen_max)]
            words_counts = ((word, sum(s.count(word) for s in circ_sources_by_wordlen[len(word)]))
                            for word in cand_words)
        else:
            words_counts = ((word, sum(s.count(word) for s in sources)) for word in cand_words)
        scores = (scorefunc(word, count) for word, count in words_counts)
    else:
        if circ_sources:
            # We don't care about erroneous duplicates, so just take the max length
            sources = [s+s[:wordlen_max] for s in sources]
        words = (word for word in cand_words if any(word in s for s in sources))
        scores = (scorefunc(word) for word in words)
    score_sum = sum(scores)
    return score_sum




