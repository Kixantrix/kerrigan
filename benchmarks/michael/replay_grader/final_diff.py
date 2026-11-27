"""Canonical final-state patch for diff contracts (SWE-bench Pro anchors); pure stdlib.

The final state of a diff-contract task is the set of edits to the writable
(tracked, UTF-8) repository files, encoded as a ``git apply``-compatible
unified diff against the exported base. It is computed by the trusted collector
from file contents (never by running candidate code), bounded by ``max_bytes``,
and applied by the trusted verifier with ``git apply`` inside the task image.
``apply`` is an exact (no fuzz) reference applier used for offline replay and tests.
Writable files are modified in place; new text files (mode 100644) can be created through
``created`` (the native agent declares them in a writable JSON file, see ``new_files``).
No deletion, rename, mode change or binary content.
"""
from __future__ import annotations

import difflib
import json
import re

HEADER = b"# michael-bench final-state git diff against the exported base; no diff below means no change\n"
NO_NEWLINE = "\\ No newline at end of file\n"
PATH = re.compile(r"[A-Za-z0-9_@+.,=-][A-Za-z0-9_@+.,=/-]*")


class DiffError(ValueError):
    pass


def _check_path(path: str) -> None:
    if not PATH.fullmatch(path) or ".." in path.split("/") or path.startswith("/"):
        raise DiffError(f"unsupported path for the diff contract: {path!r}")


def _lines(text: str) -> list[str]:
    """Split on LF only, like git (CR and other separators stay inside lines)."""
    parts = text.split("\n")
    return [part + "\n" for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


MAX_CREATED = 64


def make(base: dict[str, bytes], final: dict[str, bytes], *, max_bytes: int,
         created: dict[str, bytes] | None = None) -> bytes:
    """Patch of ``final`` against ``base`` over exactly the same (writable) paths, plus new files."""
    if set(base) != set(final):
        raise DiffError("final state must cover exactly the writable paths")
    created = created or {}
    if len(created) > MAX_CREATED or set(created) & set(base):
        raise DiffError(f"at most {MAX_CREATED} new files, none of them an existing writable path")
    out = [HEADER]
    for path in sorted({*base, *created}):
        new = path in created
        if not new and base[path] == final[path]:
            continue
        _check_path(path)
        try:
            before, after = ("" if new else base[path].decode("utf-8")), (created if new else final)[path].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DiffError(f"{path}: not UTF-8 text") from exc
        if "\0" in after:
            raise DiffError(f"{path}: NUL bytes are not text")
        body = []
        for line in difflib.unified_diff(_lines(before), _lines(after), "/dev/null" if new else f"a/{path}",
                                         f"b/{path}", n=3):
            body.append(line if line.endswith("\n") else line + "\n" + NO_NEWLINE)
        out.append(f"diff --git a/{path} b/{path}\n".encode())
        if new:
            out.append(b"new file mode 100644\n")
            if not body:  # empty new file
                body = ["--- /dev/null\n", f"+++ b/{path}\n"]
        out.append("".join(body).encode())
        if sum(map(len, out)) > max_bytes:
            raise DiffError(f"final-state patch exceeds {max_bytes} bytes")
    return b"".join(out)


def new_files(raw: bytes, prefix: str) -> dict[str, bytes]:
    """Untrusted agent declaration of new files: a JSON object {agent path: UTF-8 text}."""
    try:
        value = json.loads(raw.decode("utf-8") or "{}")
    except (UnicodeDecodeError, ValueError) as exc:
        raise DiffError("new-files declaration is not a JSON object") from exc
    if not isinstance(value, dict) or len(value) > MAX_CREATED or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
        raise DiffError(f"new-files declaration must map at most {MAX_CREATED} paths to text")
    for path in value:
        _check_path(path)
        if not path.startswith(prefix):
            raise DiffError(f"new file {path!r} must be under {prefix}")
    return {path: text.encode("utf-8") for path, text in value.items()}


def paths(patch: bytes) -> list[str]:
    return re.findall(r"^diff --git a/(\S+) b/\S+$", patch.decode("utf-8"), re.M)


def apply(base: dict[str, bytes], patch: bytes) -> dict[str, bytes]:
    """Exact reference applier for patches produced by ``make``; returns the changed files."""
    text = patch.decode("utf-8")
    if not text.startswith(HEADER.decode()):
        raise DiffError("missing canonical header")
    sections = re.split(r"^diff --git ", text[len(HEADER):], flags=re.M)
    if sections[0]:
        raise DiffError("unexpected text before the first diff")
    changed = {}
    for section in sections[1:]:
        lines = _lines(section)
        match = re.fullmatch(r"a/(\S+) b/(\S+)\n", lines[0])
        new = len(lines) > 1 and lines[1] == "new file mode 100644\n"
        if not match or match.group(1) != match.group(2) or (match.group(1) in base) == new:
            raise DiffError("diff header must modify an existing writable path or create a new one")
        path = match.group(1)
        header = lines[2:4] if new else lines[1:3]
        if header != [("--- /dev/null\n" if new else f"--- a/{path}\n"), f"+++ b/{path}\n"]:
            raise DiffError(f"{path}: malformed file header")
        source, result, cursor, index = ([] if new else _lines(base[path].decode("utf-8"))), [], 0, 4 if new else 3
        while index < len(lines):
            hunk = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*\n", lines[index])
            if not hunk:
                raise DiffError(f"{path}: malformed hunk header")
            start = int(hunk.group(1)) - (0 if hunk.group(2) == "0" else 1)
            if start < cursor:
                raise DiffError(f"{path}: overlapping hunks")
            result += source[cursor:start]
            cursor, index = start, index + 1
            while index < len(lines) and not lines[index].startswith("@@"):
                line = lines[index]
                strip = index + 1 < len(lines) and lines[index + 1] == NO_NEWLINE
                content = line[1:-1] if strip else line[1:]
                if line[0] in " -":
                    if cursor >= len(source) or source[cursor] != content:
                        raise DiffError(f"{path}: context mismatch")
                    cursor += 1
                if line[0] in " +":
                    result.append(content)
                elif line[0] != "-":
                    raise DiffError(f"{path}: malformed hunk line")
                index += 2 if strip else 1
        changed[path] = "".join(result + source[cursor:]).encode("utf-8")
    return changed
