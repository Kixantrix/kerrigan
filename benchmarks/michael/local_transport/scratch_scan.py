"""Descriptor-bound metadata scan; never follows candidate-controlled links."""
import json
import os
import stat
import sys


def scan(root, identity, byte_limit, entry_limit):
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        root_fd = os.open(root, flags)
    except FileNotFoundError:
        if os.path.lexists(root):
            raise
        # Task code removed its own TMPDIR; the stock CLI tolerates this, so it is empty, not fatal.
        return {"bytes": 0, "entries": 0, "removed": True}
    try:
        info = os.fstat(root_fd)
        if [info.st_dev, info.st_ino] != identity:
            raise ValueError("scratch_identity_changed")
        totals = {"bytes": 0, "entries": 0}

        def visit(fd):
            with os.scandir(fd) as entries:
                for entry in entries:
                    item = os.stat(entry.name, dir_fd=fd, follow_symlinks=False)
                    totals["entries"] += 1
                    if totals["entries"] > entry_limit:
                        raise ValueError("scratch_entry_budget")
                    if stat.S_ISDIR(item.st_mode):
                        child = os.open(entry.name, flags, dir_fd=fd)
                        try:
                            opened = os.fstat(child)
                            if (opened.st_dev, opened.st_ino) != (item.st_dev, item.st_ino):
                                raise ValueError("scratch_identity_changed")
                            visit(child)
                        finally:
                            os.close(child)
                    elif stat.S_ISREG(item.st_mode) and item.st_nlink == 1:
                        totals["bytes"] += item.st_size
                        if totals["bytes"] > byte_limit:
                            raise ValueError("scratch_byte_budget")
                    else:
                        raise ValueError("scratch_alias_or_special_file")

        visit(root_fd)
        return totals
    finally:
        os.close(root_fd)


if __name__ == "__main__":
    try:
        result = scan(sys.argv[1], json.loads(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    except (OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}))
        sys.exit(1)
    print(json.dumps(result))
