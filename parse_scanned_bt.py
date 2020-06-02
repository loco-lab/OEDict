#!/usr/bin/env python3
"""Generates oe_bt.json.

Reads data of the form of `oe_bosworthtoller.txt` on input and writes JSON to
output, where keys are a normalized headword, and values are a map of the form
`{headwords: [...], entries: [...]}` where all the headwords in an entry share
the same ASCII normalization. The typical case has two HTML entries, one from
Bosworth and one from Toller, in that order.

This script is ugly. Its main purpose is to stich together the different parts
of entries from different pages of BT into single HTML parts."""

from collections import defaultdict
from enum import Enum
from typing import Any, Dict, Iterable, List, NamedTuple, Set
import json
import re
import sys
import unicodedata

import normalize

# Line numbers that do not start an entry, even though they may begin with a
# bolded phrase.
NOT_AN_ENTRY = set([
    326, 330, 332, 692, 1845, 6016, 17859, 24005, 49675, 97466, 110519, 118045,
    119186, 126386
])

# Line numbers that do start an entry, even though whether they do or not is
# ambiguous (perhaps because they're at the beginning of a page).
ALWAYS_AN_ENTRY = set([
    12470, 17858, 60157, 60555, 60820, 75155, 75330, 77825, 83439, 84266,
    94282, 97998, 102650, 102655, 102810, 102822, 102895, 103897, 113712,
    113834, 119068, 123676
])

# Some entries run afoul of the normalization rules because they look too much
# like subparts of other headwords. This is a map from entry prefix to the
# correct headword.
HEADWORD_SPECIAL_CASES = {
    '<B>a;</B>': 'a',
    '<B>Á,</B>': 'a',
    '<B>á,</B> <I>indecl': 'a',
    '<B>B</B> THE sound of b is produced': 'b',
    '<B>D</B> is sometimes changed': 'd',
    '<B>A.</B> Anglo-Saxon words, containing the short or un': 'e',
    '<B>F</B> At the end of syllable': 'f',
    '<B>I</B> THE Runic character': 'i',
    '<B>Ii,</B> Hii, <I>Iona</I>': 'hii',
    '<B>Ó</B> <I>ever.</I>': 'a',
    '<B>ī.</B> es; <I>m. A letter</I>': 'i',
    '<B>á</B> = on :-- Á felda': 'a',
    '<B>á</B> <I>ever.</I> <B>B.': 'a'
}


class S(Enum):
    """State of the line-reading state machine."""
    INTRO = 1  # in the prefix, before entries are read
    ENTRY = 2  # in the middle of an entry
    BREAK = 3  # after blanks, which separate entries except at page breaks
    PAGE_BREAK = 4  # after page break, which may or may not separate entries


Entry = NamedTuple('Entry', [('headwords', Set[str]), ('defns', List[str])])


def read_entries(in_file: Iterable[str]) -> List[str]:
    """Maps a list of lines to a list of entries.

    Heuristically tries to decide which sequences of lines correspond to BT
    entries by looking for lines that begin with bolded terms.
    """
    state = S.INTRO
    partial = ''  # in-progress entry HTML
    entries = []  # type: List[str]
    n = 0
    for line in in_file:
        n += 1
        line = line.strip()
        # If we're in the intro or a break, and we see an entry start,
        # start accumulating it into `partial`.
        if line.startswith('<B>') and n not in NOT_AN_ENTRY:
            assert (state in (S.BREAK, S.PAGE_BREAK, S.INTRO)
                    or (n in ALWAYS_AN_ENTRY and state == S.ENTRY)), (state, n)
            if state == S.INTRO:
                assert partial == '', (partial, n)
            if partial:
                entries.append(partial)
                partial = ''
            partial = line
            state = S.ENTRY
            continue
        # Otherwise if we're in the intro, keep ignoring text.
        if state == S.INTRO:
            continue
        # If we see a blank line, and we're in an entry, then either the
        # entry is ending or we're in between pages.
        if not line and state == S.ENTRY:
            state = S.BREAK
            continue
        # Ignore page headers. They should only follow blank lines. But if we
        # see this, we're definitely between pages and not in the middle of
        # one.
        if (line.startswith('<HEADER>') or line.startswith('<PAGE NUM')
                or line.startswith('<letterheader')):
            assert state == S.BREAK or state == S.PAGE_BREAK
            state = S.PAGE_BREAK
            continue
        # If we're in a page break and see a blank, stay in the page break.
        if not line and state == S.PAGE_BREAK:
            continue
        # We must be in the middle of an entry, either continuing an entry
        # block, or continuing an entry block from a previous page, or rarely
        # following a spurious mid-entry break. But if we're in one of those
        # mid-entry breaks, it's possible to see a bolded word at the
        # beginning. But this is rare enough that we use a whitelist because
        # there's no way to distinguish bolded words after mid-entry breaks
        # from new entries.
        assert partial
        assert state in (S.ENTRY, S.PAGE_BREAK, S.BREAK)
        assert n in NOT_AN_ENTRY or not line.startswith('<B>')
        state = S.ENTRY
        partial += line + '\n'
    # We're done. If we're in the middle of an entry, add it to `entries`.
    if partial:
        entries.append(partial)
    return entries


