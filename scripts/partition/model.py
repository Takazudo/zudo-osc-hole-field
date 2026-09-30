"""Shared source ownership; never derive board identity from a free placement."""
from functools import lru_cache
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JACK_BOARDS = ('JL', 'JR')

@lru_cache(maxsize=1)
def source():
    return json.loads((ROOT/'design/partition/partition-input.json').read_text())

def jack_board(instance):
    split = source()['jack_split']
    matches = [board for board, key in [('JL', 'left_instances'), ('JR', 'right_instances')]
               if instance in split[key]]
    if len(matches) != 1:
        raise ValueError('Missing/duplicate J ownership for '+instance)
    return matches[0]
