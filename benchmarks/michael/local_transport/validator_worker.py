"""Closed validator file operations; invoked only inside the no-fork native task."""
import json
import os
from pathlib import Path
import stat
import sys

POLICY = json.loads(Path(__file__).with_name("validator-policy.json").read_text())


def opened(root, name, flags=os.O_RDONLY, *, policy=None):
    policy = POLICY if policy is None else policy
    if name not in policy["read"]:
        raise ValueError("path denied")
    parts = name.split("/")
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            next_directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                     dir_fd=directory)
            os.close(directory)
            directory = next_directory
        fd = os.open(parts[-1], flags | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            os.close(fd)
            raise ValueError("regular unlinked-alias-free file required")
        return fd
    finally:
        os.close(directory)


def read_source(root, name, *, policy=None):
    policy = POLICY if policy is None else policy
    fd = opened(root, name, policy=policy)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        data = stream.read(policy["bytes"] + 1)
        after = os.fstat(stream.fileno())
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_nlink")
    if (len(data) > policy["bytes"] or before.st_nlink != 1 or after.st_nlink != 1
            or any(getattr(before, k) != getattr(after, k) for k in fields)):
        raise ValueError("artifact overflow or changed during read")
    return data


def main():
    raw = sys.stdin.buffer.read(POLICY["bytes"] + 1)
    if len(raw) > POLICY["bytes"]:
        raise ValueError("action overflow")
    args = json.loads(raw)
    op, name = args["op"], args["path"]
    if set(args) != ({"op", "path", "data"} if op == "write" else {"op", "path"}):
        raise ValueError("action fields denied")
    if op == "read":
        sys.stdout.buffer.write(read_source(".", name))
    elif op == "write" and name == POLICY["source"] and isinstance(args["data"], str):
        data = args["data"].encode()
        if len(data) > POLICY["bytes"]:
            raise ValueError("write overflow")
        with os.fdopen(opened(".", name, os.O_WRONLY), "wb") as stream:
            stream.truncate(0)
            stream.write(data)
        print("written")
    elif op == "run" and name == POLICY["source"]:
        read_source(".", name)
        os.execv(sys.executable, [sys.executable, "-I", "-B",
                                 str(Path(__file__).with_name("native-run.py"))])
    else:
        raise ValueError("operation denied")


if __name__ == "__main__":
    main()