def unaccented_letters(s: str) -> str:
    """Return the letters of `s` with accents removed."""
    s = unicodedata.normalize('NFKD', s)
    s = re.sub(r'[^\w -]', '', s)
    return s


def remove_trailing_part_refs(s: str) -> str:
    """Remove non-headword parts of lowercased Toller terms.

    Entirely heuristic. E.g. if `s` is "ge-reafian; i", returns "ge-reafian".
    If the heuristics don't work, override with HEADWORD_SPECIAL_CASES.
    """
    return re.sub('((^| )([ivx]+|[abcdefoα]|[0-9]+))+$', '', s.strip())


def extract_headwords(e: str) -> List[str]:
    """Return the bolded headwords from the beginning of an entry."""
    for pfx, hwd in HEADWORD_SPECIAL_CASES.items():
        if e.startswith(pfx):
            return [hwd]
    m = re.match('^<B>([^<]+)</B>', e)  # bolded string at beginning
    assert m, e
    words = [unaccented_letters(s.lower()) for s in m.group(1).split(',')]
    short_words = [remove_trailing_part_refs(w) for w in words]
    short_words = [w for w in short_words if w]
    # If the headwords are of the form ['foo-', 'bar-baz'] drop the one with
    # the dash, since it's a prefix. It would be better to include 'foo-baz' as
    # well, but that's harder.
    full_words = [
        w for i, w in enumerate(short_words)
        if not w.endswith('-') or i + 1 == len(short_words)
    ]
    # Again, but this time dropping "-baz" from ['foo-bar', '-baz']
    full_words = [
        w for i, w in enumerate(full_words) if not w.startswith('-') or i == 0
    ]
    return full_words


def collect_entries(entries: Iterable[str]) -> Dict[str, Entry]:
    """Collect entries with the same normalized headwords.

    Returns a map from a normalized headword to a list of all headwords with
    that normalization, and a list of the HTML definitions associated with
    them.
    """
    collected = defaultdict(lambda: Entry(set(), []))  # type: Dict[str, Entry]
    for e in entries:
        e = normalize.fix_entities(e)
        headwords = extract_headwords(e)
        assert len(headwords) >= 1, e
        term = normalize.ascify(headwords[0])
        if term == '' or any(h == '' for h in headwords):
            raise Exception(
                'bad normalization, term = %r headwords = %r e = %r' %
                (term, headwords, e))
        collected[term].headwords.update(headwords)
        collected[term].defns.append(e)
    return collected


def entry_as_dict(entry: Entry) -> Dict[str, Any]:
    return {'headwords': list(entry.headwords), 'defns': entry.defns}


def main() -> None:
    with open(sys.stdin.fileno(), 'r', errors='ignore',
              encoding='ascii') as ascii_stdin:
        entries = read_entries(ascii_stdin)
    collected = collect_entries(entries)
    collected_dict = {k: entry_as_dict(v) for k, v in collected.items()}
    json.dump(collected_dict, sys.stdout, indent=2, sort_keys=True)


if __name__ == '__main__':
    main()
