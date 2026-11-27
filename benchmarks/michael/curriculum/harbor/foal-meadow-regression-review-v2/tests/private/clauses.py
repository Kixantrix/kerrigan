"""Trusted clause evaluation; pure functions shared by the Docker grader and Harbor verifier."""

_MISSING = object()


def resolve(value, path):
    """Trusted JSON path lookup; '*' maps the rest of the path over a list."""
    for index, key in enumerate(path):
        if key == "*":
            if not isinstance(value, list):
                return _MISSING
            items = [resolve(item, path[index + 1:]) for item in value]
            return _MISSING if any(item is _MISSING for item in items) else items
        if isinstance(value, list) and type(key) is int and 0 <= key < len(value):
            value = value[key]
        elif isinstance(value, dict) and isinstance(key, str) and key in value:
            value = value[key]
        else:
            return _MISSING
    return value


def matches(value, expected):
    """toMatchObject-style subset: objects may add keys; arrays match elementwise."""
    if isinstance(expected, dict):
        return isinstance(value, dict) and all(
            key in value and matches(value[key], item) for key, item in expected.items())
    if isinstance(expected, list):
        return (isinstance(value, list) and len(value) == len(expected)
                and all(matches(v, e) for v, e in zip(value, expected)))
    return type(value) is type(expected) and value == expected


def clause_passes(value, clause):
    kind, *args = clause
    if kind in ("paths_less", "paths_differ"):
        left, right = resolve(value, args[0]), resolve(value, args[1])
        if left is _MISSING or right is _MISSING:
            return False
        if kind == "paths_differ":
            return left != right
        return type(left) in (int, float) and type(right) in (int, float) and left < right
    if kind.startswith("path_"):
        found = resolve(value, args[0])
        if kind == "path_absent":
            return found is _MISSING
        if found is _MISSING:
            return False
        if kind == "path_equal":
            return found == args[1] and matches(found, args[1])
        if kind == "path_match":
            return matches(found, args[1])
        if kind == "path_keys":
            return isinstance(found, dict) and sorted(found) == args[1]
        if kind == "path_contains_all":
            return isinstance(found, (list, str)) and all(item in found for item in args[1])
        if kind == "path_contains_none":
            return isinstance(found, (list, str)) and not any(item in found for item in args[1])
        if kind == "path_within":
            return (type(found) in (int, float) and type(args[1]) in (int, float)
                    and abs(found - args[1]) <= args[2])
        if kind == "path_true":
            return found is True

    if kind == "equal":
        return value == args[0]
    if kind == "not_none":
        return value is not None
    if kind == "key":
        return isinstance(value, dict) and value.get(args[0]) == args[1]
    if kind == "absent":
        return isinstance(value, dict) and args[0] not in value
    if kind == "length":
        return isinstance(value, list) and len(value) == args[0]
    if kind == "item_contains":
        return isinstance(value, list) and len(value) > args[0] and args[1] in value[args[0]]
    if kind == "any_contains":
        return isinstance(value, list) and any(args[0] in item for item in value)
    if kind == "truthy":
        return bool(value)
    raise ValueError(f"unknown trusted clause: {kind}")
