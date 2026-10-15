"""Bounded pw-dump snapshot/event decoding shared by player and test harness."""
import json

MAX_REGISTRY_BYTES = 4 * 1024 * 1024


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate registry JSON key')
        result[key] = value
    return result


def parse_registry(data, *, objects=None):
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_REGISTRY_BYTES:
        raise ValueError('registry byte limit')
    text = data.decode('utf-8')
    decoder = json.JSONDecoder(object_pairs_hook=unique_object)
    position = 0
    if objects is None:
        objects = {}
    documents = 0
    while True:
        while position < len(text) and text[position] in ' \t\r\n':
            position += 1
        if position == len(text):
            break
        entries, position = decoder.raw_decode(text, position)
        if not isinstance(entries, list):
            raise ValueError('registry document must be an array')
        documents += 1
        seen = set()
        for entry in entries:
            if (not isinstance(entry, dict) or type(entry.get('id')) is not int or
                    not 0 <= entry['id'] < 4294967295 or entry['id'] in seen):
                raise ValueError('invalid or duplicate registry object id')
            identity = entry['id']
            seen.add(identity)
            if set(entry) in ({'id', 'info'}, {'id', 'props'}) and (
                    entry.get('info', 'absent') is None or entry.get('props', 'absent') is None):
                # pw-dump emits removals before or after its ordinary array even
                # without --monitor. Never discard a removal by choosing one
                # document. Later reuse of an id retains the new object serial.
                objects.pop(identity, None)
            elif (isinstance(entry.get('type'), str) and entry['type'] and
                  (isinstance(entry.get('info'), dict) or isinstance(entry.get('props'), dict))):
                objects[identity] = entry
            else:
                raise ValueError('invalid registry object or removal')
    if not documents:
        raise ValueError('registry document absent')
    return list(objects.values())
