"""Topic-specific authoring bridge for the reviewed T201-T280 allocation."""
import json
from pathlib import Path
from author_common import lesson

ROADMAP = {int(item['id'][1:]): item for item in json.loads((Path(__file__).parent.parent / 'expansion-roadmap.json').read_text(encoding='utf-8'))['topics']}


def emit(number, code, output, explain, pitfalls, exercise, answer):
    assert 201 <= number <= 280
    row = ROADMAP[number]
    lesson(number, row['title'], row['packages'] + [row['group']], '能' + row['behavior'] + '。',
           explain, pitfalls, exercise, answer, code, output)
