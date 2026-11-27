"""Untrusted-side staging for diff-contract anchors: larger bounded archive (patch <= 1 MiB + tests).

Task images may ship an older Python without tarfile extraction filters, so members
are checked here: regular files with relative, non-traversing names only.
"""
import io
import runpy
import sys
import tarfile

with tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read(4 << 20))) as archive:
    for member in archive.getmembers():
        if not member.isreg() or member.name.startswith("/") or ".." in member.name.split("/"):
            raise SystemExit("unsafe archive member")
    archive.extractall("/work/app")
runpy.run_path("/work/app/harness.py", run_name="__main__")
