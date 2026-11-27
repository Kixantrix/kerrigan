"""Metadata-only missing-path check beneath a descriptor-bound task root."""
import json
import os
import stat
import sys


def probe(root, identity, path):
    if not isinstance(path, str) or len(path) > 4096:
        return "invalid"
    if path == ".":
        parts = []
    else:
        parts = path.split("/")
    if len(parts) > 128 or any(
        not part or "\0" in part or part in (".", "..") for part in parts
    ):
        return "invalid"
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(root, flags)
    try:
        info = os.fstat(fd)
        if [info.st_dev, info.st_ino] != identity:
            raise ValueError("task_identity_changed")
        for index, part in enumerate(parts):
            try:
                item = os.stat(part, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                return "missing" if index == len(parts) - 1 else "missing-parent"
            if stat.S_ISLNK(item.st_mode) or (
                not stat.S_ISDIR(item.st_mode) and
                (not stat.S_ISREG(item.st_mode) or item.st_nlink != 1)
            ):
                return "alias"
            if index == len(parts) - 1:
                return "directory" if stat.S_ISDIR(item.st_mode) else "file"
            if not stat.S_ISDIR(item.st_mode):
                return "not-directory"
            child = os.open(part, flags, dir_fd=fd)
            opened = os.fstat(child)
            if (opened.st_dev, opened.st_ino) != (item.st_dev, item.st_ino):
                os.close(child)
                raise ValueError("task_identity_changed")
            os.close(fd)
            fd = child
        return "directory"
    finally:
        os.close(fd)


def missing(root, identity, path):
    return probe(root, identity, path) in ("missing", "missing-parent")


if __name__ == "__main__":
    try:
        result = {"kind": probe(sys.argv[1], json.loads(sys.argv[2]), sys.argv[3])}
    except (OSError, ValueError):
        print('{"error":"task_path_probe_failed"}')
        sys.exit(1)
    print(json.dumps(result))
